# Veeam Port Finder

A small utility to discover and collect port requirements from Veeam documentation pages.

This repository contains the original scripts and a new Python package scaffold (`veeam_port_finder`) with a CLI entrypoint to build on.

## Features

- Crawl single pages or whole site trees and extract port information from tables and text.
- Export results to Excel (existing scripts use `pandas` / `openpyxl`).
- Small CLI scaffold and tests to extend functionality.

## Installation

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Usage

Run the original script to process a single page:

```powershell
python VeeamPortFinder.py --url https://helpcenter.veeam.com/docs/backup/compatibility/ports.html --output veeam_ports.xlsx
```

Or (future) use the package CLI scaffold:

```powershell
python -m veeam_port_finder --version
```

Notes:

- The current extractor looks for HTML tables and paragraphs/lists mentioning port numbers. Parsing may need refinement for some pages.
- If you want a focused extractor for a particular Veeam KB page, I can add page-specific rules.

## Development

- Run tests:

```powershell
python -m pytest -q
```

- Add features inside `veeam_port_finder/` and add unit tests under `tests/`.

## Contributing

Open an issue or pull request. For local development, create branches from `main` and open PRs when ready.

## Repository

The package is published at: https://github.com/bwetteroff/veeam-port-finder

