import sys
from unittest.mock import MagicMock

# Must mock gspread before importing main (it calls gspread.service_account() at module level)
sys.modules["gspread"] = MagicMock()

import datetime
import pickle
import shutil
import tempfile
import unittest
from pathlib import Path

from faker import Faker

from finances.finances import (
    Category,
    Finances,
    Month,
    Transaction,
    TransactionType,
    Year,
)
from main import (
    UnknownCategory,
    UnknownTransactionType,
    category_from_str,
    check_month,
    check_year,
    load_year,
    read_old_worksheet_a,
    read_old_worksheet_b,
    read_worksheet,
    transaction_type_from_str,
)


class FinanceTests(unittest.TestCase):
    """Tests for the finances.finances module."""

    def setUp(self):
        self.faker = Faker("en_UK")
        self.output_path = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.output_path)

    def make_transaction(self, year=2024, month=1, category=Category.INCOME, amount=100.0):
        return Transaction(
            date=datetime.date(year, month, 15),
            transaction_type=TransactionType.FPI,
            category=category,
            description="test",
            amount=amount,
            note="",
        )

    def create_transaction(self, year: int, month: int):
        day = self.faker.pyint(min_value=1, max_value=28)
        date = datetime.date(year, month, day)
        transaction_type = self.faker.enum(TransactionType)
        category = self.faker.enum(Category)
        description = self.faker.text(30)
        amount = float(self.faker.pydecimal(left_digits=2, right_digits=2))
        note = self.faker.text(30)
        return Transaction(date, transaction_type, category, description, amount, note)

    # --- Existing smoke tests ---

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

    # --- Month tests ---

    def test_month_num_transactions(self):
        m = Month(1)
        self.assertEqual(m.num_transactions(), 0)
        m.transactions.append(self.make_transaction())
        self.assertEqual(m.num_transactions(), 1)
        m.transactions.append(self.make_transaction())
        self.assertEqual(m.num_transactions(), 2)

    def test_month_total_amount(self):
        m = Month(1)
        m.transactions.append(self.make_transaction(category=Category.FOOD_AND_DRINK, amount=10.0))
        m.transactions.append(self.make_transaction(category=Category.FOOD_AND_DRINK, amount=5.50))
        m.transactions.append(self.make_transaction(category=Category.BILLS, amount=100.0))
        self.assertAlmostEqual(m.total_amount(Category.FOOD_AND_DRINK), 15.50)
        self.assertAlmostEqual(m.total_amount(Category.BILLS), 100.0)
        self.assertAlmostEqual(m.total_amount(Category.SHOPPING), 0.0)

    def test_month_total_amount_empty(self):
        self.assertAlmostEqual(Month(1).total_amount(Category.INCOME), 0.0)

    def test_month_balance(self):
        m = Month(1)
        m.transactions.append(self.make_transaction(amount=500.0))
        m.transactions.append(self.make_transaction(amount=-200.0))
        self.assertAlmostEqual(m.balance(), 300.0)

    def test_month_balance_empty(self):
        self.assertAlmostEqual(Month(1).balance(), 0.0)

    def test_month_report_transactions(self):
        m = Month(1)
        m.transactions.append(self.make_transaction())
        m.report_transactions()  # Previously raised NameError due to 't' vs 'transaction'

    # --- Year tests ---

    def test_year_total_amount(self):
        y = Year(2024)
        for month_idx in range(1, 4):
            m = Month(month_idx)
            m.transactions.append(self.make_transaction(month=month_idx, category=Category.BILLS, amount=50.0))
            y.months.append(m)
        self.assertAlmostEqual(y.total_amount(Category.BILLS), 150.0)
        self.assertAlmostEqual(y.total_amount(Category.INCOME), 0.0)

    def test_year_average_amount(self):
        y = Year(2024)
        for month_idx in range(1, 5):  # 4 months, £100 each
            m = Month(month_idx)
            m.transactions.append(self.make_transaction(month=month_idx, category=Category.BILLS, amount=100.0))
            y.months.append(m)
        self.assertAlmostEqual(y.average_amount(Category.BILLS), 100.0)

    def test_year_average_amount_empty_year(self):
        self.assertAlmostEqual(Year(2024).average_amount(Category.BILLS), 0.0)

    def test_year_balance(self):
        y = Year(2024)
        m1 = Month(1)
        m1.transactions.append(self.make_transaction(amount=1000.0))
        m2 = Month(2)
        m2.transactions.append(self.make_transaction(amount=-300.0))
        y.months.extend([m1, m2])
        self.assertAlmostEqual(y.balance(), 700.0)


