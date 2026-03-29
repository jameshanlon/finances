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
from main import (
    category_from_str,
    transaction_type_from_str,
    UnknownCategory,
    UnknownTransactionType,
)
import datetime
import tempfile
import shutil
from pathlib import Path


def make_transaction(
    category: Category, amount: float, year=2024, month=1
) -> Transaction:
    return Transaction(
        date=datetime.date(year, month, 1),
        transaction_type=TransactionType.FPI,
        category=category,
        description="test",
        amount=amount,
        note="",
    )


class TestMonth(unittest.TestCase):
    def test_balance_empty(self):
        self.assertEqual(Month(1).balance(), 0.0)

    def test_balance(self):
        m = Month(1)
        m.transactions = [
            make_transaction(Category.INCOME, 1000.0),
            make_transaction(Category.BILLS, -200.0),
            make_transaction(Category.FOOD_AND_DRINK, -50.0),
        ]
        self.assertAlmostEqual(m.balance(), 750.0)

    def test_total_amount_filters_by_category(self):
        m = Month(1)
        m.transactions = [
            make_transaction(Category.INCOME, 1000.0),
            make_transaction(Category.BILLS, -200.0),
            make_transaction(Category.BILLS, -100.0),
        ]
        self.assertAlmostEqual(m.total_amount(Category.BILLS), -300.0)
        self.assertAlmostEqual(m.total_amount(Category.INCOME), 1000.0)
        self.assertAlmostEqual(m.total_amount(Category.FOOD_AND_DRINK), 0.0)

    def test_num_transactions(self):
        m = Month(1)
        self.assertEqual(m.num_transactions(), 0)
        m.transactions.append(make_transaction(Category.MISC, 10.0))
        self.assertEqual(m.num_transactions(), 1)


class TestYear(unittest.TestCase):
    def _make_year(self) -> Year:
        y = Year(2024)
        for month_num in range(1, 4):
            m = Month(month_num)
            m.transactions = [
                make_transaction(Category.INCOME, 1000.0, month=month_num),
                make_transaction(Category.BILLS, -200.0, month=month_num),
            ]
            y.months.append(m)
        return y

    def test_total_amount(self):
        y = self._make_year()
        self.assertAlmostEqual(y.total_amount(Category.INCOME), 3000.0)
        self.assertAlmostEqual(y.total_amount(Category.BILLS), -600.0)

    def test_average_amount(self):
        y = self._make_year()
        self.assertAlmostEqual(y.average_amount(Category.INCOME), 1000.0)
        self.assertAlmostEqual(y.average_amount(Category.BILLS), -200.0)

    def test_average_amount_empty_year(self):
        self.assertEqual(Year(2024).average_amount(Category.INCOME), 0.0)

    def test_balance(self):
        y = self._make_year()
        self.assertAlmostEqual(y.balance(), 2400.0)  # 3 * (1000 - 200)


class TestCategoryFromStr(unittest.TestCase):
    def test_canonical_names(self):
        cases = [
            ("income", Category.INCOME),
            ("saving", Category.SAVING),
            ("savings", Category.SAVING),
            ("bills", Category.BILLS),
            ("mortgage", Category.MORTGAGE),
            ("donation", Category.DONATION),
            ("donations", Category.DONATION),
            ("shopping", Category.SHOPPING),
            ("food and drink", Category.FOOD_AND_DRINK),
            ("cash", Category.CASH),
            ("house", Category.HOUSE),
            ("children", Category.CHILDREN),
            ("transport", Category.TRANSPORT),
            ("travel", Category.TRAVEL),
            ("misc", Category.MISC),
            ("transfers", Category.TRANSFERS),
        ]
        for label, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(category_from_str(label), expected)

    def test_aliases(self):
        self.assertEqual(category_from_str("in"), Category.INCOME)
        self.assertEqual(category_from_str("baby"), Category.CHILDREN)
        self.assertEqual(category_from_str("holiday"), Category.TRAVEL)
        self.assertEqual(category_from_str("pub"), Category.FOOD_AND_DRINK)
        self.assertEqual(category_from_str("food, cafes, pub"), Category.FOOD_AND_DRINK)
        self.assertEqual(category_from_str("monthly bills"), Category.BILLS)
        self.assertEqual(category_from_str("car insurance"), Category.TRANSPORT)

    def test_unknown_raises(self):
        with self.assertRaises(UnknownCategory):
            category_from_str("not a category")


