from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from rich import print
from tabulate import tabulate
from typing import List, Dict
import datetime
import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import shutil

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
    TRAVEL = 13

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

    def average_amount(self, category: Category) -> float:
        """
        Return the total amount in a given category of transaction.
        """
        return self.total_amount(category) / len(self.months)

    def balance(self) -> float:
        """
        Return the balance of all transactions.
        """
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
    """
    A class to hold finance data.
    """

    years: List[Year]

    DIRS = ["static"]
    FILES = ["output/bundle.js"]

    def create_html_report(self, output_dir: Path):
        self.render_html(output_dir)
        self.copy_web_dirs(output_dir)
        self.copy_web_files(output_dir)

    def render_html(self, output_dir: Path):
        environment = Environment(loader=FileSystemLoader("templates/"))
        template = environment.get_template("index.html")
        content = template.render(months=MonthInYear, categories=Category, dataset=self)
        filename = output_dir / "index.html"
        # Summary
        with open(filename, mode="w", encoding="utf-8") as f:
            f.write(content)
            logging.info(f"Wrote {filename}")
        # Years
        for year in self.years:
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

    def copy_web_dirs(self, output_dir: Path):
        """
        Copy directories into the output directory.
        """
        for d in self.DIRS:
            src_path = Path(d)
            if not src_path.exists():
                raise RuntimeError(f"Directory {d} does not exist")
            dst_path = output_dir / src_path
            if src_path != dst_path:
                shutil.copytree(src_path, output_dir, dirs_exist_ok=True)
                logging.info(f"Copied {src_path} to {dst_path}")

    def copy_web_files(self, output_dir: Path):
        """
        Copy files into the output directory.
        """
        for f in self.FILES:
            src_path = Path(f)
            if not src_path.exists():
                raise RuntimeError(f"File {f} does not exist")
            dst_path = output_dir / src_path.name
            if src_path != dst_path:
                shutil.copyfile(src_path, dst_path)
                logging.info(f"Copied {src_path} to {dst_path}")
