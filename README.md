# Personal finances

Fetch personal finance data from Google Sheets and generate interactive HTML reports with charts and transaction drill-downs.

## Overview

Data is pulled from per-year Google Sheets (`Spending-YYYY`), parsed into a typed Python model, cached as pickle files, and rendered via Jinja2 templates into a set of static HTML pages. The frontend uses Chart.js for charts and Bootstrap for layout; all assets are bundled by Webpack.

```
Google Sheets → gspread → finances-YYYY.pickle → Jinja2 → output/index.html
                                                         → output/transactions-M-YYYY.html
```

The summary page (`index.html`) shows:
- Stacked bar chart of all spending categories across all years
- Line chart of category monthly averages over time
- Per-year stacked bar charts with a sortable breakdown table linking to monthly detail

Each monthly detail page (`transactions-M-YYYY.html`) shows:
- Pie chart of spending by category (excluding income)
- Filterable, sortable transaction table

## Prerequisites

**Node (via nvm):**
```bash
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# restart shell, then:
nvm install 20
nvm use 20
npm install
```

**Python:** requires Python 3.10+.

## Setup

```bash
make install   # Create venv, install Python deps, set up pre-commit hooks, build Webpack bundle
make test      # Run unit tests to verify the installation
```

## Google Sheets API access

Data is fetched via the [gspread](https://docs.gspread.org) library. You need to grant API access before running any `--fetch` commands.

**Recommended — service account** (no expiring tokens, no OAuth consent screen):
https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account

**Alternative — OAuth2:**
https://docs.gspread.org/en/latest/oauth2.html#enable-api-access-for-a-project

Once configured, share each `Spending-YYYY` spreadsheet with the service account email.

## Usage

### Make targets

| Command | Description |
|---|---|
| `make install` | Create venv, install deps, set up pre-commit hooks, build Webpack |
| `make run` | Load pickled data and regenerate HTML reports |
| `make fetch-latest` | Fetch the current year from Google Sheets and regenerate reports |
| `make fetch-all` | Fetch all years (2016–2026) with delays between requests |
| `make serve` | Serve `output/` via a local Python HTTP server |
| `make test` | Run unit tests |
| `make clean` | Remove venv and output directory |

### CLI flags

```bash
python main.py [--fetch] [--year YEAR] [--output-dir DIR] [--report-transactions] [--debug]
```

| Flag | Description |
|---|---|
| `--fetch` | Fetch from Google Sheets (requires `--year`) |
| `--year YEAR` | Target a specific year (2016–2026) |
| `--output-dir DIR` | Output directory (default: `output/`) |
| `--report-transactions` | Print a transaction table to the terminal |
| `--debug` | Enable debug-level logging |

**Examples:**
```bash
# Fetch a single year and regenerate reports
python main.py --fetch --year 2025

# Regenerate reports from existing pickles
python main.py

# Regenerate reports into a custom directory
python main.py --output-dir /tmp/finance-reports
```

## Data model

### Categories

| Name | Description |
|---|---|
| `INCOME` | Salary and other income |
| `SAVING` | Transfers to savings accounts |
| `MORTGAGE` | Mortgage payments |
| `BILLS` | Recurring monthly bills |
| `DONATION` | Charitable donations |
| `SHOPPING` | General retail shopping |
| `FOOD_AND_DRINK` | Groceries, cafes, restaurants, pubs |
| `TRANSPORT` | Car, fuel, public transport |
| `TRAVEL` | Holidays and travel |
| `HOUSE` | Home improvements and purchases |
| `CHILDREN` | Child-related expenses |
| `CASH` | Cash withdrawals |
| `TRANSFERS` | Inter-account transfers |
| `MISC` | Miscellaneous |

### Transaction types

Standard UK bank transaction codes: `BAC`, `BGC`, `CC`, `CHG`, `CHQ`, `DD`, `FP`, `FPI`, `FPO`, `ITF`, `ONL`, `POS`, `CASH` (ATM), `DCR`, `INT`, `CPT`, `COR`, `CBP`, `CHI`, `RFP`, `JNL`, `SO`, `UNKNOWN`.

## Spreadsheet format

Each year maps to a Google Sheet named `Spending-YYYY`. Three formats are supported:

**New format (2024+)** — one row per transaction:
| Date | Type | Category | Description | Amount | Note |

**Old format A (2018–2023)** — transactions grouped under category header rows:
| Date | Type | Description | Credit | Debit | Note |

**Old format B (2016–2017)** — transactions grouped under category header rows, no date column:
| Type | Description | Credit | Debit | Note | Date |

## Project structure

```
main.py                  # CLI, Google Sheets fetching, row parsing
finances/
  finances.py            # Data model: Transaction, Month, Year, Finances
  __init__.py            # Runtime type checking via beartype
templates/
  index.html             # Summary report template
  month.html             # Monthly transaction detail template
static/
  js/sorttable.js        # Client-side table sorting
output/                  # Generated reports (git-ignored)
  index.html
  transactions-M-YYYY.html
  bundle.js              # Webpack bundle (Bootstrap + Chart.js)
tests.py                 # Unit tests (faker-generated synthetic data)
webpack.config.js        # Webpack configuration
requirements.txt         # Python dependencies
```

## Dependencies

**Python:** `gspread`, `jinja2`, `python-dateutil`, `rich`, `tabulate`, `beartype`, `faker` (tests), `pre-commit`

**Frontend:** Bootstrap 5, Chart.js (bundled via Webpack)
