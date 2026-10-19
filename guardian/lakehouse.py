"""Local Spark transformation, dbt gate, and atomic Iceberg table commits."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import duckdb
import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyspark.sql import SparkSession, functions as F
from .contracts import digest

ROOT = Path(__file__).resolve().parents[1]


def spark_transform(rows):
    # Bounded local demonstration; driver collection is explicit, not a scale claim.
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("lakehouse-guardian")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    try:
        data = spark.createDataFrame(pa.Table.from_pylist(rows))
        frame = (
            data.withColumn("observed_date", F.to_date("dteday"))
            .withColumn(
                "hour_key",
                F.concat_ws(
                    "T", F.col("dteday"), F.lpad(F.col("hr").cast("string"), 2, "0")
                ),
            )
            .orderBy("instant")
        )
        result = [r.asDict() for r in frame.collect()]
        # dates become strings for portable downstream schema/model tests.
        for row in result:
            row["observed_date"] = row["observed_date"].isoformat()
        return pa.Table.from_pylist(result)
    finally:
        spark.stop()


def model_gate(arrow, workspace):
    db = Path(workspace) / "analytics.duckdb"
    with duckdb.connect(str(db)) as connection:
        connection.register("candidate", arrow)
        connection.execute(
            "CREATE OR REPLACE TABLE observations AS SELECT * FROM candidate"
        )
    env = {
        **os.environ,
        "GUARDIAN_DB_PATH": str(db.resolve()),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }
    executable = str(Path(__import__("sys").executable).parent / "dbt")
    subprocess.run(
        [
            executable,
            "build",
            "--project-dir",
            str(ROOT / "dbt"),
            "--profiles-dir",
            str(ROOT / "dbt"),
            "--target-path",
            str(Path(workspace) / "dbt-target"),
            "--log-path",
            str(Path(workspace) / "dbt-logs"),
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    with duckdb.connect(str(db), read_only=True) as connection:
        facts = connection.execute("SELECT COUNT(*) FROM fact_hourly").fetchone()[0]
        weather = connection.execute("SELECT COUNT(*) FROM dim_weather").fetchone()[0]
        days, rentals = connection.execute(
            "SELECT COUNT(*),SUM(rentals) FROM daily"
        ).fetchone()
    return {
        "observed_days": days,
        "rentals": rentals,
        "fact_rows": facts,
        "weather_categories": weather,
    }


def publish(source, rows, plan, warehouse):
    if plan["source_sha256"] != digest(source):
        raise ValueError("Source changed")
    warehouse = Path(warehouse).resolve()
    warehouse.mkdir(parents=True, exist_ok=True)
    arrow = spark_transform(rows)
    # Model checks happen before the durable Iceberg mutation.
    with tempfile.TemporaryDirectory(prefix="guardian-model-") as scratch:
        modeled = model_gate(arrow, scratch)
    catalog = load_catalog(
        "guardian",
        type="sql",
        uri=f"sqlite:///{warehouse}/catalog.db",
        warehouse=warehouse.as_uri(),
    )
    catalog.create_namespace_if_not_exists("mobility")
    table = catalog.create_table_if_not_exists("mobility.hourly", schema=arrow.schema)
    current = table.scan().to_arrow()
    same = current.num_rows == arrow.num_rows and current.sort_by("instant").equals(
        arrow.select(current.column_names).sort_by("instant")
    )
    if not same:
        table.overwrite(
            arrow,
            snapshot_properties={
                "source-sha256": digest(source),
                "approval-proposal": plan["proposal_sha256"],
            },
        )
    snapshot = table.current_snapshot()
    return {
        "status": "unchanged" if same else "published",
        "rows": arrow.num_rows,
        "snapshot_id": snapshot.snapshot_id,
        "source_sha256": digest(source),
        **modeled,
    }
