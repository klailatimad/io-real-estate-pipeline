#!/usr/bin/env python
import argparse
import duckdb
import pandas as pd

def main():
    ap = argparse.ArgumentParser(description="Inspect dbt DuckDB warehouse")
    ap.add_argument("--db", default="/dbt/target/io.duckdb", help="Path to DuckDB file")
    ap.add_argument("--limit", type=int, default=5, help="Head rows to show")
    args = ap.parse_args()

    con = duckdb.connect(args.db)

    print("\n== Tables ==")
    tables = con.sql("""
        select table_schema, table_name
        from information_schema.tables
        where table_schema = 'main'
        order by table_name
    """).df()
    print(tables)

    def head(name):
        print(f"\n== {name} (top {args.limit}) ==")
        try:
            df = con.sql(f"select * from {name} limit {args.limit}").df()
            print(df)
        except Exception as e:
            print(f"(skipped: {e})")

    # Row counts (Python loop avoids dynamic SQL identifiers)
    print("\n== Row counts ==")
    tables = con.sql("""
        select table_name
        from information_schema.tables
        where table_schema='main'
        order by table_name
    """).fetchall()

    rows = []
    for (tname,) in tables:
        cnt = con.sql(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
        rows.append((tname, cnt))
    import pandas as pd
    print(pd.DataFrame(rows, columns=["table_name", "rows"]))

    # Quick heads
    for t in [
        "stg_io_listings",
        "dim_location",
        "dim_property",
        "fact_listing_daily",
        "fact_listing_current",
        "mart_price_trends",
        "mart_source_quality",
    ]:
        head(t)

    # Example join preview
    print("\n== Sample by region/city from fact_listing_current ==")
    print(con.sql("""
      select l.region, l.city, count(*) as listings,
             round(median(f.price),0) as median_price
      from fact_listing_current f
      join dim_location l using (location_id)
      where f.price is not null
      group by 1,2
      order by listings desc
      limit 10
    """).df())

if __name__ == "__main__":
    main()
