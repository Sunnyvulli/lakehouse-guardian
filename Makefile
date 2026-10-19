PYTHON ?= python3
.PHONY: run test eval airflow-test format-check
run:
	SPARK_LOCAL_IP=127.0.0.1 $(PYTHON) -m guardian.demo --approve-local-demo
test:
	$(PYTHON) -m unittest discover -s tests -v
eval:
	$(PYTHON) -m guardian.evaluate
airflow-test:
	sh scripts/airflow_test.sh
format-check:
	$(PYTHON) -m black --check guardian tests dags
