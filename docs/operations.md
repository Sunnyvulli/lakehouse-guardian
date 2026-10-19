# Operations

Core: activate the tested Python environment and run `make test eval run`. A second `make run` must return `unchanged` for an identical Iceberg snapshot. Generated data and catalog live in `.local/warehouse`; deleting that local directory discards this demonstration's state. Results are historical observations, not live traffic.

Airflow: install `requirements-airflow.txt`, then `make airflow-test`. The script initializes an isolated metadata database under `.local/airflow`, configures this repository's DAG bundle, and performs `dag.test()` with actual Spark/dbt tasks. It leaves a staged candidate and pending approval, never a grant of publication authority. Import success is not execution evidence. Metadata/logs are excluded from Git. The authoring sandbox has a psutil process-visibility incompatibility; use the dedicated passing CI job as execution evidence once available.

Terraform: use version 1.16.6; `terraform -chdir=infra init -backend=false`, `terraform -chdir=infra fmt -check`, `terraform -chdir=infra validate`. No AWS credentials are needed for these syntax/provider checks. Do not interpret them as a plan/apply or AWS execution. No billing budget has been approved and no cloud resources have been created by this project.

If input validation or model tests fail, inspect rejected rows and preserve the previous Iceberg table. Do not disable checks to publish. A schema/validity failure is separate from a plausible-but-wrong observation. Treat the local file path, catalog and process owner as trusted; do not expose this demonstration as a public write service.

Local Terraform initialization verified the provider signature, but subsequent directory-hash validation failed even after redownloading the official package and confirming its published archive hash against the existing lock file. Validation was not bypassed. The dedicated clean CI job is required; do not treat the local infrastructure validation as passed. Raw local outcome is retained in results/terraform-validation.json.

Clean GitHub CI passed all four jobs for the implementation commit. The actual Airflow DAG run and Terraform provider validation passed there; the preserved local failures above remain environment-specific observations, not bypassed checks. See results/ci-verification.json.
