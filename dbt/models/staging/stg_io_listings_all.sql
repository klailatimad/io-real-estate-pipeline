{{ config(materialized='view') }}

{% set RAW_GLOB = env_var('IO_RAW_GLOB', None) %}
{% if not RAW_GLOB %}
  {% do exceptions.raise_compiler_error("Set IO_RAW_GLOB to the absolute path of data/raw/io_listings/*/io_listings.csv") %}
{% endif %}

with src as (
  select *
  from read_csv_auto(
    '{{ RAW_GLOB }}',
    header=true,
    all_varchar=true,
    union_by_name=true
  )
)
select
  try_cast(property_id as int)            as property_id,
  nullif(address,'')                  as address,
  nullif(city,'')                     as city,
  nullif(region,'')                   as region,
  try_cast(acres_val as double)       as acres,
  try_cast(sqft_val as double)        as sqft,
  try_cast(price as double)           as price,
  nullif(status,'')                   as status,
  nullif(mls_text,'')                 as mls_text,
  nullif(mls_url,'')                  as mls_url,
  try_cast(posted_date as date)       as posted_date,
  nullif(details_abs,'')              as details_url,
  nullif(image_abs,'')                as image_url,
  try_cast(ingested_at as timestamp)  as ingested_at
from src
where property_id is not null
