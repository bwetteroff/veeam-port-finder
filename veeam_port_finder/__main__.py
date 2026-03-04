"""CLI entry for veeam_port_finder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from . import __version__
from .crawler import crawl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="veeam-port-finder",
        description="Veeam Port Finder CLI",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("--version", help="Show version and exit")

    crawl_p = sub.add_parser("crawl", help="Crawl a URL and extract ports")
    crawl_p.add_argument("url", help="Start URL to crawl")
    crawl_p.add_argument("--max-pages", type=int, default=20, help="Maximum pages to crawl")
    crawl_p.add_argument("--no-same-domain", dest="same_domain", action="store_false", help="Do not restrict to same domain")
    crawl_p.add_argument("--json", action="store_true", help="Output results as JSON")
    crawl_p.add_argument("--output", help="Write results to an Excel file (XLSX)")

    parser.add_argument("--version", action="store_true", help="Show version and exit")

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    if args.cmd == "crawl":
        results = []
        for url, ports in crawl(args.url, max_pages=args.max_pages, same_domain=args.same_domain):
            # ports is a list of dicts: {port, protocols, services}
            out = {"url": url, "ports": ports}
            results.append(out)
            if args.json:
                print(json.dumps(out))
            else:
                print(url)
                if ports:
                    lines = []
                    for p in ports:
                        port_num = p.get("port")
                        proto = ", ".join(p.get("protocols", []))
                        serv = ", ".join(p.get("services", []))
                        parts = [str(port_num)]
                        if proto:
                            parts.append(f"proto: {proto}")
                        if serv:
                            parts.append(f"svc: {serv}")
                        lines.append(" (".join([parts[0], ", ".join(parts[1:])]) + ")" if len(parts) > 1 else parts[0])
                    print("  ports:", ", ".join(lines))
                else:
                    print("  ports: none found")
        if args.json:
            print(json.dumps(results))

        if getattr(args, "output", None):
            out_path = Path(args.output)
            rows = []
            for r in results:
                ports_list = [str(p.get("port")) for p in r["ports"]]
                protocols_set = set()
                services_set = set()
                for p in r["ports"]:
                    for pr in p.get("protocols", []):
                        protocols_set.add(pr)
                    for sv in p.get("services", []):
                        services_set.add(sv)
                rows.append({
                    "url": r["url"],
                    "ports": ", ".join(ports_list),
                    "protocols": ", ".join(sorted(protocols_set)),
                    "services": ", ".join(sorted(services_set)),
                })
            df = pd.DataFrame(rows)
            df.to_excel(out_path, index=False)

        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
