from collections import defaultdict
from dataclasses import dataclass
from dateutil import parser
from enum import Enum
from rich import print
from tabulate import tabulate
from typing import List, Dict
import datetime
import logging


class TransactionType(Enum):
    BAC = 1
    CC = 2
    CHG = 3
    DD = 4
    FP = 5
    FPI = 6
    FPO = 7
    ITFIB = 8
    ONL = 9
    POS = 10
    ATM = 11
    DCR = 12
    INT = 13
    CHQ = 14
    BGC = 15
    CPT = 16
    COR = 17
    CBP = 18
    CHI = 19
    RFP = 20
    JNL = 21
    UNKNOWN = 22

    @staticmethod
    def from_str(label):
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
            return TransactionType.ITFIB
        elif label == "ONL":
            return TransactionType.ONL
        elif label == "POS" or label == "DEBIT_CARD":
            return TransactionType.POS
        elif label == "ATM" or label == "CSH" or label == "CPT" or label == "CASHPOINT":
            return TransactionType.ATM
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
        elif label == "COR" or label == "CORRECTION":
            return TransactionType.COR
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
        elif label == "bills" or label.startswith("monthly bills"):
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
    transactions: Dict[Category, List[Transaction]]

    def __init__(self, index: int):
        self.index = index
        self.transactions = defaultdict(list)

    def num_transactions(self) -> int:
        return sum(len(v) for _, v in self.transactions.items())

    def report_transactions(self):
        headers = ["Date", "Type", "Category", "Description", "Amount", "Note"]
        table = []
        for category, transactions in self.transactions.items():
            for t in transactions:
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


@dataclass
class Year:
    """
    A class to hold 12 months of transactions.
    """

    months: List[Month]


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
            if row[0] == "" and row[1] == "":
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
            month.transactions[t.category].append(t)
        except InvalidRow as e:
            logging.debug(f"Skipping row {i+1}: {', '.join(row)}")
    logging.info(f"Read {month.num_transactions()} transactions")
    return month


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
            if row[0] == "" and row[1] == "":
                raise InvalidRow()
            # Parse the transaction.
            # Date
            date = parser.parse(row[0])
            assert (
                date.year == year_index
                or date.year == year_index - 1
                or date.year == year_index + 1
            )
            # assert (
            #    date.month == month_index + 1
            #    or date.month == 1 + (month_index - 1) % 12
            #    or date.month == 1 + (month_index + 1) % 12
            # )
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
            month.transactions[t.category].append(t)
        except (InvalidRow, parser._parser.ParserError) as e:
            logging.debug(f"Skipping row {i+1}: {', '.join(row)}")
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
            assert (
                date.year == year_index
                or date.year == year_index - 1
                or date.year == year_index + 1
            )
            # assert (
            #    date.month == month_index + 1
            #    or date.month == 1 + (month_index - 1) % 12
            #    or date.month == 1 + (month_index + 1) % 12
            # )
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
            month.transactions[t.category].append(t)
        except parser._parser.ParserError as e:
            logging.debug(f"Skipping row {i+1}: {', '.join(row)}")
    logging.info(f"Read {month.num_transactions()} transactions")
    return month
