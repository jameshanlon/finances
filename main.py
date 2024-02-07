import gspread
import argparse
from finances import finances
from rich import print
from dataclasses import dataclass
from typing import Any
import logging
import pickle
from pathlib import Path

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


def load_month(sheet, year_index: int, month_index: int) -> finances.Month:
    logging.info(f"Opening worksheet {month_index}")
    # Load
    worksheet = sheet.get_worksheet(month_index)
    values = worksheet.get_all_values()
    # Parse
    return sheets[year_index].reader(values, year_index, month_index)


def load_year(year_index: int, fetch: bool) -> finances.Year:
    filename = f"finances-{year_index}.pickle"
    if fetch:
        sheet = gc.open(sheets[year_index].name)
        logging.info(
            f"Opening spreadsheet {sheets[year_index].name}, "
            f"last updated {sheet.get_lastUpdateTime()}"
        )
        worksheet_count = len(sheet.worksheets())
        year = finances.Year([])
        for i in range(min(finances.MONTHS_IN_YEAR, worksheet_count)):
            year.months.append(load_month(sheet, year_index, i))
        # Pickle
        with open(filename, "wb") as f:
            pickle.dump(year, f, pickle.HIGHEST_PROTOCOL)
            logging.info(f"Wrote {filename}")
        return year
    else:
        # Unpickle
        if not Path(filename).exists():
            raise RuntimeError(
                f"Pickle file {filename} does not exist, rerun with --fetch"
            )
        with open(filename, "rb") as f:
            year = pickle.load(f)
            logging.info(f"Read {filename}")
            return year


def main(args):

    if args.year:
        # Just inspect a particular year.
        year = load_year(args.year, args.fetch)
        if args.report_transactions:
            if args.month:
                year.months[args.month - 1].report_transactions()
            else:
                for month in year.months:
                    month.report_transactions()
    else:
        # All years.
        years = []
        for year in sheets.keys():
            years.append(load_year(year, args.fetch))


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
        "--month",
        type=int,
        default=None,
        choices=range(1, 12),
        help="Report a particular month (1-12)",
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
