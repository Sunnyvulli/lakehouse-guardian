select 1 as failure
where (select sum(rentals) from {{ ref('daily') }}) <> (select sum(cnt) from observations)
