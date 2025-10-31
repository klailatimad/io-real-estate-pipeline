#!/usr/bin/env python
import argparse
import duckdb
import pandas as pd
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Inspect dbt DuckDB warehouse")
    ap.add_argument("--db", default="dbt/target/io.duckdb", help="Path to DuckDB file")
    ap.add_argument("--limit", type=int, default=5, help="Head rows to show")
    args = ap.parse_args()

    # Normalize DB path
    db_path = Path(args.db).resolve()
    con = duckdb.connect(str(db_path))

    print(f"\nConnected to {db_path}")

    print("\n== Tables ==")
    tables_df = con.sql("""
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).df()
    print(tables_df[["table_schema", "table_name"]])

    def head(name: str):
        print(f"\n== {name} (top {args.limit}) ==")
        try:
            df = con.sql(f'SELECT * FROM "{name}" LIMIT {args.limit}').df()
            print(df)
        except Exception as e:
            print(f"(skipped: {e})")

    # --- Row counts (skip views) ---
    print("\n== Row counts ==")
    tables = con.sql("""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema='main'
        ORDER BY table_name
    """).fetchall()

    rows = []
    for tname, ttype in tables:
        if ttype != "BASE TABLE":
            continue  # skip views
        try:
            cnt = con.sql(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
            rows.append((tname, cnt))
        except Exception as e:
            rows.append((tname, f"error: {e}"))

    print(pd.DataFrame(rows, columns=["table_name", "rows"]))

    # --- Quick heads ---
    for t in [
        "stg_io_listings",
        "stg_io_listings_all",
        "dim_location",
        "dim_property",
        "fact_listing_daily",
        "fact_listing_current",
        "mart_price_trends",
        "mart_source_quality",
    ]:
        head(t)

    # --- Example join preview ---
    print("\n== Sample by region/city from fact_listing_current ==")
    try:
        print(con.sql("""
          SELECT l.region, l.city, COUNT(*) AS listings,
                 ROUND(median(f.price), 0) AS median_price
          FROM fact_listing_current f
          JOIN dim_location l USING (location_id)
          WHERE f.price IS NOT NULL
          GROUP BY 1,2
          ORDER BY listings DESC
          LIMIT 10
        """).df())
    except Exception as e:
        print(f"(skipped sample join: {e})")

if __name__ == "__main__":
    main()
