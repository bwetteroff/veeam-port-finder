# Veeam Port Finder

This script scrapes Veeam documentation pages for port requirements and exports the findings to an Excel file.

Quick start:

1. Create and activate a Python environment (recommended).

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the script for a single page:

```bash
python VeeamPortFinder.py --url https://helpcenter.veeam.com/docs/backup/compatibility/ports.html --output veeam_ports.xlsx
```

4. Or crawl the site for pages with port info (follow same-site links):

```bash
python VeeamPortFinder.py --url https://helpcenter.veeam.com --follow-links --max-pages 50 --output veeam_ports.xlsx
```

Notes:

- The parser looks for HTML tables and paragraph/list items that mention ports. It may need tweaking for specific Veeam pages.
- If you want tailored parsing for a particular Veeam KB page, I can refine the extraction rules.

## Scaffolded CLI package

I added a small Python CLI scaffold in the `veeam_port_finder` package with a basic entrypoint.

Usage (scaffold):

```
python -m veeam_port_finder --version
```

The package files are in `veeam_port_finder/` and a simple pytest test is in `tests/`.
