import gspread

gc = gspread.oauth()

sheet = gc.open("Finances-2024")
worksheet = sheet.get_worksheet(0)

values = worksheet.get_all_values()

print(values)
