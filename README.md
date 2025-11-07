
# 🏗️ Ontario Infrastructure Ontario (IO) Properties – Data Pipeline PoC

A **local-first data engineering project** to ingest, clean, and prepare Ontario’s public **Infrastructure Ontario “Properties for Sale”** dataset for analysis and visualization.  
The goal is to design and practice a full **end-to-end data pipeline** — from ingestion and transformation to dashboarding — using modern open-source data tools.

----------

## 🚀 Project Overview

This project demonstrates how to:

-   **Ingest** real estate listings from a public ASP.NET WebForms site using Python and BeautifulSoup
-   Handle **pagination and form postbacks** (`__VIEWSTATE`, `__EVENTVALIDATION`)
-   **Normalize and clean** fields (price, acres, square footage, posted date, etc.)   
-   **Snapshot** raw data daily as CSVs for incremental history
-   **Transform** data with dbt + DuckDB into facts, dims, and marts
-   **Visualize** trends and insights in a **Streamlit dashboard**

All processing runs **locally** for compliance, reproducibility, and easy iteration.  
Future phases include validation (Great Expectations), orchestration (Airflow), and cloud migration.

----------

## 🧱 Repository Structure

```
real_estate_data_project/
│
├── data/
│   └── raw/io_listings/ # Daily scraped CSVs (YYYY-MM-DD/io_listings.csv) 
│
├── dbt/
│   ├── dbt_project.yml
│   ├── target/io.duckdb # DuckDB warehouse 
│   └── models/
│       ├── staging/ # stg_io_listings, stg_io_listings_all 
│       ├── intermediate/ # int_io_events, int_io_latest_listing 
│       ├── dims/ # dim_property, dim_location 
│       ├── facts/ # fact_listing_daily, fact_listing_current 
│       └── marts/ # mart_price_trends, mart_source_quality 
│
├── scripts/
│   ├── set_env.sh # Exports IO_RAW_GLOB & IO_DUCKDB_PATH 
│   ├── build_local.sh # Runs dbt build with env correctly set
│   ├── dev_all.sh # Scrape -> dbt build -> Streamlit (local dev)
│   └── inspect_duckdb.py # Quick inspection & row counts 
│
├── streamlit_app/
│   └── app.py # Streamlit dashboard (interactive filters, charts) 
│
├── src/
│   ├── ingestion/
│   │   ├── io_scrape.py # Scraper module
│   │   └── html_parser.py # HTML parsing helpers
│
├── requirements.txt
├── .env.example # Example env vars for local setup
└── README.md
``` 

----------

## ⚙️ Current Capabilities

|Feature|Description|
|---|---|
|**Web Scraper**|Extracts property listings from IO’s “Properties for Sale” portal|
|**Pagination Handler**|Handles ASP.NET `__doPostBack` pagination automatically|
|**Data Normalization**|Cleans and types numeric/date fields|
|**Daily Snapshots**|Saves CSVs under `data/raw/io_listings/YYYY-MM-DD/`|
|**dbt Transformations**|Builds layered models: staging → facts/dims → marts|
|**Incremental Model**|`fact_listing_daily` appends new daily records|
|**Validation Tests**|dbt tests ensure `not_null` and `unique` keys|
|**Streamlit Dashboard**|Interactive filters by Region, City, and Status|
|**Altair Charts**|Price distribution & weekly median price trends|
|**DuckDB Warehouse**|Local analytical database used by dbt + Streamlit|

----------

## 📊 Pipeline Workflow

### 1. Scrape Daily Listings

```sh
python -m src.ingestion.io_scrape \
  --out data/raw/io_listings \
  --page-size all \
  --sleep 1.0
```

→ Creates a new folder like:

`data/raw/io_listings/YYYY-MM-DD/io_listings.csv` 

----------

### 2. Run dbt Transformations

```sh
# From project root, set env so stg_io_listings_all can find all CSVs
export IO_RAW_GLOB="$(pwd)/data/raw/io_listings/*/io_listings.csv"

cd dbt
dbt run
dbt test
``` 
After a new daily scrape, you can force a full refresh of models that depend on all CSVs:

`dbt run --full-refresh --select stg_io_listings_all+ fact_listing_daily+`


Or just use the helper:

`./scripts/build_local.sh`

DBT Models:

-   `stg_io_listings_all` unions all daily CSVs
    
-   `fact_listing_daily` is **incremental**, appending new data daily
    
-   `fact_listing_current` and marts refresh fully
    

----------

### 3. Inspect DuckDB Data


```sh
# Optional: if you pointed IO_DUCKDB_PATH elsewhere
export IO_DUCKDB_PATH="dbt/target/io.duckdb"

python scripts/inspect_duckdb.py --db dbt/target/io.duckdb --limit 5
```

Displays:

-   Tables and row counts
    
-   Top rows for staging, facts, and marts
    
-   Region-level sample summaries
    

----------

### 4. Launch Streamlit Dashboard

```sh
# Ensure env is set so the app points to the correct DB
export IO_DUCKDB_PATH="dbt/target/io.duckdb"

streamlit run streamlit_app/app.py
``` 

**Features:**

-   Toggle between **Current** and **Historical** listings
    
-   Filter by Region, City, and Status
    
-   Choose date range (for Historical mode)
    
-   Metrics (listing count, median price/sqft/acres)
    
-   Charts (price distribution, weekly trends)
    
-   Full table of filtered results
    

----------

## 🧭 Orchestration (local)

This repo includes a Makefile to run the pipeline end to end.

