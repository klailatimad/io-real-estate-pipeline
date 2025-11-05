#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
python -m src.ingestion.io_scrape --out data/raw/io_listings --page-size all --sleep 1.0
./scripts/build_local.sh
streamlit run streamlit_app/app.py