"""Execute the local dimensional mart and retain reconciled analytical results."""

import importlib.metadata
import json
from pathlib import Path
import platform
import tempfile
import time
import duckdb
from .contracts import digest, profile, read
from .lakehouse import model_gate, spark_transform

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = (ROOT / "data/hour.csv").read_bytes()
    report = profile(read(source))
    if report["rejected"]:
        raise ValueError("Mart report requires a fully valid source")
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="guardian-mart-") as work:
        summary = model_gate(spark_transform(report["accepted"]), work)
        with duckdb.connect(
            str(Path(work) / "analytics.duckdb"), read_only=True
        ) as con:
            cursor = con.execute("""
                with totals as (
                    select date_trunc('month', d.date_key)::date as month,
                           count(*) as observed_hours, sum(f.rentals) as rentals
                    from fact_hourly f join dim_date d using(date_key)
                    group by 1
                ), rates as (
                    select *, rentals::double / observed_hours as rentals_per_observed_hour
                    from totals
                )
                select *, lag(rentals_per_observed_hour) over(order by month) as prior_month_rate
                from rates order by month
            """)
            monthly = [
                dict(zip([c[0] for c in cursor.description], row))
                for row in cursor.fetchall()
            ]
        results = json.loads((Path(work) / "dbt-target/run_results.json").read_text())
        checks = [r for r in results["results"] if r["unique_id"].startswith("test.")]
    output = {
        "scope": "Full-refresh temporary local DuckDB mart; no AWS, CDC, SCD2 or causal inference",
        "source_sha256": digest(source),
        "python": platform.python_version(),
        "versions": {
            p: importlib.metadata.version(p)
            for p in ["duckdb", "dbt-core", "dbt-duckdb", "pyspark"]
        },
        "model_sha256": {
            str(p.relative_to(ROOT)): digest(p.read_bytes())
            for p in sorted((ROOT / "dbt").rglob("*.sql"))
        },
        "summary": summary,
        "dbt_checks": {r["unique_id"]: r["status"] for r in checks},
        "elapsed_seconds": time.perf_counter() - started,
        "monthly": monthly,
    }
    # JSON null, rather than nonstandard NaN, for the first unavailable lag.
    for r in output["monthly"]:
        r["month"] = str(r["month"])[:10]
        if r["prior_month_rate"] != r["prior_month_rate"]:
            r["prior_month_rate"] = None
    target = ROOT / "results/mart.json"
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {"summary": summary, "dbt_checks": len(checks), "output": str(target)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
