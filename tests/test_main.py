import sys
from veeam_port_finder import __version__
from veeam_port_finder import __main__ as vp_main


def test_version_output(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["veeam-port-finder", "--version"])
    vp_main.main()
    captured = capsys.readouterr()
    assert __version__ in captured.out
