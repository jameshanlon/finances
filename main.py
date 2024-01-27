import gspread
import argparse
from finances import finances
from rich import print

gc = gspread.service_account()

sheet_names = [
    "Spending-2019",
    "Spending-2020",
    "Spending-2021",
    "Spending-2022",
    "Spending-2023",
    "Spending-2024",
]


def main(args):
    sheet = gc.open(sheet_names[-1])
    worksheet = sheet.get_worksheet(0)
    values = worksheet.get_all_values()
    month = finances.read_worksheet(values)
    month.report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)

