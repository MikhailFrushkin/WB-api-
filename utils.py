import os
import re
import shutil

import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.workbook import Workbook


def rename_dp(string):
    pattern = re.compile(r'(POPSOCKET|POPSOCKER|POPSICKET)')
    new_name = pattern.sub(lambda match: match.group() + '_DP', string)
    return new_name.strip()


def df_in_xlsx(df: pd.DataFrame, filename: str, directory: str = 'Файлы связанные с заказом', max_width: int = 50):
    """Запись датафрейма в файл"""
    workbook = Workbook()
    sheet = workbook.active
    for row in dataframe_to_rows(df, index=False, header=True):
        sheet.append(row)
    for column in sheet.columns:
        column_letter = column[0].column_letter
        max_length = max(len(str(cell.value)) for cell in column)
        adjusted_width = min(max_length + 2, max_width)
        sheet.column_dimensions[column_letter].width = adjusted_width

    os.makedirs(directory, exist_ok=True)
    workbook.save(f"{directory}\\{filename}.xlsx")


def copy_files_name_in_directory(filename, directory, directory_to):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if filename in file:
                folder = os.path.basename(os.path.dirname(os.path.join(root, file)))
                shutil.copy2(os.path.join(root, file), os.path.join(directory_to, f'{folder}.png'))
