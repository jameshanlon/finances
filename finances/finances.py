from dataclasses import dataclass
from enum import Enum
from rich import print
from tabulate import tabulate
from typing import List
import datetime
import json
import logging
from pathlib import Path

MONTHS_IN_YEAR = 12


class TransactionType(Enum):
    BAC = 1
    BGC = 15
    CASH = 11
    CBP = 18
    CC = 2
    CHG = 3
    CHI = 19
    CHQ = 14
    COR = 17
    CPT = 16
    DCR = 12
    DD = 4
    FP = 5
    FPI = 6
    FPO = 7
    INT = 13
    ITF = 8
    JNL = 21
    ONL = 9
    POS = 10
    RFP = 20
    UNKNOWN = 22
    SO = 23

    def __str__(self):
        return str(self.value)


class Category(Enum):
    INCOME = 1
    TRANSFERS = 2
    SAVING = 3
    BILLS = 4
    DONATION = 5
    SHOPPING = 6
    FOOD_AND_DRINK = 7
    CASH = 8
    HOUSE = 9
    CHILDREN = 10
    TRANSPORT = 11
    TRAVEL = 12
    MISC = 13
    MORTGAGE = 14

    def __str__(self):
        return str(self.value)


@dataclass
class Transaction:
    date: datetime.date
    transaction_type: TransactionType
    category: Category
    description: str
    amount: float
    note: str

    def __str__(self):
        return f"{self.date:%d-%m-%Y} {self.transaction_type} {self.category} {self.amount} {self.description} {self.note}"


class Month:
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
                    f"{transaction.date:%d-%m-%Y}",
                    transaction.transaction_type.name,
                    transaction.category.name,
                    transaction.description,
                    transaction.amount,
                    transaction.note,
                ]
            )
        print()
        print(tabulate(table, headers, tablefmt="simple_outline"))

    def total_amount(self, category: Category) -> float:
        return float(
            sum([x.amount for x in self.transactions if x.category == category])
        )

    def balance(self) -> float:
        return float(sum(x.amount for x in self.transactions))


@dataclass
class Year:
    index: int
    months: List[Month]

    def __init__(self, index: int):
        self.index = index
        self.months = []

    def total_amount(self, category: Category) -> float:
        return float(sum(x.total_amount(category) for x in self.months))

    def average_amount(self, category: Category) -> float:
        if len(self.months) == 0:
            return 0.0
        return self.total_amount(category) / len(self.months)

    def balance(self) -> float:
        return float(sum(x.balance() for x in self.months))


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


@dataclass
class Finances:
    years: List[Year]

    def to_json(self, output_dir: Path):
        data = {
            "categories": [c.name for c in Category],
            "years": [
                {
                    "index": year.index,
                    "months": [
                        {
                            "index": month.index,
                            "transactions": [
                                {
                                    "date": t.date.isoformat(),
                                    "type": t.transaction_type.name,
                                    "category": t.category.name,
                                    "description": t.description,
                                    "amount": t.amount,
                                    "note": t.note,
                                }
                                for t in month.transactions
                            ],
                        }
                        for month in year.months
                    ],
                }
                for year in self.years
            ],
        }
        filename = output_dir / "data.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f)
        logging.info(f"Wrote {filename}")
