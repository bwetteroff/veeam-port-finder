import os
from pathlib import Path

import pandas as pd

import veeam_port_finder.__main__ as vp_main


def test_crawl_writes_excel(tmp_path, monkeypatch):
    # monkeypatch the crawl function to avoid network
    sample = [("https://example.com/page1", [443, 9443]), ("https://example.com/page2", [6180])]

    def fake_crawl(url, max_pages=20, same_domain=True):
        for item in sample:
            yield item

    monkeypatch.setattr(vp_main, "crawl", fake_crawl)

    out_file = tmp_path / "results.xlsx"
    # call main with our args
    rc = vp_main.main(["crawl", "https://example.com", "--max-pages", "2", "--output", str(out_file)])
    assert rc == 0
    assert out_file.exists()

    # read the excel and verify contents
    df = pd.read_excel(out_file)
    assert "url" in df.columns
    assert "ports" in df.columns
    urls = list(df["url"])
    assert "https://example.com/page1" in urls
    assert "https://example.com/page2" in urls
