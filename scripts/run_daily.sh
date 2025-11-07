#!/usr/bin/env bash
set -euo pipefail

# Move to repo root (edit this path to your actual repo location)
cd /home/klailatimad/real_estate_data_project

# Activate venv if you use one
source .venv/bin/activate

# Run the pipeline
make daily