{{ config(
    materialized='incremental',
    unique_key=['property_id','posted_date'],
    on_schema_change='sync_all_columns'
) }}

with s as (
  select * from {{ ref('stg_io_listings_all') }}
),
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
{% if is_incremental() %}
  where s.posted_date > (select coalesce(max(posted_date), date '1900-01-01') from {{ this }})
{% endif %}
