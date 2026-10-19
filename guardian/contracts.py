"""Explicit UCI contracts, batch drift signals, and bounded remediation plans."""

import csv
import hashlib
import io
import json
import math
from datetime import date

FIELDS = "instant dteday season yr mnth hr holiday weekday workingday weathersit temp atemp hum windspeed casual registered cnt".split()
FLOATS = {"temp", "atemp", "hum", "windspeed"}
BOUNDS = {
    "season": (1, 4),
    "yr": (0, 1),
    "mnth": (1, 12),
    "hr": (0, 23),
    "holiday": (0, 1),
    "weekday": (0, 6),
    "workingday": (0, 1),
    "weathersit": (1, 4),
    **{k: (0, 1) for k in FLOATS},
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(data):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    if reader.fieldnames != FIELDS:
        raise ValueError("Schema mismatch; no publication permitted")
    return list(reader)


def profile(rows, reference=None):
    good, rejected, keys, identifiers = [], [], set(), set()
    for index, raw in enumerate(rows):
        reasons = []
        try:
            if set(raw) != set(FIELDS):
                raise ValueError("row width")
            row = {
                k: (
                    str(raw[k])
                    if k == "dteday"
                    else float(raw[k]) if k in FLOATS else int(raw[k])
                )
                for k in FIELDS
            }
            day = date.fromisoformat(row["dteday"])
            for k, (lo, hi) in BOUNDS.items():
                if not math.isfinite(row[k]) or not lo <= row[k] <= hi:
                    reasons.append("domain:" + k)
            if any(
                row[k] < (1 if k == "instant" else 0)
                for k in ["instant", "casual", "registered", "cnt"]
            ):
                reasons.append("negative_or_invalid_id")
            if row["cnt"] != row["casual"] + row["registered"]:
                reasons.append("count_reconciliation")
            if (
                row["yr"] != day.year - 2011
                or row["mnth"] != day.month
                or row["weekday"] != (day.weekday() + 1) % 7
            ):
                reasons.append("calendar_reconciliation")
            key = (row["dteday"], row["hr"])
            if key in keys or row["instant"] in identifiers:
                reasons.append("duplicate_key")
        except (ValueError, TypeError, KeyError, OverflowError):
            reasons.append("parse_or_schema")
        if reasons:
            rejected.append({"index": index, "reasons": sorted(set(reasons))})
        else:
            good.append(row)
            keys.add(key)
            identifiers.add(row["instant"])
    means = {k: sum(r[k] for r in good) / len(good) for k in FLOATS} if good else {}
    shifts = {
        k: abs(means[k] - reference[k]) for k in means if reference and k in reference
    }
    return {
        "accepted": good,
        "rejected": rejected,
        "means": means,
        "drift": {k: v for k, v in shifts.items() if v > 0.10},
    }


def proposal(source_sha, report):
    if not report["accepted"]:
        action = "block"
    elif report["drift"]:
        action = "investigate_drift"
    else:
        action = "publish_valid_rows"
    body = {
        "action": action,
        "source_sha256": source_sha,
        "accepted_rows": len(report["accepted"]),
        "rejected_rows": len(report["rejected"]),
        "drift": report["drift"],
    }
    body["proposal_sha256"] = digest(json.dumps(body, sort_keys=True).encode())
    return body
