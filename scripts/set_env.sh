#!/usr/bin/env bash
set -euo pipefail
# Call from project root
export IO_RAW_GLOB="$(pwd)/data/raw/io_listings/*/io_listings.csv"
export IO_DUCKDB_PATH="dbt/target/io.duckdb"
echo "IO_RAW_GLOB=$IO_RAW_GLOB"
echo "IO_DUCKDB_PATH=$IO_DUCKDB_PATH"