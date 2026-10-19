{{ config(materialized='table') }}
-- Stable UCI category codes, not inferred meteorological measurements.
select * from (values
    (1, 'clear_or_partly_cloudy'),
    (2, 'mist_or_cloudy'),
    (3, 'light_precipitation'),
    (4, 'heavy_precipitation')
) as categories(weather_key, weather_category)
