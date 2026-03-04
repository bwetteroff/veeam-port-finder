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
    text = "\n".join(p.get_text(" ") for p in soup.find_all(["p", "li", "td", "th"]))
    found = set()
    for m in re.finditer(r"\b(\d{1,5})\b", text):
        num = int(m.group(1))
        if 0 < num <= 65535:
            found.add(num)
    # prefer numbers near the word 'port' when possible
    ports = sorted(found)
    return ports


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
