{{ config(materialized='table') }}

with s as (
  select
    property_id, posted_date, price, status,
    address, city, region, acres, sqft, details_url, image_url, mls_url
  from {{ ref('stg_io_listings') }}
),
e as (
  select
    s.*,
    lag(price)  over (partition by property_id order by posted_date) as prev_price,
    lag(status) over (partition by property_id order by posted_date) as prev_status
  from s
)
select
  *,
  case when price  is not null and prev_price  is not null and price  != prev_price  then 1 else 0 end as price_change_flag,
  case when status is not null and prev_status is not null and status != prev_status then 1 else 0 end as status_change_flag
from e
