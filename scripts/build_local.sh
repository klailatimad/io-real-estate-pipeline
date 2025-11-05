#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
./scripts/set_env.sh
cd dbt
dbt run --full-refresh