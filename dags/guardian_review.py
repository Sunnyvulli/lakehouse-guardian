"""Airflow DAG stages and checks data; it never grants publication approval."""

from datetime import datetime, timezone
from pathlib import Path
import os
from airflow.sdk import dag, task

ROOT = Path(os.environ["GUARDIAN_PROJECT_ROOT"]).resolve()


@dag(
    dag_id="guardian_review",
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["data-quality", "human-approval"],
)
def guardian_review():
    @task(retries=1)
    def inspect_source():
        from guardian.contracts import read, profile, proposal, digest

        source = (ROOT / "data/hour.csv").read_bytes()
        report = profile(read(source))
        plan = proposal(digest(source), report)
        if plan["action"] != "publish_valid_rows":
            raise ValueError("Review required before staging")
        return plan

    @task(retries=1)
    def stage(plan):
        from guardian.contracts import read, profile, digest
        from guardian.lakehouse import spark_transform
        import pyarrow.parquet as pq

        source = (ROOT / "data/hour.csv").read_bytes()
        if digest(source) != plan["source_sha256"]:
            raise ValueError("Source changed since inspection")
        path = ROOT / ".local" / "staging" / plan["source_sha256"]
        path.mkdir(parents=True, exist_ok=True)
        pq.write_table(
            spark_transform(profile(read(source))["accepted"]),
            path / "candidate.parquet",
        )
        return {"path": str(path), "proposal": plan}

    @task(retries=0)
    def validate_models(candidate):
        import pyarrow.parquet as pq
        from guardian.lakehouse import model_gate
        import json

        path = Path(candidate["path"])
        result = model_gate(pq.read_table(path / "candidate.parquet"), path)
        summary = {
            "status": "awaiting_operator_approval",
            "proposal": candidate["proposal"],
            "dbt": result,
            "published": False,
        }
        (ROOT / "results/airflow.json").write_text(json.dumps(summary, indent=2) + "\n")
        return summary

    validate_models(stage(inspect_source()))


dag = guardian_review()
if __name__ == "__main__":
    run = dag.test()
    if str(run.state) != "success":
        raise SystemExit("Airflow DAG test failed")
