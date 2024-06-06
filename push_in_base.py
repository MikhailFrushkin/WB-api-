import json
import re
from loguru import logger
import pandas as pd

from bd import Characteristic, CharacteristicValue, ArticleCharacteristicValue, Article


def push_characteristic(data):
    for item in data:
        id_wb = int(item['charcID'])
        name = item['name']
        try:
            charac = Characteristic.get(Characteristic.id_wb == id_wb)
        except Characteristic.DoesNotExist:
            charac = Characteristic.create(id_wb=id_wb, name=name)
            print(f'Обработана характеристика: {charac.id_wb} - {charac.name}')


if __name__ == '__main__':
    # пуш характеристик значков в таблицу
    with open('dir_wb\\characteristics 1559.json', 'r', encoding='utf-8') as f:
        data = json.load(f).get('data')
    push_characteristic(data)

    df = pd.read_excel('Значки 1.xlsx')

    # Список используемых столбцов
    used_columns = ['Номер склейки', 'Ссылка на срм', 'Артикул', 'Наименование',
                    'Описание', 'Категория', 'Цена', 'Глубина упаковки', 'Ширина упаковки', 'Высота упаковки']

    # Итерация по строкам DataFrame
    for index, row in df.iterrows():
        join_group = row['Номер склейки']
        url_crm = row['Ссылка на срм']
        art = row['Артикул']
        if ' ' in art:
            logger.error(art)
        if re.search('[а-яА-Я]', art):
            logger.error(f'В артикуле есть русские буквы: {art}')
        art = row['Артикул'].strip().replace(' ', '')
        name = row['Наименование']
        descriptions = row['Описание']
        category = row['Категория']
        price = row['Цена']
        length = row['Глубина упаковки']
        width = row['Ширина упаковки']
        height = row['Высота упаковки']
        try:
            article = Article.create(
                join_group=join_group,
                url_crm=url_crm,
                art=art,
                name=name,
                descriptions=descriptions,
                category=category,
                price=price,
                length=length,
                width=width,
                height=height,
            )
        except Exception as ex:
            logger.error(art)
        else:
            # Вывод всех остальных столбцов, которые не использовались
            other_columns = [col for col in df.columns if col not in used_columns]
            for col in other_columns:
                charac = None
                try:
                    charac = Characteristic.get(Characteristic.name == col)
                except Exception as ex:
                    print(col, ex)
                if charac:
                    try:
                        characteristic_value = CharacteristicValue.create(characteristic=charac, value=str(row[col]))
                    except Exception as ex2:
                        print(ex2)
                    else:
                        ArticleCharacteristicValue.create(article=article, characteristic_value=characteristic_value)
