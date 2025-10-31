{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_io_listings') }}),
agg as (
  select
    region,
    city,
    count(*) as rows,
    sum(case when price is null then 1 else 0 end) as price_nulls,
    sum(case when sqft  is null then 1 else 0 end) as sqft_nulls,
    max(posted_date) as latest_date
  from s
  group by 1,2
)
select
  *,
  1.0 - (price_nulls::double / nullif(rows,0)) as price_completeness,
  1.0 - (sqft_nulls::double  / nullif(rows,0)) as sqft_completeness
from agg
