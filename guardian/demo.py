"""Run an actual approval interruption and optional explicit local approval."""

import argparse
import importlib.metadata
import json
import platform
import time
from pathlib import Path
from langgraph.types import Command
from .workflow import build
from .lakehouse import publish

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--approve-local-demo",
        action="store_true",
        help="Explicitly approve publishing attributed fixture data to the local warehouse",
    )
    parser.add_argument("--warehouse", default=".local/warehouse")
    args = parser.parse_args()
    source = (ROOT / "data/hour.csv").read_bytes()
    start = time.perf_counter()
    graph = build(lambda data, rows, plan: publish(data, rows, plan, args.warehouse))
    config = {"configurable": {"thread_id": "local-demo"}}
    paused = graph.invoke({"source": source}, config)
    assert "__interrupt__" in paused
    plan = paused["proposal"]
    print(json.dumps({"approval_required": plan}, indent=2))
    if not args.approve_local_demo:
        print(
            "No data published. To execute this local fixture, rerun with --approve-local-demo."
        )
        return
    final = graph.invoke(
        Command(resume={"approve": True, "proposal_sha256": plan["proposal_sha256"]}),
        config,
    )
    report = {
        "scope": "Local Spark/Iceberg/dbt/LangGraph demo; no AWS or model call",
        "python": platform.python_version(),
        "versions": {
            p: importlib.metadata.version(p)
            for p in [
                "langgraph",
                "pyspark",
                "pyiceberg",
                "duckdb",
                "dbt-core",
                "dbt-duckdb",
            ]
        },
        "elapsed_seconds": time.perf_counter() - start,
        "billed_api_cost_usd": 0,
        "cloud_cost_usd": None,
        "proposal": plan,
        "result": final["published"],
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/demo.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
