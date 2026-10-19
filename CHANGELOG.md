# Changelog

## 0.1.0 - 2026-10-19
- Implement local Spark transformation, dbt model gate and Iceberg snapshot publication/replay.
- Implement typed LangGraph interruption and explicit scoped local approval.
- Add 11 behavioral tests and 21 controlled fault batches, with an observed plausible-count failure.
- Add Airflow staging/review DAG and S3/Glue-catalog Terraform groundwork.
- Cloud deployment and model-based agent reasoning are not verified. Local integration, actual Airflow, Terraform validation and full-history checks passed before release preparation.
