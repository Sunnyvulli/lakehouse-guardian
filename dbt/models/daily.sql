select observed_date, count(*) as observed_hours, sum(cnt) as rentals
from observations
group by observed_date
