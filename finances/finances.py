from collections import defaultdict
from dataclasses import dataclass
from dateutil import parser
from enum import Enum
from rich import print
from tabulate import tabulate
from typing import List, Dict
import datetime
import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

MONTHS_IN_YEAR = 12


class TransactionType(Enum):
    CASH = 11
    BAC = 1
    BGC = 15
    CBP = 18
    CC = 2
    CHARGE = 3
    CHI = 19
    CHEQUE = 14
    CORRECTION = 17
    CPT = 16
    DCR = 12
    DD = 4
    FP = 5
    FP_IN = 6
    FP_OUT = 7
    INTEREST = 13
    INTERNAL_TRANSFER = 8
    JNL = 21
    ONL = 9
    POS = 10
    RFP = 20
    UNKNOWN = 22

    @staticmethod
    def from_str(label):
        if label == "BAC":
            return TransactionType.BAC
        elif label == "CC":
            return TransactionType.CC
        elif label == "CHG" or label == "CHARGE":
            return TransactionType.CHARGE
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
            return TransactionType.FP_IN
        elif label == "FPO" or label == "FPOB" or label == "FASTER_PAYMENTS_OUTGOING":
            return TransactionType.FP_OUT
        elif label == "ITFIB" or label == "TRANSFER" or label == "TFR":
            return TransactionType.INTERNAL_TRANSFER
        elif label == "ONL":
            return TransactionType.ONL
        elif label == "POS" or label == "DEBIT_CARD":
            return TransactionType.POS
        elif label == "ATM" or label == "CSH" or label == "CPT" or label == "CASHPOINT":
            return TransactionType.CASH
        elif label == "DCR":
            return TransactionType.DCR
        elif label == "INT":
            return TransactionType.INTEREST
        elif label == "CHQ" or label == "CHEQUE":
            return TransactionType.CHEQUE
        elif label == "BGC":
            return TransactionType.BGC
        elif label == "CPT":
            return TransactionType.CPT
        elif label == "COR":
            return TransactionType.CORRECTION
        elif label == "CBP":
            return TransactionType.CBP
        elif label == "CHI":
            return TransactionType.CHI
        elif label == "RFP":
            return TransactionType.RFP
        elif label == "JNL":
            return TransactionType.JNL
        elif label == "UNKNOWN" or label == "":
            return TransactionType.UNKNOWN
        else:
            raise RuntimeError(f"unknown transaction type: {label}")

    def __str__(self):
        return str(self.value)


class UnknownCategory(Exception):
    pass


class Category(Enum):
    INCOME = 1
    SAVING = 2
    BILLS = 3
    DONATION = 4
    SHOPPING = 5
    FOOD_AND_DRINK = 6
    CASH = 7
    HOUSE = 8
    CHILDREN = 9
    TRANSPORT = 10
    MISC = 11
    TRANSFERS = 12

    @staticmethod
    def from_str(label):
        if label == "income" or label == "in":
            return Category.INCOME
        elif label.startswith("saving"):
            return Category.SAVING
        elif label == "bills" or label.startswith("monthly"):
            return Category.BILLS
        elif label == "donation" or label == "donations":
            return Category.DONATION
        elif label == "shopping":
            return Category.SHOPPING
        elif label == "food and drink" or label == "food, cafes, pub":
            return Category.FOOD_AND_DRINK
        elif label == "cash":
            return Category.CASH
        elif label == "house":
            return Category.HOUSE
        elif label == "children" or label == "baby":
            return Category.CHILDREN
        elif label == "transport" or label.startswith("car"):
            return Category.TRANSPORT
        elif label == "misc":
            return Category.MISC
        elif label == "transfers":
            return Category.TRANSFERS
        else:
            raise UnknownCategory(label)

    def __str__(self):
        return str(self.value)


@dataclass
class Transaction:
    """
    A class to represent a single transaction.
    """

    date: datetime.date
    transaction_type: TransactionType
    category: Category
    description: str
    amount: float
    note: str

    def __str__(self):
        return f"{self.date:%d-%m-%Y} {self.transaction_type} {self.category} {self.amount} {self.description} {self.note}"


