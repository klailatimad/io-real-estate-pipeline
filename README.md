# 🏗️ Ontario Infrastructure Ontario (IO) Properties – Data Pipeline PoC

A **local-first data engineering project** to ingest, clean, and prepare Ontario’s public **Infrastructure Ontario “Properties for Sale”** dataset for analysis and future cloud deployment.  
The goal is to design and practice a full **end-to-end data pipeline** — from ingestion and transformation to visualization — using modern data tools.

----------

## 🚀 Project Overview

This project demonstrates how to:

-   **Ingest** real estate listings data directly from a public ASP.NET WebForms site using Python and BeautifulSoup.
    
-   Handle **pagination and form postbacks** (via `__VIEWSTATE`, `__EVENTVALIDATION`).
    
-   **Normalize and clean** property-level data (e.g., prices, acres, square footage, dates).
    
-   **Persist** structured data as daily **CSV and Parquet snapshots**.
    
-   Optionally **download PDF property maps** for binary data handling practice.
    
-   Prepare for downstream **dbt transformations** and **Streamlit dashboarding**.
    

All work runs locally for compliance and reproducibility.  
The project will later evolve into a full local-to-cloud pipeline (dbt + Great Expectations + Streamlit + Airflow or Dagster).

----------

## 🧱 Repository Structure

```
io-properties-pipeline/
  ├── README.md
  ├── requirements.txt
  ├── .env.example
  ├── .gitignore
  ├── src/
  │   ├── common/
  │   │   └── io_utils.py
  │   └── ingestion/
  │       ├── io_scrape.py
  │       └── html_parsers.py
  ├── data/
  │   └── raw/
  │       ├── io_listings/         # daily snapshots (CSV + Parquet)
  │       └── images/              # optional per-property PDF maps
  └── scripts/
      └── run_scrape_once.sh
```

----------

## ⚙️ Current Capabilities

| Feature | Description | 
| -------- | -------- |
| **Web Scraper** | Extracts listings from Infrastructure Ontario’s “Properties for Sale” portal | 
|**Pagination Handler**|Handles ASP.NET `__doPostBack` pagination|
|**Data Normalization**|Cleans and types numeric/date fields (price, acres, sqft, posted date)|
|**Snapshotting**|Saves daily CSV and Parquet outputs under `data/raw/io_listings/YYYY-MM-DD/`|
|**Polite Throttling**|Configurable request sleep interval for responsible scraping|
|**PDF Downloads**|Optional image/PDF fetch for each property|
|**Deduplication**|Prevents repeated records between page sets|
|**Logging**|Prints page-by-page row counts and total record summary|

----------

## 🧩 Tools Used

-   **Python 3.11+**
    
-   `requests`, `beautifulsoup4`, `pandas`, `pyarrow`
    
-   `tenacity` for retry logic
    
-   `dotenv` for local configuration
    
-   (Planned) **dbt**, **DuckDB**, **Streamlit**, **Great Expectations**
    

----------

## 📊 Steps Completed So Far

1.  **Exploration of public Ontario data sources** for suitable real estate data.
    
2.  Identified **Infrastructure Ontario “Properties for Sale”** as viable source.
    
3.  Built **modular ingestion code** (`io_scrape.py` and `html_parsers.py`) handling ASP.NET pagination.
    
4.  Added **data normalization** (price, sqft, acres, posted date).
    
5.  Implemented **daily snapshot persistence** (CSV + Parquet).
    
6.  Validated correctness — **153 total listings** parsed, matching the portal’s “Total Records: 153”.
    
7.  Established **folder structure and helper utilities** for reusability.
    
8.  Created **README documentation and repo scaffold** for version control setup.
    

----------

## 🪜 Next Steps

|Stage|Description|Status|
|---|---|---|
|**Data Validation**|Add Great Expectations suite for raw data integrity|⏳ Planned|
|**Transformations (dbt)**|Create DuckDB-based `stg_io_listings` model with data typing|⏳ Planned|
|**Visualization**|Build Streamlit dashboard (filter, KPIs, price histogram)|⏳ Planned|
|**Automation**|Wrap ingestion into Airflow or Dagster DAG|⏳ Future
|**Cloud Migration**|Move data & transformations to Azure/AWS for end-to-end demo|⏳ Future|

----------

## 💡 Future Enhancements

-   Scrape or integrate additional sources (TRREB/CREA, StatsCan) for comparison.
    
-   Add property “details page” enrichment for broker info.
    
-   Develop a “property history” model (e.g., price or status changes over time).
    
-   Build unit tests and a CI workflow with GitHub Actions.
    
-   Parameterize and containerize the pipeline via Docker Compose.
    

----------

## 🛡️ Data Use Disclaimer

This project is for **educational and non-commercial purposes** only.  
The Infrastructure Ontario property data is publicly accessible, but redistribution or publication is not permitted.  
If demonstrating work publicly (e.g., GitHub portfolio), **avoid including raw data** and instead show schemas, charts, or mock samples.

----------
