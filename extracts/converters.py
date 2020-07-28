import csv
import xlrd


def excel_to_csv(source_path, dest_path):

    workbook = xlrd.open_workbook(source_path)

    sheets = workbook.sheets()

    def _sheet_to_csv(sheet, out_path):
        with open(out_path, "w") as f:
            output_writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            for row in sheet.get_rows():
                output_writer.writerow(row)

    if 1 == len(sheets):
        _sheet_to_csv(sheets[0], dest_path)

    else:
        for number, sheet in enumerate(sheets):
            _sheet_to_csv(sheet, f"{dest_path}.{number}")
