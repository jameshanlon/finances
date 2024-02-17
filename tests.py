import unittest
from faker import Faker
from finances.finances import (
    Transaction,
    TransactionType,
    Category,
    Month,
    Year,
    Finances,
)
import datetime
import tempfile
import shutil
from pathlib import Path


class FinanceTests(unittest.TestCase):
    """
    Unit tests for finances.
    """

    def setUp(self):
        self.faker = Faker("en_UK")
        self.output_path = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.output_path)

    def create_transaction(self, year: int, month: int):
        day = self.faker.pyint(min_value=1, max_value=28)
        date = datetime.date(year, month, day)
        transaction_type = self.faker.enum(TransactionType)
        category = self.faker.enum(Category)
        description = self.faker.text(30)
        amount = float(self.faker.pydecimal(left_digits=2, right_digits=2))
        note = self.faker.text(30)
        return Transaction(date, transaction_type, category, description, amount, note)

    def test_single_transaction(self):
        m = Month(1)
        m.transactions.append(self.create_transaction(2024, 1))
        y = Year(2024)
        y.months.append(m)
        f = Finances([])
        f.years.append(y)
        f.render_html(self.output_path)

    def test_many_transactions(self):
        MONTHS = range(1, 13)
        YEARS = range(2000, 2005)
        NUM_TRANSACTIONS = 100
        f = Finances([])
        for year in YEARS:
            y = Year(year)
            f.years.append(y)
            for month in MONTHS:
                m = Month(month)
                y.months.append(m)
                for i in range(NUM_TRANSACTIONS):
                    m.transactions.append(self.create_transaction(year, month))
        f.render_html(self.output_path)
        self.assertTrue((self.output_path / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
