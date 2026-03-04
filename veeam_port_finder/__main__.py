"""CLI entry for veeam_port_finder."""
from __future__ import annotations

import argparse
from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="veeam-port-finder",
        description="Veeam Port Finder CLI (scaffold)",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    print("Veeam Port Finder CLI — no commands implemented yet.")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
