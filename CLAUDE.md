# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install       # Create venv, install Python deps, set up pre-commit hooks, build with Vite
make run           # Generate data.json and copy dist/ to output/
make fetch-latest  # Fetch current year from Google Sheets and regenerate reports
make fetch-all     # Fetch all years (2016–2026) with delays between requests
make serve         # Serve generated reports via Python HTTP server
make test          # Run unit tests (python tests.py)
make clean         # Remove venv and output directory
```

`main.py` CLI flags: `--fetch`, `--year`, `--output-dir` (default: `output/`), `--report-transactions`.

## Architecture

**Data flow:** Google Sheets API → parse with gspread → store as `finances-YYYY.pickle` → load pickle → serialize to `data.json` → React + MUI SPA reads JSON at runtime and renders interactive reports.

**Core data model** (`finances/finances.py`):
- `Transaction` — single transaction (date, type, category, description, amount, note)
- `Month` — aggregates transactions for a month
- `Year` — aggregates 12 months
- `Finances` — top-level container; owns JSON serialization (`to_json()`)

**Key enums:** `TransactionType` (23 bank transaction codes: BAC, CC, DD, POS, etc.) and `Category` (14 categories: INCOME, SAVING, BILLS, MORTGAGE, FOOD_AND_DRINK, etc.).

**Google Sheets schemas:** Three formats depending on year — old format B (2016–2017), old format A (2018–2023), new format (2024+). Each year maps to a separate Google Sheet named `Spending-YYYY`.

**Frontend:** Vite builds React + MUI into `dist/`, copied to `output/` by `make run`. `data.json` is written to `output/` by Python and fetched at runtime by the React SPA.

**Tests** (`tests.py`): Uses `unittest` + `faker` to generate synthetic transactions and verify `data.json` output. No external services required for tests.
