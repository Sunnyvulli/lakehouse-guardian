select
    d.date_key as observed_date,
    count(*) as observed_hours,
    sum(f.rentals) as rentals
from {{ ref('fact_hourly') }} f
join {{ ref('dim_date') }} d on f.date_key = d.date_key
group by d.date_key
