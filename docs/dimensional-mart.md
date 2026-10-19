# Dimensional mart: definitions and reproducible evidence

## Business question
How do monthly rentals per observed hour change, and how do observed hours reconcile to the raw data? This is descriptive historical reporting, not a causal explanation of weather or demand.

## Grain and definitions

- `fact_hourly`: exactly one dataset-wide date/hour observation. `source_record_id` preserves UCI `instant`; `observation_key` preserves date/hour. Neither represents a station or customer.
- `dim_date`: one row per observed date, with calendar year/month, source Sunday-zero weekday, holiday, working-day and season codes. Conflicting attributes cause duplicate date keys and fail the gate.
- `dim_weather`: four fixed category codes from UCI. It includes categories with no observed facts; a fact cannot invent a fifth code.
- `daily`: fact rows joined to the calendar dimension, count of observed hours and sum of rentals. Missing hours are not fabricated or treated as zero demand.
- `rentals`: `casual_rentals + registered_rentals`, not unique riders. Counts are additive; rates are recomputed from summed counts and observed hours, not averaged across daily averages.

The schema is rebuilt in temporary DuckDB before Iceberg publication. These are full-refresh models, not CDC, incremental merge, slowly changing dimensions, a persistent warehouse product or a distributed transaction. The durable Iceberg table remains the approved hourly snapshot.

## Execute

After the README prerequisite installation, run `make mart`. This executes Spark transformation, actual dbt build/tests and a monthly SQL query using a CTE, dimensional join and `LAG`. It writes `results/mart.json` with source/model hashes, versions, check statuses and all 24 monthly rows. It does not publish to Iceberg or approve any cloud operation. `make run` still requires the explicit local-demo approval flag and checks these same models before publication.

The recorded full-source run reconciles 17,379 facts, 731 observed dates and 3,292,679 rentals; all 25 dbt checks pass. January 2011 has 38,189 rentals / 688 observed hours = 55.5073 rentals per observed hour. February has 48,215 / 649 = 74.2912. This does not establish a weather effect, a forecast, population coverage or a general performance benchmark. See the raw precision rather than rounding for calculations.

`tests/test_mart.py` independently specifies a three-row example: 60 rentals across three observed hours/two dates, including a missing hour. It checks rollups and weather joins. Four mutated candidates must fail the relevant dbt test: duplicate business grain, unknown weather category, inconsistent counts and conflicting calendar attributes. Tests inspect failed test IDs, not merely subprocess exit codes. Together with the existing 11 workflow tests, 13 Python test methods run. The 25 dbt checks are a separate count.

## Decisions and limits

Natural date/weather keys are sufficient for fixed reference categories; fabricated station/customer dimensions or SCD2 history would claim facts this dataset does not contain. No claim of high-volume Spark efficiency is made: the implementation still collects this bounded historical input on the driver. No primary-source independence is added by another model over the same CSV.

References: [UCI dataset and license](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset), [dbt data tests](https://docs.getdbt.com/reference/resource-properties/data-tests), consulted 2026-10-19. Dataset bytes/license remain in data/SOURCE.md; no tutorial code is copied.
