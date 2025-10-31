{{ config(materialized='table') }}

with base as (
  select
    property_id,
    any_value(address)     as address,
    any_value(details_url) as details_url,
    any_value(image_url)   as image_url
  from {{ ref('stg_io_listings') }}
  group by property_id
)
select
  md5(cast(property_id as varchar)) as property_sk,
  *
from base
