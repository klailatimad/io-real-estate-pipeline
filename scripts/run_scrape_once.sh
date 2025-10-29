#!/usr/bin/env bash
set -euo pipefail

python -m src.ingestion.io_scrape \
  --out data/raw/io_listings \
  --page-size all \
  --download-images \
  --sleep 1.0