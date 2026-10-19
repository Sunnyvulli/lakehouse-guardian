select date_key, hour_number
from {{ ref('fact_hourly') }}
group by date_key, hour_number
having count(*) <> 1
