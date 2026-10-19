select * from {{ ref('daily') }} where observed_hours < 1 or observed_hours > 24 or rentals < 0