### Common commands:
```sh
make scrape          # scrape daily IO listings into data/raw/io_listings/YYYY-MM-DD/io_listings.csv
make dbt-run         # run dbt models (uses IO_RAW_GLOB)
make dbt-test        # run dbt tests with safe settings
make daily           # scrape -> dbt-run -> dbt-test (one-shot)
make dashboard       # launch Streamlit UI
make inspect         # quick row counts and samples from DuckDB
```

### Environment:

- Ensure IO_RAW_GLOB is available to dbt. The Makefile sets it automatically to:
```sh
<data_root>/data/raw/io_listings/*/io_listings.csv
```

- You can also add it to .env:
```sh
IO_RAW_GLOB=/absolute/path/to/data/raw/io_listings/*/io_listings.csv
```

### Cron example (WSL/Linux):

1. Edit the repository path inside scripts/run_daily.sh.
2. Add to crontab:

```sh
crontab -e
```
```sh
# Run every day at 07:30 local time
30 7 * * * /home/klailatimad/real_estate_data_project/scripts/run_daily.sh >> /home/klailatimad/real_estate_data_project/logs/daily.log 2>&1
```

3. Create logs/ if missing:
```sh
mkdir -p logs
```

*Tip: on Windows Task Scheduler, call bash -lc "cd /home/klailatimad/real_estate_data_project && ./scripts/run_daily.sh".*

----------

## 🧩 dbt Model Highlights

|Model|Type|Purpose|
|---|---|---|
|`stg_io_listings`|Table|Cleaned data from daily CSVs|
|`stg_io_listings_all`|View|Union of all CSV snapshots|
|`dim_location`|Table|City → Region mapping|
|`dim_property`|Table|Property metadata|
|`fact_listing_daily`|Incremental|Historical records|
|`fact_listing_current`|Table|Latest state snapshot|
|`mart_price_trends`|Table|Weekly median prices by city|
|`mart_source_quality`|Table|Data completeness metrics|

----------

## 🧪 Data Quality Tests

Run:

`dbt test` 

Tests include:

-   `unique` and `not_null` on `property_id`
    
-   `not_null` on `posted_date`
    
-   `unique` keys on facts and staging models
    

----------

## 📈 Visualization Highlights

-   **KPI cards** for listings, median price, acres, sqft
    
-   **Histogram** for price distribution
    
-   **Line chart** for weekly price trends
    
-   **Dynamic table** updated by sidebar filters
    
-   Works for both _Current_ and _Historical_ data views
    

----------

## 🩺 Troubleshooting

- dbt: “No files found that match the pattern … io_listings.csv”
  - Set IO_RAW_GLOB to an absolute path, then rebuild:
    ```sh
    export IO_RAW_GLOB="$(pwd)/data/raw/io_listings/*/io_listings.csv"
    cd dbt && dbt run --full-refresh --select stg_io_listings_all+
    ```

- Streamlit shows empty data
  - Make sure you’ve scraped and then run dbt. Also confirm `IO_DUCKDB_PATH` points to the right file.

- Date picker errors in Historical mode
  - Ensure you have at least one CSV day under `data/raw/io_listings/` and re-run dbt to populate `fact_listing_daily`.
----------

## 🪜 Next Steps

|Stage|Description|Status|
|---|---|---|
|**Data Validation**|Add Great Expectations or dbt data_tests|⏳ Planned
|**Automation**|Local orchestration via Makefile and cron implemented; full Airflow DAG planned next|✅ Partial|
|**Cloud Deployment**|Port to Snowflake or Azure Synapse|⏳ Future|
|**Testing & CI/CD**|Add pytest and GitHub Actions|⏳ Future
|**Dockerization**|Local containerized demo|⏳ Future|

----------

## 🧰 Tools Used

-   **Python 3.11+** (`requests`, `beautifulsoup4`, `pandas`, `duckdb`, `altair`, `streamlit`)
    
-   **dbt-core 1.8+** (transformations, testing)
    
-   **DuckDB** (local analytical database)
    
-   **Streamlit** (interactive visualization)
    
-   **Altair** (charts)
    

----------
## 🔧 Environment Variables

These are used by dbt (DuckDB) and the Streamlit app.

```sh
# REQUIRED: absolute path to your raw daily CSVs for stg_io_listings_all
export IO_RAW_GLOB="<ABSOLUTE_PATH>/data/raw/io_listings/*/io_listings.csv"

# OPTIONAL: override DuckDB file used by Streamlit & scripts
export IO_DUCKDB_PATH="dbt/target/io.duckdb"
```

- Linux/WSL/macOS:
    ```
    export IO_RAW_GLOB="$(pwd)/data/raw/io_listings/*/io_listings.csv"
    ```

- PowerShell:
    ```
    $env:IO_RAW_GLOB = "$(Get-Location)/data/raw/io_listings/*/io_listings.csv"
    ```

You can also run:
```sh
./scripts/set_env.sh
```

----------


## 🧱 Version History

|Branch|Description|Key Changes|
|---|---|---|
|`main`|Base ingestion and repo scaffold|Scraper + normalization logic|
|`feature/dbt-setup`|Added dbt project|dbt_project.yml, staging & dim models, tests|
|`feature/dbt-incremental`|Introduced incremental loads| `fact_listing_daily`,schema drift handling|
|`feature/dashboard`|Added Streamlit visualization|`app.py`, filters, charts, KPIs|
|`feature/dbt-path-fix`|Stablize dbt CSV glob and local dev flow|`IO_RAW_GLOB` env var for `stg_io_listings_all`, helper scripts (`set_env.sh`, `build_local.sh`, `dev_all.sh`), README updates|
|`feature/orchestration-local`|Local one-click runs|Makefile targets, cron example, documented `IO_RAW_GLOB` behavior|
|`main` (merged)|Current stable release|Fully working local pipeline from scrape → dbt → Streamlit|