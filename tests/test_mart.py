"""Execute dbt against independent small examples, including rejected inputs."""

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import duckdb
import pyarrow as pa
from guardian.lakehouse import model_gate


class MartTests(unittest.TestCase):
    def fixture(self):
        # Hand-calculated: 3 observed hours, 2 dates, 60 rentals, one absent hour.
        return [
            dict(
                instant=1,
                observed_date="2011-01-01",
                hour_key="2011-01-01T00",
                hr=0,
                weekday=6,
                holiday=0,
                workingday=0,
                season=1,
                weathersit=1,
                casual=5,
                registered=5,
                cnt=10,
            ),
            dict(
                instant=2,
                observed_date="2011-01-01",
                hour_key="2011-01-01T02",
                hr=2,
                weekday=6,
                holiday=0,
                workingday=0,
                season=1,
                weathersit=2,
                casual=8,
                registered=12,
                cnt=20,
            ),
            dict(
                instant=3,
                observed_date="2011-01-02",
                hour_key="2011-01-02T00",
                hr=0,
                weekday=0,
                holiday=0,
                workingday=0,
                season=1,
                weathersit=1,
                casual=10,
                registered=20,
                cnt=30,
            ),
        ]

    def test_reconciled_mart_preserves_observed_grain(self):
        with tempfile.TemporaryDirectory() as work:
            r = model_gate(pa.Table.from_pylist(self.fixture()), work)
            self.assertEqual(
                r, dict(observed_days=2, rentals=60, fact_rows=3, weather_categories=4)
            )
            with duckdb.connect(str(Path(work) / "analytics.duckdb")) as con:
                self.assertEqual(
                    con.execute(
                        "select observed_hours from daily order by observed_date"
                    ).fetchall(),
                    [(2,), (1,)],
                )
                self.assertEqual(
                    con.execute(
                        "select w.weather_key, sum(f.rentals) from fact_hourly f join dim_weather w using(weather_key) group by w.weather_key order by w.weather_key"
                    ).fetchall(),
                    [(1, 40), (2, 20)],
                )

    def test_gate_rejects_four_invalid_candidates(self):
        variants = {}
        duplicate = self.fixture()
        duplicate.append({**duplicate[0], "instant": 4, "hour_key": "forged-key"})
        variants["duplicate_business_grain"] = duplicate
        weather = self.fixture()
        weather[0]["weathersit"] = 9
        variants["unknown_weather"] = weather
        counts = self.fixture()
        counts[0]["cnt"] = 999
        variants["inconsistent_measures"] = counts
        calendar = self.fixture()
        calendar[1]["workingday"] = 1
        variants["conflicting_calendar_attributes"] = calendar
        expected = {
            "duplicate_business_grain": "fact_grain",
            "unknown_weather": "relationships_fact_hourly_weather_key",
            "inconsistent_measures": "fact_measures",
            "conflicting_calendar_attributes": "unique_dim_date_date_key",
        }
        for name, rows in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as work:
                with self.assertRaises(subprocess.CalledProcessError):
                    model_gate(pa.Table.from_pylist(copy.deepcopy(rows)), work)

                result = json.loads(
                    (Path(work) / "dbt-target/run_results.json").read_text()
                )
                failed = [
                    r["unique_id"] for r in result["results"] if r["status"] == "fail"
                ]
                self.assertTrue(any(expected[name] in test for test in failed), failed)
