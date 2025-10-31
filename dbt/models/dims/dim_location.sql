{{ config(materialized='table') }}

select
  md5(concat_ws('||', coalesce(city,''), coalesce(region,''))) as location_id,
  city,
  region
from {{ ref('stg_io_listings') }}
group by city, region
