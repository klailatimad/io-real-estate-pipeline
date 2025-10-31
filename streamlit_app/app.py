import os
import duckdb
import pandas as pd
import altair as alt
import streamlit as st
from datetime import date


# ---------- Config ----------
st.set_page_config(page_title="Ontario IO Listings", layout="wide")
DB_PATH = os.getenv("IO_DUCKDB_PATH", "dbt/target/io.duckdb")

@st.cache_resource(show_spinner=False)
def get_conn():
    return duckdb.connect(DB_PATH, read_only=True)

@st.cache_data(ttl=60, show_spinner=False)
def load_dim_location():
    con = get_conn()
    return con.sql("""
        select location_id, city, region
        from dim_location
        order by region, city
    """).df()

@st.cache_data(ttl=60, show_spinner=False)
def load_current(filters):
    con = get_conn()
    base = """
      select f.property_id, l.city, l.region, f.as_of_date, f.price, f.status,
             f.acres, f.sqft
      from fact_listing_current f
      join dim_location l using (location_id)
      where 1=1
    """
    params = []
    if filters["regions"]:
        base += " and l.region in ({})".format(",".join(["?"]*len(filters["regions"])))
        params += filters["regions"]
    if filters["cities"]:
        base += " and l.city in ({})".format(",".join(["?"]*len(filters["cities"])))
        params += filters["cities"]
    if filters["status"]:
        base += " and f.status in ({})".format(",".join(["?"]*len(filters["status"])))
        params += filters["status"]
    return con.execute(base, params).df()

@st.cache_data(ttl=60, show_spinner=False)
def load_price_trends(filters):
    con = get_conn()
    base = """
      select city, region, week_start, median_price, listings
      from mart_price_trends
      where 1=1
    """
    params = []
    if filters["regions"]:
        base += " and region in ({})".format(",".join(["?"]*len(filters["regions"])))
        params += filters["regions"]
    if filters["cities"]:
        base += " and city in ({})".format(",".join(["?"]*len(filters["cities"])))
        params += filters["cities"]
    return con.execute(base, params).df()

# ---------- Sidebar filters ----------
st.sidebar.title("Filters")

loc = load_dim_location()
regions = sorted(loc["region"].dropna().unique().tolist())
cities = sorted(loc["city"].dropna().unique().tolist())

mode = st.sidebar.radio("Mode", ["Current", "Historical"], horizontal=True, key="mode_picker")

sel_regions = st.sidebar.multiselect("Region", regions, key="region_filter")
cities_scoped = sorted(
    loc.loc[loc["region"].isin(sel_regions), "city"].unique().tolist()
) if sel_regions else sorted(loc["city"].dropna().unique().tolist())
sel_cities  = st.sidebar.multiselect("City", cities_scoped, key="city_filter")

status_choices = [
    "Listed on the Open Market", "Under Review", "In Negotiations for Direct Sale",
    "Sold", "Not Applicable", "n/a", ""
]
sel_status  = st.sidebar.multiselect("Status", status_choices, key="status_filter")

# cache-buster
if st.sidebar.button("Reload data"):
    st.cache_data.clear()

filters = {"regions": sel_regions, "cities": sel_cities, "status": sel_status}

# ---------- Data selection (single source of truth) ----------
if mode == "Current":
    # No date picker in Current mode
    df_display = load_current(filters)
    trend = load_price_trends(filters)   # overall trend (or filter by city/region only)
    date_range_used = None

