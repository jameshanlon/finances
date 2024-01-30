from collections import defaultdict
from dataclasses import dataclass
from dateutil import parser
from enum import Enum
from rich import print
from tabulate import tabulate
from typing import List, Dict
import datetime


class TransactionType(Enum):
    BAC = 1
    CC = 2
    CHG = 3
    DD = 4
    FP = 5
    FPIB = 6
    ITFIB = 7
    ONL = 8
    POS = 9

    @staticmethod
    def from_str(label):
        if label == "BAC":
            return TransactionType.BAC
        elif label == "CC":
            return TransactionType.CC
        elif label == "CHG":
            return TransactionType.CHG
        elif label == "DD":
            return TransactionType.DD
        elif label == "FP":
            return TransactionType.FP
        elif label == "FPIB":
            return TransactionType.FPIB
        elif label == "ITFIB":
            return TransactionType.ITFIB
        elif label == "ONL":
            return TransactionType.ONL
        elif label == "POS":
            return TransactionType.POS
        else:
            raise runtime_error(f"unknown transaction type: {label}")

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
        elif label == "saving" or label == "saving deposit":
            return Category.SAVING
        elif label == "bills" or label == "monthly bills":
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
        elif label == "children":
            return Category.CHILDREN
        elif label == "transport" or label == "car":
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

    transactions: Dict[Category, List[Transaction]]

    def __init__(self):
        self.transactions = defaultdict(list)

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
        print(tabulate(table, headers, tablefmt="simple_outline"))


@dataclass
class Year:
    """
    A class to hold 12 months of transactions.
    """

    months: List[Month]


def read_old_worksheet(table) -> Month:
    """
    Read an old-format worksheet and return a Month.
    """
    month = Month()
    category = None
    for i, row in enumerate(table[1:]):
        try:
            # Try and read a category label.
            category = Category.from_str(row[0])
            print(f"Category set to {category.name}")
        except UnknownCategory:
            pass
        try:
            # Parse the transaction.
            date = parser.parse(row[0])
            transaction_type = TransactionType.from_str(row[1].upper())
            description = row[2]
            if len(row[3]):
                amount = float(row[3].replace("£", "").replace(",", ""))
            elif len(row[4]):
                amount = -float(row[4].replace("£", "").replace(",", ""))
            else:
                amount = None
            note = row[5]
            t = Transaction(date, transaction_type, category, description, amount, note)
            # Append it to the month.
            month.transactions[t.category].append(t)
        except parser._parser.ParserError as e:
            print(f"Skipping row {i+1}: {row}")
    return month


def read_worksheet(table) -> Month:
    """
    Read a new-format worksheet and return a Month.
    """
    month = Month()
    assert table[0] == ["Date", "Type", "Category", "Description", "Amount", "Note"]
    for i, row in enumerate(table[1:]):
        try:
            # Parse the transaction.
            date = parser.parse(row[0])
            transaction_type = TransactionType.from_str(row[1].upper())
            category = Category.from_str(row[2].lower())
            description = row[3]
            amount = float(row[4].replace("£", "").replace(",", ""))
            note = row[5]
            t = Transaction(date, transaction_type, category, description, amount, note)
            # Append it to the month.
            month.transactions[t.category].append(t)
        except parser._parser.ParserError as e:
            print(f"Skipping row {i+1}: {row}")
    return month
