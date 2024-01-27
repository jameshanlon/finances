from collections import defaultdict
from dataclasses import dataclass
from dateutil import parser
from enum import Enum
from rich import print
from typing import List, Dict
import datetime
import tabulate

class TransactionType(Enum):
    CC = 1
    DD = 2
    CHG = 3
    FP = 4
    BAC = 5
    FPIB = 6
    ITFIB = 7
    ONL = 8
    POS = 9

    def __str__(self):
        return str(self.value)


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
        if label.lower() == 'income':
            return Category.INCOME
        elif label.lower() == 'saving':
            return Category.SAVING
        elif label.lower() == 'bills':
            return Category.BILLS
        elif label.lower() == 'donation':
            return Category.DONATION
        elif label.lower() == 'shopping':
            return Category.SHOPPING
        elif label.lower() == 'food and drink':
            return Category.FOOD_AND_DRINK
        elif label.lower() == 'cash':
            return Category.CASH
        elif label.lower() == 'house':
            return Category.HOUSE
        elif label.lower() == 'children':
            return Category.CHILDREN
        elif label.lower() == 'transport':
            return Category.TRANSPORT
        elif label.lower() == 'misc':
            return Category.MISC
        elif label.lower() == 'transfers':
            return Category.TRANSFERS
        else:
            return NotImplementedError

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

    def report(self):
        for category, transactions in self.transactions.items():
            for transaction in transactions:
                print(str(transaction))

@dataclass
class Year:
    """
    A class to hold 12 months of transactions.
    """
    months: List[Month]

def read_worksheet(table) -> Month:
    month = Month()
    assert table[0] == ["Date", "Type", "Category", "Description", "Amount", "Note"]
    for row in table[1:]:
        # Create the transaction object.
        date = parser.parse(row[0])
        transaction_type = TransactionType[row[1].upper()]
        category = Category.from_str(row[2])
        description = row[3]
        amount = float(row[4].replace("£", "").replace(",", ""))
        note = row[5]
        t = Transaction(date, transaction_type, category, description, amount, note)
        # Append it to the month.
        month.transactions[t.category].append(t)
    return month


