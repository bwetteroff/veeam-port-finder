from veeam_port_finder.crawler import extract_ports_from_html


def test_extract_ports_from_html():
    html = """
    <html><body>
    <p>Service listens on port 443 for HTTPS.</p>
    <ul><li>Optional port 6180</li></ul>
    <table><tr><td>Port</td><td>9443</td></tr></table>
    </body></html>
    """
    ports = extract_ports_from_html(html)
    assert 443 in ports
    assert 6180 in ports
    assert 9443 in ports
