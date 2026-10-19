# Changelog

## 0.1.0 - 2026-10-19
- Implement local Spark transformation, dbt model gate and Iceberg snapshot publication/replay.
- Implement typed LangGraph interruption and explicit scoped local approval.
- Add 11 behavioral tests and 21 controlled fault batches, with an observed plausible-count failure.
- Add Airflow staging/review DAG and S3/Glue-catalog Terraform groundwork.
- Cloud deployment and model-based agent reasoning are not verified. Local integration, actual Airflow, Terraform validation and full-history checks passed before release preparation.

## Unreleased
- Add explicit hourly fact grain, calendar/weather dimensions and join-based daily reporting with 25 executed dbt data checks.
- Add two real dbt integration test methods (13 Python methods total), including four negative candidates and independent hand-calculated rollups.
- Add `make mart`, hashed/ versioned raw monthly reporting results and SQL window analysis. Full-refresh/local scope; no AWS, incremental/CDC or SCD2 claim.
- Prepare an independent technical-review invitation; external review remains pending until a reviewer responds. v0.1.0 continues to identify the earlier released snapshot.
