import gspread
import argparse
from finances.finances import (
    MONTHS_IN_YEAR,
    Category,
    Finances,
    Month,
    Transaction,
    TransactionType,
    Year,
)
from rich import print
from dataclasses import dataclass
from typing import Any
import logging
import pickle
from pathlib import Path
import datetime
from dateutil import parser as dateparser

"""
Finances command-line interface and integration with Google Sheets.
"""

gc = gspread.service_account()


@dataclass
class Sheet:
    name: str
    reader: Any


class InvalidRow(Exception):
    pass


class UnknownCategory(Exception):
    pass


class UnknownTransactionType(Exception):
    pass


def category_from_str(label: str) -> Category:
    if label == "income" or label == "in":
        return Category.INCOME
    elif label.startswith("saving"):
        return Category.SAVING
    elif label == "bills" or label.startswith("monthly"):
        return Category.BILLS
    elif label == "mortgage":
        return Category.MORTGAGE
    elif label == "donation" or label == "donations":
        return Category.DONATION
    elif label == "shopping":
        return Category.SHOPPING
    elif label == "food and drink" or label == "food, cafes, pub" or label == "pub":
        return Category.FOOD_AND_DRINK
    elif label == "cash":
        return Category.CASH
    elif label == "house":
        return Category.HOUSE
    elif label == "children" or label == "baby":
        return Category.CHILDREN
    elif label == "transport" or label.startswith("car"):
        return Category.TRANSPORT
    elif label == "travel" or label == "holiday":
        return Category.TRAVEL
    elif label == "misc":
        return Category.MISC
    elif label == "transfers":
        return Category.TRANSFERS
    else:
        raise UnknownCategory(label)


def transaction_type_from_str(label: str) -> TransactionType:
    if label == "BAC":
        return TransactionType.BAC
    elif label == "CC":
        return TransactionType.CC
    elif label == "CHG" or label == "CHARGE":
        return TransactionType.CHG
    elif label == "DD" or label == "DEB" or label == "DIRECT_DEBIT":
        return TransactionType.DD
    elif label == "FP" or label == "PAY" or label == "BANK_GIRO_CREDIT":
        return TransactionType.FP
    elif (
        label == "FPI"
        or label == "FPIB"
        or label == "DEP"
        or label == "FASTER_PAYMENTS_INCOMING"
    ):
        return TransactionType.FPI
    elif label == "FPO" or label == "FPOB" or label == "FASTER_PAYMENTS_OUTGOING":
        return TransactionType.FPO
    elif label == "ITFIB" or label == "TRANSFER" or label == "TFR":
        return TransactionType.ITF
    elif label == "ONL":
        return TransactionType.ONL
    elif label == "POS" or label == "DEBIT_CARD":
        return TransactionType.POS
    elif label == "ATM" or label == "CSH" or label == "CPT" or label == "CASHPOINT":
        return TransactionType.CASH
    elif label == "DCR":
        return TransactionType.DCR
    elif label == "INT":
        return TransactionType.INT
    elif label == "CHQ" or label == "CHEQUE":
        return TransactionType.CHQ
    elif label == "BGC":
        return TransactionType.BGC
    elif label == "CPT":
        return TransactionType.CPT
    elif label == "COR":
        return TransactionType.COR
    elif label == "CBP":
        return TransactionType.CBP
    elif label == "CHI":
        return TransactionType.CHI
    elif label == "RFP":
        return TransactionType.RFP
    elif label == "JNL":
        return TransactionType.JNL
    elif label == "SO":
        return TransactionType.SO
    elif label == "UNKNOWN" or label == "":
        return TransactionType.UNKNOWN
    else:
        raise UnknownTransactionType(f"unknown transaction type: {label}")


def check_year(date: datetime.datetime, year_index: int, row):
    if not (
        date.year == year_index
        or date.year == year_index - 1
        or date.year == year_index + 1
    ):
        logging.error(f"Date year ({date}) is out of range for {year_index}")
        logging.info(f"Row: {', '.join(row)}")


def check_month(date: datetime.datetime, month_index: int, row):
    if not (
        date.month == month_index + 1
        or date.month == 1 + (month_index - 1) % 12
        or date.month == 1 + (month_index + 1) % 12
    ):
        logging.error(f"Date month ({date}) is out of range for {month_index}")
        logging.info(f"Row: {', '.join(row)}")


def read_old_worksheet_b(table, year_index: int, month_index: int) -> Month:
    """
    Read an old-format worksheet (2016, 2017) and return a Month.
    """
    month = Month(month_index + 1)
    category = None
    for i, row in enumerate(table[1:]):
        try:
            # Try and read a category label.
            category = category_from_str(row[0].lower())
            logging.debug(f"Category set to {category.name}")
            continue
        except UnknownCategory:
            pass
        try:
            if category == None:
                raise InvalidRow()
            if row[0] == "":
                raise InvalidRow()
            # Parse the transaction.
            transaction_type = transaction_type_from_str(row[0].upper())
            description = row[1]
            if len(row[2]):
                amount = float(
                    row[2].replace("£", "").replace(",", "").replace("CR", "")
                )
            elif len(row[3]):
                amount = -float(
                    row[3].replace("£", "").replace(",", "").replace("CR", "")
                )
            else:
                amount = None
            note = row[4]
            # Try and parse the date if it's there.
            try:
                date = dateparser.parse(row[5])
            except (IndexError, dateparser._parser.ParserError) as e:
                date = datetime.datetime(year_index, month_index + 1, 1)
            # Create the transaction.
            t = Transaction(date, transaction_type, category, description, amount, note)
            # Append it to the month.
            month.transactions.append(t)
        except InvalidRow as e:
            logging.warning(f"Skipping row {i+1}: {', '.join(row)}")
        except UnknownTransactionType as e:
            logging.error(f"Unknown transaction type on row {i}: {row[2]}")
    logging.info(f"Read {month.num_transactions()} transactions")
    return month


