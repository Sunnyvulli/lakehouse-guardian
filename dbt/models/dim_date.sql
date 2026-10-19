{{ config(materialized='table') }}
-- One row per observed calendar date; no synthetic zero-demand dates.
select distinct
    cast(observed_date as date) as date_key,
    extract(year from cast(observed_date as date))::integer as calendar_year,
    extract(month from cast(observed_date as date))::integer as calendar_month,
    weekday as sunday_zero_weekday,
    holiday,
    workingday,
    season as source_season_code
from observations
