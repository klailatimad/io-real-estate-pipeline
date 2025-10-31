
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
│   ├── scrape_io_listings.py # Daily scraper (Infrastructure Ontario) 
│   └── inspect_duckdb.py # Quick inspection & row counts │
├── streamlit_app/
│   └── app.py # Streamlit dashboard (interactive filters, charts) 
│
├── requirements.txt
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

`python scripts/scrape_io_listings.py` 

→ Creates a new folder like:

`data/raw/io_listings/2025-10-31/io_listings.csv` 

----------

### 2. Run dbt Transformations

`cd dbt
dbt run
dbt test` 

-   `stg_io_listings_all` unions all daily CSVs
    
-   `fact_listing_daily` is **incremental**, appending new data daily
    
-   `fact_listing_current` and marts refresh fully
    

----------

### 3. Inspect DuckDB Data

`python scripts/inspect_duckdb.py --db dbt/target/io.duckdb --limit 5` 

Displays:

-   Tables and row counts
    
-   Top rows for staging, facts, and marts
    
-   Region-level sample summaries
    

----------

### 4. Launch Streamlit Dashboard

`streamlit run streamlit_app/app.py` 

**Features:**

-   Toggle between **Current** and **Historical** listings
    
-   Filter by Region, City, and Status
    
-   Choose date range (for Historical mode)
    
-   Metrics (listing count, median price/sqft/acres)
    
-   Charts (price distribution, weekly trends)
    
-   Full table of filtered results
    

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

## 🪜 Next Steps

|Stage|Description|Status|
|---|---|---|
|**Data Validation**|Add Great Expectations or dbt data_tests|⏳ Planned
|**Automation**|Airflow DAG for scrape + dbt + Streamlit|⏳ Future|
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

## 🧱 Version History

|Branch|Description|Key Changes|
|---|---|---|
|`main`|Base ingestion and repo scaffold|Scraper + normalization logic|
|`feature/dbt-setup`|Added dbt project|dbt_project.yml, staging & dim models, tests|
|`feature/dbt-incremental`|Introduced incremental loads| `fact_listing_daily`,schema drift handling|
|`feature/dashboard`|Added Streamlit visualization|`app.py`, filters, charts, KPIs|
|`main` (merged)|Current stable release|Fully working local pipeline from scrape → dbt → Streamlit|