class Month:
    """
    A class to hold a set of transations within one month.
    """

    index: int
    transactions: List[Transaction]

    def __init__(self, index: int):
        self.index = index
        self.transactions = []

    def num_transactions(self) -> int:
        return len(self.transactions)

    def report_transactions(self):
        headers = ["Date", "Type", "Category", "Description", "Amount", "Note"]
        table = []
        for transaction in self.transactions:
            table.append(
                [
                    f"{t.date:%d-%m-%Y}",
                    t.transaction_type.name,
                    t.category.name,
                    t.description,
                    t.amount,
                    t.note,
                ]
            )
        print()
        print(tabulate(table, headers, tablefmt="simple_outline"))

    def total_amount(self, category: Category) -> float:
        """
        Return the total amount in a given category of transaction.
        """
        return float(
            sum([x.amount for x in self.transactions if x.category == category])
        )

    def balance(self) -> float:
        """
        Return the balance of all transactions.
        """
        return float(sum(x.amount for x in self.transactions))


@dataclass
class Year:
    """
    A class to hold 12 months of transactions.
    """

    index: int
    months: List[Month]

    def __init__(self, index: int):
        self.index = index
        self.months = []

    def total_amount(self, category: Category) -> float:
        """
        Return the total amount in a given category of transaction.
        """
        return float(sum(x.total_amount(category) for x in self.months))

    def balance(self) -> float:
        """
        Return the balance of all transactions.
        """
        return float(sum(x.balance() for x in self.months))


@dataclass
class Finances:
    """
    A class to hold finance data.
    """

    years: List[Year]


class InvalidRow(Exception):
    pass


def read_oldest_worksheet(table, year_index: int, month_index: int) -> Month:
    """
    Read an old-format worksheet (2016, 2017) and return a Month.
    """
    month = Month(month_index + 1)
    category = None
    for i, row in enumerate(table[1:]):
        try:
            # Try and read a category label.
            category = Category.from_str(row[0].lower())
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
            transaction_type = TransactionType.from_str(row[0].upper())
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
                date = parser.parse(row[5])
            except (IndexError, parser._parser.ParserError) as e:
                date = datetime.datetime(year_index, month_index + 1, 1)
            # Create the transaction.
            t = Transaction(date, transaction_type, category, description, amount, note)
            # Append it to the month.
            month.transactions.append(t)
        except InvalidRow as e:
            logging.warning(f"Skipping row {i+1}: {', '.join(row)}")
    logging.info(f"Read {month.num_transactions()} transactions")
    return month


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


def read_old_worksheet(table, year_index: int, month_index: int) -> Month:
    """
    Read an old-format worksheet (2018-2023) and return a Month.
    """
    month = Month(month_index + 1)
    category = None
    for i, row in enumerate(table[1:]):
        try:
            # Try and read a category label.
            category = Category.from_str(row[0].lower())
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
            date = parser.parse(row[0])
            check_year(date, year_index, row)
            check_month(date, month_index, row)
            # Type
            transaction_type = TransactionType.from_str(row[1].upper())
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
        except (InvalidRow, parser._parser.ParserError) as e:
            logging.warning(f"Skipping row {i+1}: {', '.join(row)}")
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
            date = parser.parse(row[0])
            check_year(date, year_index, row)
            check_month(date, month_index, row)
            # Type
            transaction_type = TransactionType.from_str(row[1].upper())
            # Category
            category = Category.from_str(row[2].lower())
            # Description
            description = row[3]
            # Amount
            amount = float(row[4].replace("£", "").replace(",", ""))
            # Note
            note = row[5]
            t = Transaction(date, transaction_type, category, description, amount, note)
            # Append it to the month.
            month.transactions.append(t)
        except parser._parser.ParserError as e:
            logging.warning(f"Skipping row {i+1}: {', '.join(row)}")
    logging.info(f"Read {month.num_transactions()} transactions")
    return month


class MonthInYear(Enum):
    Jan = 1
    Feb = 2
    Mar = 3
    Apr = 4
    May = 5
    Jun = 6
    Jul = 7
    Aug = 8
    Sep = 9
    Oct = 10
    Nov = 11
    Dec = 12


def render_html(dataset: Finances, output_dir: Path):
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("index.html")
    content = template.render(months=MonthInYear, categories=Category, dataset=dataset)
    filename = output_dir / "index.html"
    # Summary
    with open(filename, mode="w", encoding="utf-8") as f:
        f.write(content)
        logging.info(f"Wrote {filename}")
    # Years
    for year in dataset.years:
        for month in year.months:
            template = environment.get_template("month.html")
            content = template.render(
                year=year.index,
                month=month.index,
                months=MonthInYear,
                categories=Category,
                dataset=month,
            )
            filename = output_dir / f"transactions-{month.index}-{year.index}.html"
            with open(filename, mode="w", encoding="utf-8") as f:
                f.write(content)
                logging.info(f"Wrote {filename}")
