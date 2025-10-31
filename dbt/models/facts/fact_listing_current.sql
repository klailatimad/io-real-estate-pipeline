{{ config(materialized='table') }}

with latest as (select * from {{ ref('int_io_latest_listing') }}),
loc as (select * from {{ ref('dim_location') }}),
prop as (select * from {{ ref('dim_property') }})
select
  p.property_sk,
  l.location_id,
  latest.property_id,
  latest.posted_date as as_of_date,
  latest.price,
  latest.status,
  latest.acres,
  latest.sqft
from latest
join loc l using (city, region)
join prop p using (property_id)
