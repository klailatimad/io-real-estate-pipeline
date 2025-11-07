# Makefile for local orchestration
# Usage examples:
#   make scrape
#   make dbt-run
#   make dbt-test
#   make daily
#   make dashboard

SHELL := /bin/bash

# Load .env if present
ifneq (,$(wildcard ./.env))
include .env
export
endif

# Paths
PROJECT_ROOT := $(shell pwd)
DUCKDB_PATH := $(PROJECT_ROOT)/dbt/target/io.duckdb
IO_RAW_GLOB ?= $(PROJECT_ROOT)/data/raw/io_listings/*/io_listings.csv

# Options
THREADS ?= 4
PY := python
DBT := dbt
STREAMLIT := streamlit

.PHONY: help scrape dbt-run dbt-test dbt-fullrefresh inspect daily dashboard clean-target

help:
	@echo "Targets:"
	@echo "  make scrape          - run the IO scraper (writes daily CSVs)"
	@echo "  make dbt-run         - run dbt models"
	@echo "  make dbt-test        - run dbt tests (safe settings)"
	@echo "  make dbt-fullrefresh - full refresh of dbt models"
	@echo "  make inspect         - quick glance at DuckDB"
	@echo "  make daily           - scrape -> dbt-run -> dbt-test"
	@echo "  make dashboard       - start Streamlit app"
	@echo "  make clean-target    - remove dbt/target artifacts"

scrape:
	$(PY) -m src.ingestion.io_scrape \
	  --out $(PROJECT_ROOT)/data/raw/io_listings \
	  --page-size all \
	  --sleep 1.0

dbt-run:
	@cd dbt && IO_RAW_GLOB="$(IO_RAW_GLOB)" $(DBT) run --threads $(THREADS)

dbt-test:
	@cd dbt && \
	IO_RAW_GLOB="$(IO_RAW_GLOB)" \
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python \
	$(DBT) test --threads 1

dbt-fullrefresh:
	@cd dbt && IO_RAW_GLOB="$(IO_RAW_GLOB)" $(DBT) run --full-refresh --threads $(THREADS)

inspect:
	$(PY) scripts/inspect_duckdb.py --db $(DUCKDB_PATH) --limit 10

daily: scrape dbt-run dbt-test

dashboard:
	$(STREAMLIT) run streamlit_app/app.py

clean-target:
	rm -rf $(PROJECT_ROOT)/dbt/target
