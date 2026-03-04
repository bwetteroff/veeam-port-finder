"""VeeamPortFinder

Scrape Veeam documentation pages for port requirements and export to Excel.

Usage examples:
  python VeeamPortFinder.py --url https://helpcenter.veeam.com/docs/backup/compatibility/ports.html --output veeam_ports.xlsx
  python VeeamPortFinder.py --url https://helpcenter.veeam.com --follow-links --output veeam_ports.xlsx

Requirements: see requirements.txt
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import List, Dict

try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
except ModuleNotFoundError as e:
    missing = str(e).split("'")[1] if "'" in str(e) else str(e)
    print(
        "Missing required Python packages. Please install dependencies:"
    )
    print("  python -m pip install -r requirements.txt")
    print(f"Missing module: {missing}")
    raise


PORT_REGEX = re.compile(r"\b\d{1,5}(?:[-–]\d{1,5})?(?:,\s*\d{1,5})*\b")


def fetch(url: str, session: requests.Session, timeout: int = 15, verify: bool = True) -> str:
    resp = session.get(url, timeout=timeout, verify=verify)
    resp.raise_for_status()
    return resp.text


def find_port_tables(soup: BeautifulSoup) -> List[Dict[str, str]]:
    rows = []
    tables = soup.find_all("table")
    for tbl in tables:
        # collect headers (if present)
        headers = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
        # fallback: try first row as header if th missing
        if not headers:
            first_tr = tbl.find("tr")
            if first_tr:
                first_cells = [td.get_text(strip=True).lower() for td in first_tr.find_all("td")]
                # treat as headers if any cell contains 'port' or 'protocol' or 'service'
                if any("port" in c or "protocol" in c or "service" in c for c in first_cells):
                    headers = first_cells

        has_port_header = any("port" in h for h in headers)

        for tr in tbl.find_all("tr"):
            # gather cells (including th if used in rows)
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            if not cells:
                continue

            row_text = " ".join(cells)
            # detect port-like content either by header or by regex match in row
            if has_port_header or PORT_REGEX.search(row_text) or re.search(r"\bTCP\b|\bUDP\b", row_text, re.I):
                entry = {}
                if headers and len(headers) == len(cells):
                    for h, c in zip(headers, cells):
                        entry[h] = c
                else:
                    # fallback: put into generic columns
                    for i, c in enumerate(cells, start=1):
                        entry[f"col{i}"] = c

                # normalize port/protocol from row text if not present in columns
                entry.setdefault("port", "")
                entry.setdefault("protocol", "")

                # map any header that contains 'port' or 'protocol' into normalized keys
                for k in list(entry.keys()):
                    if "port" in k:
                        entry["port"] = entry.get(k) or entry["port"]
                    if "protocol" in k:
                        entry["protocol"] = entry.get(k) or entry["protocol"]

                # attempt to extract protocol/port patterns from row text
                pp = parse_port_proto(row_text)
                if pp.get("port") and not entry["port"]:
                    entry["port"] = pp.get("port")
                if pp.get("protocol") and not entry["protocol"]:
                    entry["protocol"] = pp.get("protocol")

                entry["_row_text"] = row_text
                rows.append(entry)

    return rows


def find_port_mentions(soup: BeautifulSoup) -> List[Dict[str, str]]:
    rows = []
    # search common textual containers
    for el in soup.find_all(["p", "li", "code", "pre", "dd"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        # look for protocol + port patterns like 'TCP 2500-2504' or '2500 (TCP)'
        pp = parse_port_proto(text)
        if pp.get("port"):
            entry = {"port": pp.get("port"), "protocol": pp.get("protocol", ""), "description": text, "_row_text": text}
            rows.append(entry)

    # also scan headings with following sibling text (common in docs where headings describe a port)
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        htext = h.get_text(" ", strip=True)
        if "port" in htext.lower() or re.search(r"\bport\b", htext, re.I):
            sib = h.find_next_sibling()
            if sib:
                text = sib.get_text(" ", strip=True)
                pp = parse_port_proto(text)
                if pp.get("port"):
                    rows.append({"port": pp.get("port"), "protocol": pp.get("protocol", ""), "description": text, "_row_text": text})

    return rows


def parse_port_proto(text: str) -> Dict[str, str]:
    """Extract a port (or range/comma list) and optional protocol from free text."""
    res: Dict[str, str] = {}
    # try patterns like 'TCP 1234', 'TCP: 1234-1236', '1234 (TCP)'
    m = re.search(r"\b(TCP|UDP)[:\s]*([\d,\-– ]{1,30})", text, re.I)
    if m:
        res["protocol"] = m.group(1).upper()
        res["port"] = m.group(2).strip()
        return res

    m2 = re.search(r"([\d]{1,5}(?:[-–][\d]{1,5})?(?:,\s*[\d]{1,5})*)\s*\(?\s*(TCP|UDP)\s*\)?", text, re.I)
    if m2:
        res["port"] = m2.group(1)
        res["protocol"] = m2.group(2).upper()
        return res

    # generic 'port(s): 1234, 2345-2347' or 'ports 1234-1236'
    m3 = re.search(r"port[s]?[:\s]*([\d,\-– ]{1,50})", text, re.I)
    if m3:
        res["port"] = m3.group(1).strip()
        # try to infer protocol near the match
        nearby = text[max(0, m3.start()-30):m3.end()+30]
        mp = re.search(r"\b(TCP|UDP)\b", nearby, re.I)
        if mp:
            res["protocol"] = mp.group(1).upper()
        return res

    # fallback: any port-like number
    m4 = PORT_REGEX.search(text)
    if m4:
        res["port"] = m4.group(0)
    return res


def crawl_and_extract(start_url: str, follow_links: bool = False, max_pages: int = 20, verify: bool = True) -> List[Dict[str, str]]:
    session = requests.Session()
    session.headers.update({"User-Agent": "VeeamPortFinder/1.0 (+https://github.com)"})

    parsed = requests.utils.urlparse(start_url)
    base_netloc = parsed.netloc

    to_visit = [start_url]
    visited = set()
    results: List[Dict[str, str]] = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            html = fetch(url, session, verify=verify)
        except Exception:
            visited.add(url)
            continue

        soup = BeautifulSoup(html, "html.parser")
        # extract tables and mentions
        results.extend(find_port_tables(soup))
        results.extend(find_port_mentions(soup))

        visited.add(url)

        if follow_links:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                abs_url = requests.compat.urljoin(url, href)
                p = requests.utils.urlparse(abs_url)
                # only follow same site links
                if p.netloc == base_netloc and abs_url not in visited and abs_url not in to_visit:
                    # quick filter for likely docs pages
                    if "port" in abs_url.lower() or "ports" in abs_url.lower() or "/docs/" in abs_url.lower():
                        to_visit.append(abs_url)

    return results


def rows_to_dataframe(rows: List[Dict[str, str]], source_url: str) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    # normalize dicts to same columns
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    # ensure stable order: prefer common columns
    preferred = ["port", "protocol", "description", "from", "to"]
    other_keys = sorted(k for k in all_keys if k not in preferred)
    columns = [k for k in preferred if k in all_keys] + other_keys

    normalized = []
    for r in rows:
        nr = {k: r.get(k, "") for k in columns}
        nr["source_url"] = source_url
        normalized.append(nr)

    df = pd.DataFrame(normalized)
    # try to promote the 'port' column to front if present
    if "port" in df.columns:
        cols = [c for c in df.columns if c != "port"]
        df = df[["port"] + cols]
    return df


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scrape Veeam docs for port requirements and export to Excel")
    ap.add_argument("--url", required=True, help="Start URL to scrape (single page or index)")
    ap.add_argument("--output", default="veeam_ports.xlsx", help="Excel output filename")
    ap.add_argument("--follow-links", action="store_true", help="Follow same-site links to find more pages")
    ap.add_argument("--max-pages", type=int, default=20, help="Max pages to crawl when following links")
    ap.add_argument("--insecure", action="store_true", help="Disable SSL certificate verification (use only for testing)")
    args = ap.parse_args(argv)

    rows = crawl_and_extract(args.url, follow_links=args.follow_links, max_pages=args.max_pages, verify=(not args.insecure))

    if not rows:
        print("No port information found on the provided page(s).")
        return 1

    df = rows_to_dataframe(rows, args.url)
    if df.empty:
        print("No structured data to write.")
        return 1

    # normalize port strings to reduce trivial duplicates
    if "port" in df.columns:
        df["port"] = df["port"].astype(str).str.replace("\s+", "", regex=True)

    # drop duplicates based on key columns if present
    key_cols = [c for c in ("port", "protocol", "description", "source_url") if c in df.columns]
    before = len(df)
    if key_cols:
        df = df.drop_duplicates(subset=key_cols)
    else:
        df = df.drop_duplicates()
    after = len(df)

    # write to excel
    try:
        df.to_excel(args.output, index=False)
    except Exception as e:
        print(f"Failed to write Excel file: {e}")
        return 2

    print(f"Wrote {after} rows to {args.output} (deduplicated from {before})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


