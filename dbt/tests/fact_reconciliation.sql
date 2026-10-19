select 1 as failure
where (select count(*) from {{ ref('fact_hourly') }}) <> (select count(*) from observations)
   or (select coalesce(sum(rentals), 0) from {{ ref('fact_hourly') }}) <> (select coalesce(sum(cnt), 0) from observations)
