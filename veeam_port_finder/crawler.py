from __future__ import annotations

import re
from collections import deque
from typing import Iterable

import requests
from bs4 import BeautifulSoup


PORT_RE = re.compile(r"\b(?:port|ports)[:\s]*([0-9]{1,5})(?:\b|[^0-9])", re.I)


def fetch_html(url: str, timeout: int = 10) -> str:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_ports_from_html(html: str) -> list[int]:
    soup = BeautifulSoup(html, "html.parser")

    # Gather candidate numbers found near explicit 'port' keywords
    candidates: set[int] = set()

    # Join key textual elements for context scanning
    text_nodes = [p.get_text(" ") for p in soup.find_all(["p", "li"]) ]
    text = "\n".join(text_nodes)

    # 1) Direct patterns like 'port 443' or 'ports: 80, 443'
    for m in re.finditer(r"\b(?:port|ports)\b[^\d\n]*([0-9]{1,5})(?:[^0-9]|$)", text, re.I):
        num = int(m.group(1))
        if 0 < num <= 65535:
            candidates.add(num)

    # 2) Look per-sentence: if a sentence contains 'port', capture numbers inside that sentence
    for sentence in re.split(r"[\.\n\r!?]+", text):
        if "port" in sentence.lower():
            for n in re.finditer(r"\b(\d{1,5})\b", sentence):
                num = int(n.group(1))
                if 0 < num <= 65535:
                    candidates.add(num)

    # 3) Table-aware extraction: if a table has a header cell mentioning 'port', take numeric cells
    for table in soup.find_all("table"):
        # look for header cells mentioning 'port' — accept th or first-row td
        headers = [th.get_text(" ").strip().lower() for th in table.find_all("th")]
        if not headers:
            # check first row td cells as fallback header
            first_row = table.find("tr")
            if first_row:
                headers = [td.get_text(" ").strip().lower() for td in first_row.find_all("td")]

        if any("port" in h for h in headers):
            for td in table.find_all("td"):
                for n in re.finditer(r"\b(\d{1,5})\b", td.get_text()):
                    num = int(n.group(1))
                    if 0 < num <= 65535:
                        candidates.add(num)

    # 4) Fallback: if no candidate ports were found via heuristics, fall back to any numbers in key text
    if not candidates:
        for n in re.finditer(r"\b(\d{1,5})\b", text):
            num = int(n.group(1))
            if 0 < num <= 65535:
                candidates.add(num)

    return sorted(candidates)


def crawl(start_url: str, max_pages: int = 50, same_domain: bool = True) -> Iterable[tuple[str, list[int]]]:
    parsed = requests.utils.urlparse(start_url)
    base_netloc = parsed.netloc

    q = deque([start_url])
    seen = set([start_url])

    while q and len(seen) <= max_pages:
        url = q.popleft()
        try:
            html = fetch_html(url)
        except Exception:
            continue
        ports = extract_ports_from_html(html)
        yield url, ports

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            next_url = requests.compat.urljoin(url, href)
            if next_url in seen:
                continue
            if same_domain:
                if requests.utils.urlparse(next_url).netloc != base_netloc:
                    continue
            seen.add(next_url)
            q.append(next_url)