class CategoryParsingTests(unittest.TestCase):
    """Tests for category_from_str."""

    def test_all_known_labels(self):
        cases = [
            ("income", Category.INCOME),
            ("in", Category.INCOME),
            ("saving", Category.SAVING),
            ("savings", Category.SAVING),       # startswith "saving"
            ("bills", Category.BILLS),
            ("monthly bills", Category.BILLS),  # startswith "monthly"
            ("mortgage", Category.MORTGAGE),
            ("donation", Category.DONATION),
            ("donations", Category.DONATION),
            ("shopping", Category.SHOPPING),
            ("food and drink", Category.FOOD_AND_DRINK),
            ("food, cafes, pub", Category.FOOD_AND_DRINK),
            ("pub", Category.FOOD_AND_DRINK),
            ("cash", Category.CASH),
            ("house", Category.HOUSE),
            ("children", Category.CHILDREN),
            ("baby", Category.CHILDREN),
            ("transport", Category.TRANSPORT),
            ("car insurance", Category.TRANSPORT),  # startswith "car"
            ("travel", Category.TRAVEL),
            ("holiday", Category.TRAVEL),
            ("misc", Category.MISC),
            ("transfers", Category.TRANSFERS),
        ]
        for label, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(category_from_str(label), expected)

    def test_unknown_label_raises(self):
        with self.assertRaises(UnknownCategory):
            category_from_str("gibberish")


