{{ config(materialized='table') }}

with d as (
  select
    l.city,
    l.region,
    f.posted_date,
    f.price
  from {{ ref('fact_listing_daily') }} f
  join {{ ref('dim_location') }} l using (location_id)
  where f.price is not null
),
w as (
  select
    city,
    region,
    date_trunc('week', posted_date) as week_start,
    median(price) as median_price,
    count(*) as listings
  from d
  group by 1,2,3
)
select * from w
