from __future__ import annotations
import argparse
import csv
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
import re

from src.common.io_utils import DEF_USER_AGENT, ensure_dir, polite_sleep, today_str
from src.ingestion.html_parsers import (
    extract_form_state,
    find_pagination_postbacks,
    parse_results_table,
)

BASE_URL = "https://apps.infrastructureontario.ca/propertiesforsale/Home.aspx"
DETAILS_BASE = "https://apps.infrastructureontario.ca/propertiesforsale/pspropertydetails.aspx"
IMAGE_BASE = "https://apps.infrastructureontario.ca/propertiesforsale/imageview.aspx"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch(session: requests.Session, url: str, method: str = "GET", data: Optional[dict] = None) -> requests.Response:
    if method == "POST":
        r = session.post(url, data=data, timeout=30)
    else:
        r = session.get(url, timeout=30)
    r.raise_for_status()
    return r

def discover_pages(session: requests.Session, page_size: str = "all", sleep: float = 1.0) -> list[BeautifulSoup]:
    soups: list[BeautifulSoup] = []

    resp = fetch(session, BASE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    tried_all = False
    if page_size.lower() == "all":
        postbacks = find_pagination_postbacks(soup)
        all_pb = next((pb for pb in postbacks if pb.get("text", "").lower() == "all"), None)
        if all_pb:
            tried_all = True
            form_state = extract_form_state(soup)
            payload = {
                "__EVENTTARGET": all_pb["target"],
                "__EVENTARGUMENT": all_pb.get("argument", ""),
                **form_state,
            }
            resp = fetch(session, BASE_URL, method="POST", data=payload)
            soup = BeautifulSoup(resp.text, "html.parser")
            # After attempting All, keep going below. We will still fall back to paging if needed.

    soups.append(soup)

    # Fallback: if All wasn't available or didn't increase rows, iterate numeric pages
    postbacks = find_pagination_postbacks(soup)
    page_pbs = [pb for pb in postbacks if pb.get("text", "").isdigit()]

    # If there are no numeric pages, we're done (either All worked or only one page exists)
    if not page_pbs:
        return soups

    # keep first postback for each page label (avoids top+bottom duplicates)
    uniq_by_label = {}
    for pb in page_pbs:
        label = pb.get("text")
        if label not in uniq_by_label:
            uniq_by_label[label] = pb

    for label, pb in sorted(uniq_by_label.items(), key=lambda kv: int(kv[0])):
        if label == "1":
            continue
        form_state = extract_form_state(soup)
        payload = {"__EVENTTARGET": pb["target"], "__EVENTARGUMENT": pb.get("argument", ""), **form_state}
        polite_sleep(sleep)
        r = fetch(session, BASE_URL, method="POST", data=payload)
        soups.append(BeautifulSoup(r.text, "html.parser"))

    return soups


def normalize_rows(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).drop_duplicates(subset=["property_id", "address", "posted"], keep="first")

    def to_float(x: Optional[str]) -> Optional[float]:
        if x is None:
            return None
        x = str(x).replace(",", "").strip()
        try:
            return float(x)
        except Exception:
            return None

    def clean_price(x: Optional[str]) -> Optional[float]:
        if not x:
            return None
        digits = "".join(ch for ch in str(x) if ch.isdigit() or ch == ".")
        return float(digits) if digits else None

    df["acres_val"] = df["acres"].apply(to_float)
    df["sqft_val"] = df["sqft"].apply(to_float)
    df["price"] = df["price_raw"].apply(clean_price)

    def parse_date(s: Optional[str]) -> Optional[str]:
        if not s:
            return None
        try:
            return pd.to_datetime(s, errors="coerce").date().isoformat()
        except Exception:
            return None

    df["posted_date"] = df["posted"].apply(parse_date)

    def abs_url(u: Optional[str], base: str) -> Optional[str]:
        if not u:
            return None
        if u.startswith("http"):
            return u
        if u.startswith("/"):
            return f"https://apps.infrastructureontario.ca{u}"
        if "?" in u:
            return f"https://apps.infrastructureontario.ca/propertiesforsale/{u}"
        return f"{base}?{u}"

    df["details_abs"] = df["details_url"].apply(lambda u: abs_url(u, DETAILS_BASE))
    df["image_abs"] = df["image_url"].apply(lambda u: abs_url(u, IMAGE_BASE))

    df["ingested_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    cols = [
        "property_id", "address", "city", "region",
        "acres", "acres_val", "sqft", "sqft_val",
        "price_raw", "price", "status", "mls_text", "mls_url",
        "posted", "posted_date", "details_abs", "image_abs", "ingested_at"
    ]
    return df[cols]

def download_image_pdfs(session: requests.Session, df: pd.DataFrame, out_dir: str, sleep: float = 1.0, limit: Optional[int] = None) -> None:
    if df.empty:
        return
    out = ensure_dir(out_dir)
    n = 0
    for _, row in df.iterrows():
        if limit is not None and n >= limit:
            break
        url = row.get("image_abs")
        pid = row.get("property_id")
        if not url or not pid:
            continue
        dest = out / f"{pid}.pdf"
        if dest.exists():
            n += 1
            print(f"Exists {n}: {dest}")
            continue
        try:
            r = fetch(session, url)
            with open(dest, "wb") as f:
                f.write(r.content)
            n += 1
            print(f"Downloaded {n}: {dest}")
        except Exception:
            print(f"Failed image for {pid}")
        polite_sleep(sleep)

def main():
    ap = argparse.ArgumentParser(description="Scrape IO Properties grid -> CSV/Parquet snapshot")
    ap.add_argument("--out", required=True, help="Output folder for daily snapshots")
    ap.add_argument("--download-images", action="store_true", help="Download per-property PDF maps")
    ap.add_argument("--images-dir", default="data/raw/images", help="Where to save images if downloading")
    ap.add_argument("--image-limit", type=int, default=10, help="Max images to fetch this run (safety)")
    ap.add_argument("--page-size", choices=["50", "100", "150", "all"], default="all")
    ap.add_argument("--sleep", type=float, default=1.0, help="Seconds between requests")
    args = ap.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": DEF_USER_AGENT})

    soups = discover_pages(session, page_size=args.page_size, sleep=args.sleep)

    all_rows: list[dict] = []
    for soup in soups:
        rows = parse_results_table(soup)
        all_rows.extend(rows)

    # for i, sp in enumerate(soups, start=1):
    #     rows = parse_results_table(sp)
    #     # print(f"Page {i}: parsed {len(rows)} rows")
    #     all_rows.extend(rows)

    df = normalize_rows(all_rows)
    if df.empty:
        print("No rows parsed; check selectors or site changes.")
        return
    
    def parse_total_records(soup: BeautifulSoup) -> int | None:
        text = soup.get_text(" ", strip=True)
        m = re.search(r"Total Records:\s*(\d+)", text)
        return int(m.group(1)) if m else None

    # after collecting all soups and building df:
    total_records = parse_total_records(soups[0])
    unique_props = df["property_id"].nunique()
    # print(f"Site total_records={total_records}, unique_property_ids={unique_props}")

    day = today_str()
    out_dir = ensure_dir(os.path.join(args.out, day))
    csv_path = out_dir / "io_listings.csv"
    pq_path = out_dir / "io_listings.parquet"
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    df.to_parquet(pq_path, index=False)
    print(f"Wrote {len(df)} cleaned rows -> {csv_path} and {pq_path}")

    if args.download_images:
        download_image_pdfs(session, df, args.images_dir, sleep=args.sleep, limit=args.image_limit)
        print("Image download step completed (best-effort).")

if __name__ == "__main__":
    main()
