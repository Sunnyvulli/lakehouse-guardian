#!/usr/bin/env sh
set -eu
export GUARDIAN_PROJECT_ROOT="$(pwd)"
export PYTHONPATH="$GUARDIAN_PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export AIRFLOW_HOME="$GUARDIAN_PROJECT_ROOT/.local/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$GUARDIAN_PROJECT_ROOT/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=false
export AIRFLOW__CORE__EXECUTOR=SequentialExecutor
export SPARK_LOCAL_IP=127.0.0.1
airflow db migrate
python dags/guardian_review.py
