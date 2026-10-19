"""Controlled mutations of real UCI rows; known labels, no real-world accuracy claim."""

import copy
import importlib.metadata
import json
import random
import statistics
import time
from pathlib import Path
from .contracts import read, profile, digest

ROOT = Path(__file__).resolve().parents[1]


def evaluate():
    source = (ROOT / "data/hour.csv").read_bytes()
    original = read(source)
    reference = profile(original)["means"]
    records = []
    for seed in [7, 17, 29]:
        for family in [
            "clean",
            "count",
            "domain",
            "calendar",
            "duplicate",
            "plausible_count",
            "weather_shift",
        ]:
            rows = copy.deepcopy(original)
            rng = random.Random(seed)
            chosen = rng.sample(range(len(rows)), 30)
            truth = set()
            for i in chosen:
                if family == "count":
                    rows[i]["cnt"] = str(int(rows[i]["cnt"]) + 50)
                    truth.add(i)
                elif family == "domain":
                    rows[i]["hr"] = "25"
                    truth.add(i)
                elif family == "calendar":
                    rows[i]["mnth"] = "13"
                    truth.add(i)
                elif family == "plausible_count":
                    rows[i]["casual"] = str(int(rows[i]["casual"]) + 50)
                    rows[i]["cnt"] = str(int(rows[i]["cnt"]) + 50)
                    truth.add(i)
                elif family == "duplicate":
                    rows.append(rows[i].copy())
                    truth.add(len(rows) - 1)
            if family == "weather_shift":
                for row in rows:
                    row["hum"] = str(max(0, float(row["hum"]) - 0.3))
            start = time.perf_counter()
            result = profile(rows, reference)
            latency = time.perf_counter() - start
            flagged = {x["index"] for x in result["rejected"]}
            records.append(
                {
                    "seed": seed,
                    "family": family,
                    "rows": len(rows),
                    "positive_rows": len(truth),
                    "tp": len(flagged & truth),
                    "fp": len(flagged - truth),
                    "fn": len(truth - flagged),
                    "drift_alarm": bool(result["drift"]),
                    "seconds": latency,
                }
            )
    tp = sum(r["tp"] for r in records)
    fp = sum(r["fp"] for r in records)
    fn = sum(r["fn"] for r in records)
    return {
        "scope": "Controlled faults on one historical dataset; labels derive from injected mutations",
        "source_sha256": digest(source),
        "seeds": [7, 17, 29],
        "drift_threshold_absolute_mean_shift": 0.10,
        "batches": len(records),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "false_alarms_on_clean_batches": sum(
            r["drift_alarm"] or r["fp"] > 0 for r in records if r["family"] == "clean"
        ),
        "clean_batches": 3,
        "median_profile_seconds": statistics.median(r["seconds"] for r in records),
        "p95_profile_seconds": sorted(r["seconds"] for r in records)[
            int(0.95 * (len(records) - 1))
        ],
        "paid_api_calls": 0,
        "billed_api_cost_usd": 0,
        "cloud_cost_usd": None,
        "records": records,
        "failure_story": "Reconciled but artificially inflated counts evade the row contracts. Domain checks cannot establish observational truth.",
        "limitations": [
            "Mutations are designed and labeled by the project author, not independent real incidents",
            "Humidity mean shift is not seasonal-adjusted and can flag legitimate distribution changes",
            "No learned planner or LLM reasoning evaluation; deterministic tool workflow",
            "Timing is local process wall time, not a service SLA",
        ],
    }


if __name__ == "__main__":
    r = evaluate()
    (ROOT / "results/evaluation.json").write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({k: v for k, v in r.items() if k != "records"}, indent=2))
