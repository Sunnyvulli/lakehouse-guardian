{{ config(materialized='table') }}
-- Grain: one dataset-wide observed date/hour, not a station or rider.
select
    instant as source_record_id,
    hour_key as observation_key,
    cast(observed_date as date) as date_key,
    hr as hour_number,
    weathersit as weather_key,
    casual as casual_rentals,
    registered as registered_rentals,
    cnt as rentals
from observations
