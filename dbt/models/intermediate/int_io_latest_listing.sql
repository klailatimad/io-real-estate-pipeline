{{ config(materialized='table') }}

with ranked as (
  select
    *,
    row_number() over (partition by property_id order by posted_date desc) as rn
  from {{ ref('stg_io_listings') }}
)
select *
from ranked
where rn = 1
