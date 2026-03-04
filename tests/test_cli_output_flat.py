import os
from pathlib import Path

import pandas as pd

import veeam_port_finder.__main__ as vp_main


def test_crawl_writes_excel_flat(tmp_path, monkeypatch):
    # monkeypatch the crawl function to avoid network
    sample = [
        ("https://example.com/page1", [{"port": 443, "protocols": ["https"], "services": ["https"]}, {"port": 9443, "protocols": [], "services": []}]),
        ("https://example.com/page2", [{"port": 6180, "protocols": [], "services": []}]),
    ]

    def fake_crawl(url, max_pages=20, same_domain=True):
        for item in sample:
            yield item

    monkeypatch.setattr(vp_main, "crawl", fake_crawl)

    out_file = tmp_path / "results_flat.xlsx"
    # call main with our args
    rc = vp_main.main(["crawl", "https://example.com", "--max-pages", "2", "--output", str(out_file), "--flat"])
    assert rc == 0
    assert out_file.exists()

    # read the excel and verify contents (flattened: one row per port)
    df = pd.read_excel(out_file)
    assert "url" in df.columns
    assert "port" in df.columns
    assert "protocols" in df.columns
    assert "services" in df.columns
    assert len(df) == 3
    assert 443 in list(df["port"])
    assert 9443 in list(df["port"])
    assert 6180 in list(df["port"])
