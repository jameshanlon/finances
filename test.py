import gspread

gc = gspread.service_account()

sheet_names = [
        "Spending-2019",
        "Spending-2020",
        "Spending-2021",
        "Spending-2022",
        "Spending-2023",
        "Spending-2024",
        ]

sheet = gc.open(sheet_names[-1])
worksheet = sheet.get_worksheet(0)

values = worksheet.get_all_values()

print(values)
