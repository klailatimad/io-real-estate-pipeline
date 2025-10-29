from __future__ import annotations
import re
from typing import Any, Optional
from bs4 import BeautifulSoup

def extract_form_state(soup: BeautifulSoup) -> dict[str, str]:
    fields = {}
    for name in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]:
        tag = soup.find("input", {"name": name})
        if tag and tag.get("value"):
            fields[name] = tag["value"]
    return fields

def find_pagination_postbacks(soup: BeautifulSoup) -> list[dict[str, str]]:
    anchors = soup.find_all("a", href=True)
    out: list[dict[str, str]] = []
    for a in anchors:
        href = a["href"]
        m = re.search(r"__doPostBack\('([^']+)'\s*,\s*'([^']*)'\)", href)
        if m:
            out.append({"target": m.group(1), "argument": m.group(2), "text": a.get_text(strip=True)})
    return out

def _get_results_table(soup: BeautifulSoup):
    table = soup.find("table", id=re.compile(r"gvPropertyList", re.I))
    if table:
        return table
    for t in soup.find_all("table"):
        hdrs = [th.get_text(strip=True) for th in t.find_all("th")]
        if any("Municipal Address" in h for h in hdrs):
            return t
    return None

def parse_results_table(soup: BeautifulSoup) -> list[dict[str, Any]]:
    table = _get_results_table(soup)
    if table is None:
        return []

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    idx = {h: i for i, h in enumerate(headers)}

    rows: list[dict[str, Any]] = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds or len(tds) != len(headers):
            continue

        def cell(h: str) -> str:
            return tds[idx[h]].get_text(strip=True) if h in idx else ""

        def link(h: str) -> Optional[str]:
            if h not in idx:
                return None
            a = tds[idx[h]].find("a", href=True)
            return a["href"] if a else None

        prop_id = cell("ID")
        if not re.fullmatch(r"\d+", prop_id or ""):
            continue

        rows.append({
            "property_id": prop_id,
            "address": cell("Municipal Address"),
            "region": cell("Region"),
            "city": cell("City"),
            "acres": cell("Acres"),
            "sqft": cell("Square Feet"),
            "price_raw": cell("Price"),
            "status": cell("Status"),
            "mls_text": cell("MLS"),
            "posted": cell("Posted"),
            "mls_url": link("MLS"),
            "details_url": link("Details"),
            "image_url": link("Image"),
        })
    return rows