class TransactionTypeParsingTests(unittest.TestCase):
    """Tests for transaction_type_from_str."""

    def test_all_known_labels(self):
        cases = [
            ("BAC", TransactionType.BAC),
            ("CC", TransactionType.CC),
            ("CHG", TransactionType.CHG),
            ("CHARGE", TransactionType.CHG),
            ("DD", TransactionType.DD),
            ("DEB", TransactionType.DD),
            ("DIRECT_DEBIT", TransactionType.DD),
            ("FP", TransactionType.FP),
            ("PAY", TransactionType.FP),
            ("BANK_GIRO_CREDIT", TransactionType.FP),
            ("FPI", TransactionType.FPI),
            ("FPIB", TransactionType.FPI),
            ("DEP", TransactionType.FPI),
            ("FASTER_PAYMENTS_INCOMING", TransactionType.FPI),
            ("FPO", TransactionType.FPO),
            ("FPOB", TransactionType.FPO),
            ("FASTER_PAYMENTS_OUTGOING", TransactionType.FPO),
            ("ITFIB", TransactionType.ITF),
            ("TRANSFER", TransactionType.ITF),
            ("TFR", TransactionType.ITF),
            ("ONL", TransactionType.ONL),
            ("POS", TransactionType.POS),
            ("DEBIT_CARD", TransactionType.POS),
            ("ATM", TransactionType.CASH),
            ("CSH", TransactionType.CASH),
            ("CASHPOINT", TransactionType.CASH),
            ("CPT", TransactionType.CPT),  # distinct from CASH after bug fix
            ("DCR", TransactionType.DCR),
            ("INT", TransactionType.INT),
            ("CHQ", TransactionType.CHQ),
            ("CHEQUE", TransactionType.CHQ),
            ("BGC", TransactionType.BGC),
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

    def test_unknown_label_raises(self):
        with self.assertRaises(UnknownTransactionType):
            transaction_type_from_str("NOTATYPE")


class DateValidationTests(unittest.TestCase):
    """Tests for check_year and check_month."""

    def _row(self):
        return ["2024-01-01", "FPI", "income", "Salary", "1000.00", ""]

    def test_check_year_exact_match(self):
        check_year(datetime.datetime(2024, 6, 1), 2024, self._row())

    def test_check_year_one_below(self):
        # date.year == year_index - 1 is valid (e.g. Dec transaction in Jan sheet)
        check_year(datetime.datetime(2024, 12, 31), 2025, self._row())

    def test_check_year_one_above(self):
        # date.year == year_index + 1 is valid (e.g. Jan transaction in Dec sheet)
        check_year(datetime.datetime(2025, 1, 1), 2024, self._row())

    def test_check_year_out_of_range_logs_error(self):
        date = datetime.datetime(2020, 1, 1)
        with self.assertLogs(level="ERROR") as cm:
            check_year(date, 2024, self._row())
        self.assertTrue(any("out of range" in msg for msg in cm.output))

    def test_check_month_exact_match(self):
        # month_index=0 → expects month 1 (January)
        check_month(datetime.datetime(2024, 1, 15), 0, self._row())

    def test_check_month_adjacent_prev(self):
        # month_index=0 → previous month wraps to 12 (December)
        check_month(datetime.datetime(2024, 12, 31), 0, self._row())

    def test_check_month_adjacent_next(self):
        # month_index=0 → next month is 2 (February)
        check_month(datetime.datetime(2024, 2, 1), 0, self._row())

    def test_check_month_out_of_range_logs_error(self):
        # June is not adjacent to January (month_index=0)
        date = datetime.datetime(2024, 6, 15)
        with self.assertLogs(level="ERROR") as cm:
            check_month(date, 0, self._row())
        self.assertTrue(any("out of range" in msg for msg in cm.output))


class WorksheetParsingTests(unittest.TestCase):
    """Tests for read_worksheet, read_old_worksheet_a, and read_old_worksheet_b."""

    # --- read_worksheet (2024+ format) ---

    def test_read_worksheet_basic(self):
        table = [
            ["Date", "Type", "Category", "Description", "Amount", "Note"],
            ["01/01/2024", "FPI", "income", "Salary", "3000.00", ""],
            ["15/01/2024", "DD", "bills", "Electric", "-45.50", "monthly"],
        ]
        month = read_worksheet(table, 2024, 0)
        self.assertEqual(month.num_transactions(), 2)
        self.assertAlmostEqual(month.total_amount(Category.INCOME), 3000.0)
        self.assertAlmostEqual(month.total_amount(Category.BILLS), -45.50)

    def test_read_worksheet_strips_pound_and_commas(self):
        table = [
            ["Date", "Type", "Category", "Description", "Amount", "Note"],
            ["01/01/2024", "FPI", "income", "Salary", "£3,000.00", ""],
        ]
        month = read_worksheet(table, 2024, 0)
        self.assertAlmostEqual(month.total_amount(Category.INCOME), 3000.0)

    def test_read_worksheet_skips_bad_date_row(self):
        table = [
            ["Date", "Type", "Category", "Description", "Amount", "Note"],
            ["not-a-date", "FPI", "income", "Salary", "3000.00", ""],
            ["01/01/2024", "DD", "bills", "Electric", "45.50", ""],
        ]
        month = read_worksheet(table, 2024, 0)
        self.assertEqual(month.num_transactions(), 1)

    def test_read_worksheet_wrong_header_raises(self):
        table = [["Wrong", "Header", "Format", "", "", ""]]
        with self.assertRaises(AssertionError):
            read_worksheet(table, 2024, 0)

    def test_read_worksheet_correct_month_index(self):
        # month_index=5 → Month.index should be 6
        table = [["Date", "Type", "Category", "Description", "Amount", "Note"]]
        month = read_worksheet(table, 2024, 5)
        self.assertEqual(month.index, 6)

    # --- read_old_worksheet_a (2018-2023 format) ---

    def test_read_old_worksheet_a_basic(self):
        table = [
            [""],                                                      # header - skipped
            ["income", "", "", "", "", ""],                            # category row
            ["01/01/2020", "FPI", "Salary", "1000.00", "", ""],       # credit
            ["05/01/2020", "DD", "Electric", "", "50.00", ""],        # debit → negated
        ]
        month = read_old_worksheet_a(table, 2020, 0)
        self.assertEqual(month.num_transactions(), 2)
        self.assertAlmostEqual(month.balance(), 950.0)

    def test_read_old_worksheet_a_debit_is_negated(self):
        table = [
            [""],
            ["bills", "", "", "", "", ""],
            ["01/01/2020", "DD", "Electric", "", "100.00", ""],
        ]
        month = read_old_worksheet_a(table, 2020, 0)
        self.assertAlmostEqual(month.total_amount(Category.BILLS), -100.0)

    def test_read_old_worksheet_a_strips_pound_and_commas(self):
        table = [
            [""],
            ["income", "", "", "", "", ""],
            ["01/01/2020", "FPI", "Salary", "£5,000.00", "", ""],
        ]
        month = read_old_worksheet_a(table, 2020, 0)
        self.assertAlmostEqual(month.total_amount(Category.INCOME), 5000.0)

    def test_read_old_worksheet_a_skips_empty_type_row(self):
        table = [
            [""],
            ["income", "", "", "", "", ""],
            ["", "", "", "", "", ""],                             # empty type → InvalidRow
            ["01/01/2020", "FPI", "Salary", "1000.00", "", ""],
        ]
        month = read_old_worksheet_a(table, 2020, 0)
        self.assertEqual(month.num_transactions(), 1)

    def test_read_old_worksheet_a_skips_rows_before_category(self):
        # Transactions before any category row are skipped (category is None)
        table = [
            [""],
            ["01/01/2020", "FPI", "Salary", "1000.00", "", ""],  # no category yet → skipped
            ["income", "", "", "", "", ""],
            ["02/01/2020", "FPI", "Bonus", "500.00", "", ""],
        ]
        month = read_old_worksheet_a(table, 2020, 0)
        self.assertEqual(month.num_transactions(), 1)

    # --- read_old_worksheet_b (2016-2017 format) ---

    def test_read_old_worksheet_b_basic(self):
        table = [
            [""],                                                        # header - skipped
            ["income", "", "", "", "", ""],                              # category row
            ["FPI", "Salary", "1000.00", "", "note", "01/01/2016"],     # credit with date
            ["DD", "Bills", "", "50.00", "note2", ""],                  # debit → negated
        ]
        month = read_old_worksheet_b(table, 2016, 0)
        self.assertEqual(month.num_transactions(), 2)
        self.assertAlmostEqual(month.balance(), 950.0)

    def test_read_old_worksheet_b_debit_is_negated(self):
        table = [
            [""],
            ["bills", "", "", "", "", ""],
            ["DD", "Electric", "", "100.00", "", ""],
        ]
        month = read_old_worksheet_b(table, 2016, 0)
        self.assertAlmostEqual(month.total_amount(Category.BILLS), -100.0)

    def test_read_old_worksheet_b_fallback_date(self):
        # When date column is empty, falls back to datetime(year_index, month_index+1, 1)
        table = [
            [""],
            ["income", "", "", "", "", ""],
            ["FPI", "Salary", "1000.00", "", "", ""],  # empty date
        ]
        month = read_old_worksheet_b(table, 2016, 2)  # month_index=2 → March
        self.assertEqual(month.num_transactions(), 1)
        self.assertEqual(month.transactions[0].date, datetime.datetime(2016, 3, 1))

    def test_read_old_worksheet_b_skips_empty_type_row(self):
        table = [
            [""],
            ["income", "", "", "", "", ""],
            ["", "", "", "", "", ""],                            # empty type → InvalidRow
            ["FPI", "Salary", "500.00", "", "", "01/01/2016"],
        ]
        month = read_old_worksheet_b(table, 2016, 0)
        self.assertEqual(month.num_transactions(), 1)


class LoadYearTests(unittest.TestCase):
    """Tests for load_year."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _make_year(self, year_idx):
        y = Year(year_idx)
        m = Month(1)
        m.transactions.append(
            Transaction(
                date=datetime.date(year_idx, 1, 15),
                transaction_type=TransactionType.FPI,
                category=Category.INCOME,
                description="Salary",
                amount=1000.0,
                note="",
            )
        )
        y.months.append(m)
        return y

    def test_load_year_roundtrip(self):
        y = self._make_year(2024)
        filename = self.tmp_dir / "finances-2024.pickle"
        with open(filename, "wb") as f:
            pickle.dump(y, f, pickle.HIGHEST_PROTOCOL)
        loaded = load_year(2024, False, self.tmp_dir)
        self.assertEqual(loaded.index, 2024)
        self.assertEqual(loaded.months[0].num_transactions(), 1)
        self.assertAlmostEqual(loaded.months[0].total_amount(Category.INCOME), 1000.0)

    def test_load_year_missing_file_returns_empty_year(self):
        result = load_year(2024, False, self.tmp_dir)
        self.assertEqual(result.index, 2024)
        self.assertEqual(len(result.months), 0)


if __name__ == "__main__":
    unittest.main()
