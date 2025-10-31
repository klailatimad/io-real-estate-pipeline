{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_io_listings') }}),
loc as (select * from {{ ref('dim_location') }}),
prop as (select * from {{ ref('dim_property') }})
select
  p.property_sk,
  l.location_id,
  s.property_id,
  s.posted_date,
  s.price,
  s.status,
  s.acres,
  s.sqft
from s
join loc l using (city, region)
join prop p using (property_id)
