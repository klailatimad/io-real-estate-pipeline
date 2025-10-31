#!/usr/bin/env bash
set -euo pipefail
export IO_DUCKDB_PATH=${IO_DUCKDB_PATH:-dbt/target/io.duckdb}
streamlit run streamlit_app/app.py
