import json
import os
import shutil
from collections import OrderedDict

import openpyxl
import pandas as pd
from loguru import logger

from utils import rename_dp


def art_on_push():
    directory = r'D:\rebase_pop\Готовые переименованные'
    with open('result_wb.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    not_found_art = [i for i in os.listdir(directory) if i.replace('_DP', '') not in [j.strip() for j in data.keys()]]
    logger.error(not_found_art)
    found_art = [i for i in os.listdir(directory) if i.replace('_DP', '') in [j.strip() for j in data.keys()]]
    logger.debug(len(found_art))

    filtered_data = {rename_dp(key): value for key, value in data.items() if rename_dp(key) in found_art}

    def update_spreadsheet(path: str, _df, starcol: int = 1, startrow: int = 1, sheet_name: str = "ToUpdate"):

        wb = openpyxl.load_workbook(path)
        for ir in range(0, len(_df)):
            for ic in range(0, len(_df.iloc[ir])):
                wb[sheet_name].cell(startrow + ir, starcol + ic).value = _df.iloc[ir][ic]
        wb.save(path)
        logger.success(f'Создан файл: {path}')

    def create_xlsx(data_art: dict):
        file_path = '1.xlsx'
        new_file_path = '2.xlsx'
        shutil.copy2(file_path, new_file_path)

        df = pd.read_excel(file_path)
        df_data = OrderedDict()
        for i in df.columns:
            df_data[i] = []
        for key, value in data_art.items():
            try:
                for i in df_data:
                    if i == 'Артикул производителя':
                        df_data[i].append(rename_dp(key))
                    elif i == 'Предмет':
                        df_data[i].append('Кольца-держатели для телефона')
                    elif i == 'Бренд':
                        df_data[i].append('Дочке понравилось')
                    elif i == 'Артикул продавца':
                        df_data[i].append(key)
                    elif i == 'Цена':
                        df_data[i].append(1000)
                    elif i == 'Состав':
                        df_data[i].append('Пластик')
                    elif i == 'Высота упаковки':
                        df_data[i].append(15)
                    elif i == 'Ширина упаковки':
                        df_data[i].append(11)
                    elif i == 'Длина упаковки':
                        df_data[i].append(1)
                    elif i == 'Комплектация':
                        df_data[i].append('Держатель для телефона')
                    elif i == 'Материал изделия':
                        df_data[i].append('Пластик')
                    elif i == 'Страна производства':
                        df_data[i].append('Россия')

                    elif i == 'Цвет':
                        color = value.get('characteristics', {}).get("Цвет", [])
                        if color:
                            df_data[i].append(','.join(color))
                        else:
                            df_data[i].append('')
                    elif i == 'Пол':
                        gender = value.get('characteristics', {}).get('Пол', '')
                        if gender:
                            df_data[i].append(','.join(gender))
                        else:
                            df_data[i].append('')
                    elif i == 'Наименование':
                        title = value.get('title', '')
                        df_data[i].append(title)
                    elif i == 'Описание':
                        description = value.get('description', '').replace('AniKoya', '"Дочке понравилось"')
                        df_data[i].append(description)
                    else:
                        df_data[i].append('')

            except Exception as ex:
                logger.error(f'Ошибка в строке {ex} {key}')
        new_data = pd.DataFrame(df_data)

        try:
            update_spreadsheet(new_file_path, new_data, sheet_name='Шаблон', starcol=1, startrow=2)
        except Exception as ex:
            logger.error(f'Ошибка сохранения файла {ex}')

    # create_xlsx(filtered_data)
    return filtered_data


if __name__ == '__main__':
    art_on_push()