def read_old_worksheet_a(table, year_index: int, month_index: int) -> Month:
    """
    Read an old-format worksheet (2018-2023) and return a Month.
    """
    month = Month(month_index + 1)
    category = None
    for i, row in enumerate(table[1:]):
        try:
            # Try and read a category label.
            category = category_from_str(row[0].lower())
            logging.debug(f"Category set to {category.name}")
            continue
        except UnknownCategory:
            pass
        try:
            if category == None:
                raise InvalidRow()
            if row[1] == "":
                raise InvalidRow()
            # Parse the transaction.
            # Date
            date = dateparser.parse(row[0])
            check_year(date, year_index, row)
            check_month(date, month_index, row)
            # Type
            transaction_type = transaction_type_from_str(row[1].upper())
            # Description
            description = row[2]
            # Amount
            if len(row[3]):
                amount = float(row[3].replace("£", "").replace(",", ""))
            elif len(row[4]):
                amount = -float(row[4].replace("£", "").replace(",", ""))
            else:
                amount = None
            # Note
            note = row[5]
            t = Transaction(date, transaction_type, category, description, amount, note)
            # Append it to the month.
            month.transactions.append(t)
        except (InvalidRow, dateparser._parser.ParserError) as e:
            logging.warning(f"Skipping row {i+1}: {', '.join(row)}")
        except UnknownTransactionType as e:
            logging.error(f"Unknown transaction type on row {i}: {row[2]}")
    logging.info(f"Read {month.num_transactions()} transactions")
    return month


def read_worksheet(table, year_index: int, month_index: int) -> Month:
    """
    Read a new-format worksheet and return a Month.
    """
    month = Month(month_index + 1)
    assert table[0] == ["Date", "Type", "Category", "Description", "Amount", "Note"]
    for i, row in enumerate(table[1:]):
        try:
            # Parse the transaction.
            # Date
            date = dateparser.parse(row[0])
            check_year(date, year_index, row)
            check_month(date, month_index, row)
            # Type
            transaction_type = transaction_type_from_str(row[1].upper())
            # Category
            category = category_from_str(row[2].lower())
            # Description
            description = row[3]
            # Amount
            amount = float(row[4].replace("£", "").replace(",", ""))
            # Note
            note = row[5]
            t = Transaction(date, transaction_type, category, description, amount, note)
            # Append it to the month.
            month.transactions.append(t)
        except dateparser._parser.ParserError as e:
            logging.warning(f"Skipping row {i+1}: {', '.join(row)}")
        except UnknownCategory as e:
            logging.error(f"Unknown category on row {i}: {row[2]}")
        except UnknownTransactionType as e:
            logging.error(f"Unknown transaction type on row {i}: {row[2]}")
    logging.info(f"Read {month.num_transactions()} transactions")
    return month


def fetch_month(sheet, year_index: int, month_index: int) -> Month:
    """
    Fetch month data from a particular worksheet.
    """
    logging.info(f"Opening worksheet {month_index}")
    # Load
    worksheet = sheet.get_worksheet(month_index)
    values = worksheet.get_all_values()
    # Parse
    return SHEETS[year_index].reader(values, year_index, month_index)


def fetch_year(year_index: int, fetch: bool, output_dir: Path) -> Year:
    """
    Fetch year date from Google Sheets.
    """
    filename = output_dir / f"finances-{year_index}.pickle"
    sheet = gc.open(SHEETS[year_index].name)
    logging.info(
        f"Opening spreadsheet {SHEETS[year_index].name}, "
        f"last updated {sheet.get_lastUpdateTime()}"
    )
    worksheet_count = len(sheet.worksheets())
    year = Year(year_index)
    for i in range(min(MONTHS_IN_YEAR, worksheet_count)):
        year.months.append(fetch_month(sheet, year_index, i))
    # Pickle
    with open(filename, "wb") as f:
        pickle.dump(year, f, pickle.HIGHEST_PROTOCOL)
        logging.info(f"Wrote {filename}")
    return year


def load_year(year_index: int, fetch: bool, output_dir: Path) -> Year:
    """
    Load a year from a pikcle file.
    """
    filename = output_dir / f"finances-{year_index}.pickle"
    if not Path(filename).exists():
        logging.warning(f"Pickle file {filename} does not exist, skipping")
        return Year(year_index)
    with open(filename, "rb") as f:
        year = pickle.load(f)
        logging.info(f"Read {filename}")
    return year


SHEETS = {
    2016: Sheet("Spending-2016", read_old_worksheet_b),
    2017: Sheet("Spending-2017", read_old_worksheet_b),
    2018: Sheet("Spending-2018", read_old_worksheet_a),
    2019: Sheet("Spending-2019", read_old_worksheet_a),
    2020: Sheet("Spending-2020", read_old_worksheet_a),
    2021: Sheet("Spending-2021", read_old_worksheet_a),
    2022: Sheet("Spending-2022", read_old_worksheet_a),
    2023: Sheet("Spending-2023", read_old_worksheet_a),
    2024: Sheet("Spending-2024", read_worksheet),
}


def main(args):

    # Output path.
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    if args.fetch:
        if not args.year:
            raise RuntimeError("Specify a year to fetch (--year)")

        # Just fetch a particular year.
        fetch_year(args.year, args.fetch, output_path)
        return

    # Load pickled data.
    dataset = Finances([load_year(x, args.fetch, output_path) for x in SHEETS.keys()])

    # Render the HTML.
    dataset.create_html_report(output_path)


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
        "--output-dir",
        default="output",
        help="Specify an output directory (default: 'output')",
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
