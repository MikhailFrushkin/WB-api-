import json
import re
from pprint import pprint

import pandas as pd
import requests
from loguru import logger

from api_wb import get_barcode
from bd import Characteristic, CharacteristicValue, ArticleCharacteristicValue, Article
from config import url_api_prod_list


def get_info_site():
    """
    получение всех артикулов с сайта
    """
    response = requests.get(url_api_prod_list)
    if response.status_code == 200:
        data = response.json()
        pprint(len(data))
        with open('dir_wb\\site_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        logger.error(response.status_code)
        logger.error(response.text)


def push_characteristic():
    """
    пуш характеристик значков в таблицу
    """

    with open('dir_wb\\characteristics.json', 'r', encoding='utf-8') as f:
        data = json.load(f).get('data')
    for item in data:
        id_wb = int(item['charcID'])
        name = item['name']
        try:
            charac = Characteristic.get(Characteristic.id_wb == id_wb)
        except Characteristic.DoesNotExist:
            charac = Characteristic.create(id_wb=id_wb, name=name)
            print(f'Обработана характеристика: {charac.id_wb} - {charac.name}')


def created_article(file):
    df = pd.read_excel(file)

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
                    logger.error(f'{col}\n{ex}')
                if charac:
                    try:
                        characteristic_value = CharacteristicValue.create(characteristic=charac,
                                                                          value=str(row[col]).capitalize())
                    except Exception as ex2:
                        logger.error(f'{col}\n{ex2}')
                    else:
                        ArticleCharacteristicValue.create(article=article, characteristic_value=characteristic_value)
                else:
                    logger.error(f'Не найдена категория: {col}')


def push_urls_cat_in_arts():
    with open('dir_wb\\site_data.json', 'r', encoding='utf-8') as f:
        data_site = json.load(f)
    arts = Article.select().where(Article.public_url == None)
    for item in arts:
        id_art_site = item.url_crm.split('/')[-2]
        item.public_url = data_site[id_art_site].get('directory_url', None)
        task_id = data_site[id_art_site].get('task__id', None)
        if task_id:
            item.url_task = f'https://mycego.online/task/task/{task_id}/'
        item.category = data_site[id_art_site].get('category__name', None)
        item.brand = data_site[id_art_site].get('brand__name', None)
        item.save()


def push_barcode():
    arts = Article.select().where(Article.barcode == None)
    count = len(arts)
    data = get_barcode(count).get('data', None)
    if data:
        with open(f'dir_wb\\barcode.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        for index, art in enumerate(arts):
            art.barcode = data[index]
            print(data[index])
            art.save()


if __name__ == '__main__':
    print()
    # push_characteristic()
    # created_article('Значки 1.xlsx')
    # get_info_site()
    # push_urls_cat_in_arts()
    # push_barcode()