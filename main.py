import gspread
import argparse
from finances import finances
from rich import print
from dataclasses import dataclass

gc = gspread.service_account()


@dataclass
class Sheet:
    name: str
    reader


sheets = {
    "2019": Sheet("Spending-2019", finances.read_old_worksheet),
    "2020": Sheet("Spending-2020", finances.read_old_worksheet),
    "2021": Sheet("Spending-2021", finances.read_old_worksheet),
    "2022": Sheet("Spending-2022", finances.read_old_worksheet),
    "2023": Sheet("Spending-2023", finances.read_old_worksheet),
    "2024": Sheet("Spending-2024", finances.read_worksheet),
}


def report_month(sheet, year: str, month_index: int):
    print(f"Opening worksheet {month_index} from {sheet_name}")
    worksheet = sheet.get_worksheet(month_index)
    values = worksheet.get_all_values()
    month = sheets[year].reader(values)
    month.report_transactions()


def report_sheet(year: str, month_index: int):
    sheet = gc.open(sheets[year].name)
    worksheet_count = len(spreadsheet.worksheets())
    if month_index == -1:
        # Report all months.
        for i in range(min(12, worksheet_count)):
            report_month(sheet, i)
    else:
        # Report one month.
        report_month(sheet, month_index)


def main(args):
    if args.year:
        report_sheet(args.year, args.month)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    parser.add_argument("--year", default=None, help="Report a particular year")
    parser.add_argument("--month", default=-1, help="Report a particular month")
    main(args)
