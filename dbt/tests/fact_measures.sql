select * from {{ ref('fact_hourly') }}
where rentals <> casual_rentals + registered_rentals
   or rentals < 0 or casual_rentals < 0 or registered_rentals < 0
   or hour_number is null or hour_number < 0 or hour_number > 23
   or observation_key <> strftime(date_key, '%Y-%m-%d') || 'T' || lpad(cast(hour_number as varchar), 2, '0')
