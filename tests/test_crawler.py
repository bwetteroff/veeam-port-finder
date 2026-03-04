from veeam_port_finder.crawler import extract_ports_from_html


def test_extract_ports_from_html():
    html = """
    <html><body>
    <p>Service listens on port 443 for HTTPS.</p>
    <ul><li>Optional port 6180</li></ul>
    <table><tr><td>Port</td><td>9443</td></tr></table>
    </body></html>
    """
    # include an unrelated number that should be ignored unless heuristics fail
    html += "<p>Build number 9999 - unrelated</p>"
    port_entries = extract_ports_from_html(html)
    ports = [p["port"] for p in port_entries]
    assert 443 in ports
    assert 6180 in ports
    assert 9443 in ports
    assert 9999 not in ports

    # check that 443 has an inferred service/protocol (HTTPS was present)
    entry_443 = next(p for p in port_entries if p["port"] == 443)
    assert ("https" in entry_443.get("services", [])) or ("https" in entry_443.get("protocols", []))
