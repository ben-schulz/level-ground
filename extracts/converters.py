import csv

import openpyxl
import pandas as pd


def remove_excel_suffix(path):
    ix = str.rfind(path, ".xlsx")
    if -1 < ix:
        return path[0:ix]
    return path


def excel_to_csv(source_path, out_path):

    workbook = openpyxl.load_workbook(filename=source_path)

    sheets = workbook.worksheets

    out_path = remove_excel_suffix(out_path)

    if 1 == len(sheets):
        df = pd.DataFrame([v for v in workbook.worksheets[0].values])
        df.to_csv(f"{out_path}.csv", quoting=csv.QUOTE_ALL)

    else:
        for number, sheet in enumerate(sheets):
            df = pd.DataFrame([v for v in workbook.worksheets[number].values])
            df.to_csv(f"{out_path}.{number}.csv", quoting=csv.QUOTE_ALL)
