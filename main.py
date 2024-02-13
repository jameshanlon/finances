import gspread
import argparse
from finances import finances
from rich import print
from dataclasses import dataclass
from typing import Any
import logging
import pickle
from pathlib import Path

"""
To do:
    - Skip 'Summary' and 'Template' sheet names.
"""

gc = gspread.service_account()


@dataclass
class Sheet:
    name: str
    reader: Any


sheets = {
    2016: Sheet("Spending-2016", finances.read_oldest_worksheet),
    2017: Sheet("Spending-2017", finances.read_oldest_worksheet),
    2018: Sheet("Spending-2018", finances.read_old_worksheet),
    2019: Sheet("Spending-2019", finances.read_old_worksheet),
    2020: Sheet("Spending-2020", finances.read_old_worksheet),
    2021: Sheet("Spending-2021", finances.read_old_worksheet),
    2022: Sheet("Spending-2022", finances.read_old_worksheet),
    2023: Sheet("Spending-2023", finances.read_old_worksheet),
    2024: Sheet("Spending-2024", finances.read_worksheet),
}


def fetch_month(sheet, year_index: int, month_index: int) -> finances.Month:
    """
    Fetch month data from a particular worksheet.
    """
    logging.info(f"Opening worksheet {month_index}")
    # Load
    worksheet = sheet.get_worksheet(month_index)
    values = worksheet.get_all_values()
    # Parse
    return sheets[year_index].reader(values, year_index, month_index)


def fetch_year(year_index: int, fetch: bool) -> finances.Year:
    """
    Fetch year date from Google Sheets.
    """
    filename = f"finances-{year_index}.pickle"
    sheet = gc.open(sheets[year_index].name)
    logging.info(
        f"Opening spreadsheet {sheets[year_index].name}, "
        f"last updated {sheet.get_lastUpdateTime()}"
    )
    worksheet_count = len(sheet.worksheets())
    year = finances.Year(year_index)
    for i in range(min(finances.MONTHS_IN_YEAR, worksheet_count)):
        year.months.append(fetch_month(sheet, year_index, i))
    # Pickle
    with open(filename, "wb") as f:
        pickle.dump(year, f, pickle.HIGHEST_PROTOCOL)
        logging.info(f"Wrote {filename}")
    return year


def load_year(year_index: int, fetch: bool) -> finances.Year:
    """
    Load a year from a pikcle file.
    """
    filename = f"finances-{year_index}.pickle"
    if not Path(filename).exists():
        logging.warning(f"Pickle file {filename} does not exist, skipping")
        return
    with open(filename, "rb") as f:
        year = pickle.load(f)
        logging.info(f"Read {filename}")
    return year


def main(args):

    if args.fetch:
        if not args.year:
            logging.error("Specify a year to fetch (--year)")
            return 1
        # Just fetch a particular year.
        fetch_year(args.year, args.fetch)
        return 0

    # Load pickled data.
    dataset = finances.Finances([load_year(x, args.fetch) for x in sheets.keys()])
    finances.render_html(dataset)
    return 0


if __name__ == "__main__":
    # Setup argument parsing.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fetch", action="store_true", help="Fetch data from Google Sheets"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        choices=range(2016, 2100),
        help="Report a particular year (from 2016)",
    )
    parser.add_argument(
        "--report-transactions",
        action="store_true",
        help="Display transactions in a table",
    )
    parser.add_argument("--debug", action="store_true", help="Print debugging messages")
    args = parser.parse_args()
    # Setup logging.
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    main(args)