class TestTransactionTypeFromStr(unittest.TestCase):
    def test_canonical_codes(self):
        cases = [
            ("BAC", TransactionType.BAC),
            ("CC", TransactionType.CC),
            ("DD", TransactionType.DD),
            ("FP", TransactionType.FP),
            ("FPI", TransactionType.FPI),
            ("FPO", TransactionType.FPO),
            ("ONL", TransactionType.ONL),
            ("POS", TransactionType.POS),
            ("DCR", TransactionType.DCR),
            ("INT", TransactionType.INT),
            ("CHQ", TransactionType.CHQ),
            ("BGC", TransactionType.BGC),
            ("CPT", TransactionType.CPT),
            ("COR", TransactionType.COR),
            ("CBP", TransactionType.CBP),
            ("CHI", TransactionType.CHI),
            ("RFP", TransactionType.RFP),
            ("JNL", TransactionType.JNL),
            ("SO", TransactionType.SO),
            ("UNKNOWN", TransactionType.UNKNOWN),
            ("", TransactionType.UNKNOWN),
        ]
        for label, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(transaction_type_from_str(label), expected)

    def test_aliases(self):
        self.assertEqual(transaction_type_from_str("CHARGE"), TransactionType.CHG)
        self.assertEqual(transaction_type_from_str("DEB"), TransactionType.DD)
        self.assertEqual(transaction_type_from_str("DIRECT_DEBIT"), TransactionType.DD)
        self.assertEqual(transaction_type_from_str("PAY"), TransactionType.FP)
        self.assertEqual(
            transaction_type_from_str("BANK_GIRO_CREDIT"), TransactionType.FP
        )
        self.assertEqual(transaction_type_from_str("FPIB"), TransactionType.FPI)
        self.assertEqual(transaction_type_from_str("DEP"), TransactionType.FPI)
        self.assertEqual(
            transaction_type_from_str("FASTER_PAYMENTS_INCOMING"), TransactionType.FPI
        )
        self.assertEqual(transaction_type_from_str("FPOB"), TransactionType.FPO)
        self.assertEqual(
            transaction_type_from_str("FASTER_PAYMENTS_OUTGOING"), TransactionType.FPO
        )
        self.assertEqual(transaction_type_from_str("ITFIB"), TransactionType.ITF)
        self.assertEqual(transaction_type_from_str("TRANSFER"), TransactionType.ITF)
        self.assertEqual(transaction_type_from_str("TFR"), TransactionType.ITF)
        self.assertEqual(transaction_type_from_str("DEBIT_CARD"), TransactionType.POS)
        self.assertEqual(transaction_type_from_str("ATM"), TransactionType.CASH)
        self.assertEqual(transaction_type_from_str("CSH"), TransactionType.CASH)
        self.assertEqual(transaction_type_from_str("CASHPOINT"), TransactionType.CASH)
        self.assertEqual(transaction_type_from_str("CHEQUE"), TransactionType.CHQ)

    def test_unknown_raises(self):
        with self.assertRaises(UnknownTransactionType):
            transaction_type_from_str("NOTACODE")


class TestHtmlRendering(unittest.TestCase):
    def setUp(self):
        self.faker = Faker("en_UK")
        self.output_path = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.output_path)

    def create_transaction(self, year: int, month: int) -> Transaction:
        return Transaction(
            date=datetime.date(
                year, month, self.faker.pyint(min_value=1, max_value=28)
            ),
            transaction_type=self.faker.enum(TransactionType),
            category=self.faker.enum(Category),
            description=self.faker.text(30),
            amount=float(self.faker.pydecimal(left_digits=2, right_digits=2)),
            note=self.faker.text(30),
        )

    def test_renders_index_and_month_pages(self):
        m = Month(1)
        m.transactions.append(self.create_transaction(2024, 1))
        f = Finances([Year(2024)])
        f.years[0].months.append(m)
        f.render_html(self.output_path)
        self.assertTrue((self.output_path / "index.html").exists())
        self.assertTrue((self.output_path / "transactions-1-2024.html").exists())

    def test_many_transactions(self):
        YEARS = range(2000, 2005)
        f = Finances([])
        for year in YEARS:
            y = Year(year)
            f.years.append(y)
            for month_num in range(1, 13):
                m = Month(month_num)
                y.months.append(m)
                for _ in range(100):
                    m.transactions.append(self.create_transaction(year, month_num))
        f.render_html(self.output_path)
        self.assertTrue((self.output_path / "index.html").exists())
        for year in YEARS:
            for month_num in range(1, 13):
                self.assertTrue(
                    (
                        self.output_path / f"transactions-{month_num}-{year}.html"
                    ).exists()
                )

    def test_empty_finances_renders(self):
        Finances([]).render_html(self.output_path)
        self.assertTrue((self.output_path / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