else:
    # Historical mode (one date_input only)
    con = get_conn()
    dmin, dmax = con.sql(
        "select min(posted_date), max(posted_date) from fact_listing_daily"
    ).fetchone()

    if dmin is None or dmax is None:
        st.info("No historical rows found yet. Run a scrape + dbt run to populate fact_listing_daily.")
        df_display = pd.DataFrame(columns=["property_id","city","region","as_of_date","price","status","acres","sqft"])
        trend = pd.DataFrame(columns=["city","region","week_start","median_price","listings"])
        date_range_used = None
    else:
        picker = st.sidebar.date_input(
            "Posted date range",
            value=(dmin, dmax),
            min_value=dmin,
            max_value=dmax
        )

        # normalize picker to (start, end)
        if isinstance(picker, (tuple, list)):
            if len(picker) == 2:
                start, end = picker
            elif len(picker) == 1:
                start = end = picker[0]
            else:
                start, end = dmin, dmax
        else:
            start = end = picker

        start = pd.to_datetime(start).date()
        end   = pd.to_datetime(end).date()
        if start > end:
            start, end = end, start
        date_range_used = (start, end)

        q = """
          select f.property_id, l.city, l.region, f.posted_date as as_of_date,
                 f.price, f.status, f.acres, f.sqft
          from fact_listing_daily f
          join dim_location l using (location_id)
          where f.posted_date between cast(? as date) and cast(? as date)
        """
        params = [start, end]

        if filters["regions"]:
            q += " and l.region in ({})".format(",".join(["?"] * len(filters["regions"])))
            params += filters["regions"]

        if filters["cities"]:
            q += " and l.city in ({})".format(",".join(["?"] * len(filters["cities"])))
            params += filters["cities"]

        if filters["status"]:
            q += " and f.status in ({})".format(",".join(["?"] * len(filters["status"])))
            params += filters["status"]

        df_display = con.execute(q, params).df()

        # trend filtered to same window (optional)
        trend = load_price_trends(filters)
        if not trend.empty:
            trend = trend[
                (trend["week_start"] >= pd.to_datetime(start)) &
                (trend["week_start"] <= pd.to_datetime(end))
            ]

# ---------- KPIs ----------
st.title(f"IO Properties – {'Current Listings' if mode=='Current' else 'Historical Listings'}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Listings", int(len(df_display)))
if df_display["price"].notna().any():
    c2.metric("Median price", f"${int(df_display['price'].median()):,}")
else:
    c2.metric("Median price", "n/a")
c3.metric("Median sqft", "n/a" if df_display["sqft"].dropna().empty else int(df_display["sqft"].median()))
c4.metric("Median acres", "n/a" if df_display["acres"].dropna().empty else round(float(df_display["acres"].median()), 3))

# ---------- Charts ----------
st.subheader("Price distribution")
if df_display["price"].dropna().empty:
    st.info("No price data available for the selected filters.")
else:
    hist = alt.Chart(df_display.dropna(subset=["price"])).mark_bar().encode(
        alt.X("price", bin=alt.Bin(maxbins=30), title="Price"),
        alt.Y("count()", title="Listings")
    ).properties(height=280)
    st.altair_chart(hist, use_container_width=True)

st.subheader("Weekly median price")
if trend.empty:
    st.info("No trend rows for the selected filters{}.".format(
        "" if not date_range_used else f" in {date_range_used[0]} to {date_range_used[1]}"
    ))
else:
    line = alt.Chart(trend).mark_line(point=True).encode(
        x=alt.X("week_start:T", title="Week"),
        y=alt.Y("median_price:Q", title="Median price"),
        color=alt.Color("city:N", title="City")
    ).properties(height=300)
    st.altair_chart(line, use_container_width=True)

# ---------- Table ----------
st.subheader("Listings")
show_cols = ["property_id", "city", "region", "as_of_date", "status", "price", "acres", "sqft"]
if "as_of_date" not in df_display.columns and "posted_date" in df_display.columns:
    df_display = df_display.rename(columns={"posted_date": "as_of_date"})
st.dataframe(
    df_display[show_cols].sort_values(
        ["region", "city", "as_of_date"], ascending=[True, True, False]
    ),
    use_container_width=True
)

st.caption(
    f"DB: {DB_PATH} • Mode: {mode} • Regions: {sel_regions or 'All'} | Cities: {sel_cities or 'All'} | "
    f"Status: {sel_status or 'All'}{' | Range: ' + str(date_range_used) if date_range_used else ''}"
)