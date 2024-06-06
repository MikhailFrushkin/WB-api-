import asyncio
import json
import os
import time
from urllib.parse import quote

import aiohttp
import pandas as pd
import requests
from loguru import logger

from config import token_y, url_api_created_prod, url_publish, headers_yandex, url_upload
from utils import df_in_xlsx


def create_prod(data_art):
    headers = {'Content-Type': 'application/json'}
    json_data = json.dumps(data_art)
    response = requests.post(url_api_created_prod, data=json_data, headers=headers)
    if response.status_code == 200:
        logger.success(f'Артикул успешно создан {data_art["art"]}')
    else:
        logger.warning(response.status_code)


def public_folder(path):
    """Публикация папки и файлов.
    path: Путь к папке."""
    requests.put(f'{url_publish}?path={path}', headers=headers_yandex)


async def traverse_yandex_disk(session, folder_path, result_dict, offset=0):
    limit = 1000
    url = f"https://cloud-api.yandex.net/v1/disk/resources?path={quote(folder_path)}&limit={limit}&offset={offset}"
    headers = {"Authorization": f"OAuth {token_y}"}
    dirs_list = ['Значки ШК', 'AniKoya', 'DP', 'Popsockets', 'сделать', 'Новые значки']
    try:
        async with (session.get(url, headers=headers) as response):
            data = await response.json()
            tasks = []

            for item in data["_embedded"]["items"]:
                if item["type"] == "dir" and (item["name"] not in result_dict):
                    if item["name"] not in dirs_list:
                        result_dict[item["name"].lower()] = item["path"]
                    task = traverse_yandex_disk(session, item["path"], result_dict)
                    tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks)

            total = data["_embedded"]["total"]
            offset += limit
            if offset < total:
                await traverse_yandex_disk(session, folder_path, result_dict, offset)

    except Exception as ex:
        pass


async def main_search(folder_path):
    result_dict = {}
    async with aiohttp.ClientSession() as session:
        await traverse_yandex_disk(session, folder_path, result_dict)

    df = pd.DataFrame(list(result_dict.items()), columns=['Имя', 'Путь'])
    logger.info('Создан документ Пути к артикулам.xlsx')
    df_in_xlsx(df, 'Пути к артикулам')
    return result_dict


def upload_file(loadfile, savefile, replace=False):
    resp = requests.get(f'{url_upload}/upload?path={savefile}&overwrite={replace}', headers=headers_yandex)
    res = resp.json()
    if resp.status_code == 409:
        logger.warning(f'Файл существует {savefile}')
        return True
    else:
        with open(loadfile, 'rb') as f:
            try:
                requests.put(res['href'], files={'file': f})
            except KeyError as e:
                logger.error(f"KeyError: {e}. Response: {res}")
            except requests.exceptions.Timeout as e:
                logger.error("Timeout error:", e)
            except requests.exceptions.RequestException as e:
                logger.error("An error occurred:", e)
                logger.error("An error occurred:", resp.status_code)
                logger.error("An error occurred:", resp.json())
            except Exception as e:
                logger.error(f"An error Exception: {e}")
            else:
                return True


def get_info(path):
    """Получения url папки.
    path: Путь к папке."""
    url = f'https://cloud-api.yandex.net/v1/disk/resources?path={path}&limit=1000'
    response = requests.get(url, headers=headers_yandex)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logger.error(f"Error {response.status_code}: {response.text}\n{path}")
        return None


if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # result_dict = loop.run_until_complete(main_search('/Новая база (1)/Попсокеты ДП'))
    # pprint(result_dict)

    # df = pd.read_excel('Файлы связанные с заказом/Пути к артикулам.xlsx')
    # for index, row in df.iterrows():
    #     print(index)
    #     public_folder(path=row['Путь'].removeprefix('disk:/'))

    # directory = r'D:\PyCharm\GenBarcode\output'
    # yandex_path = '/Новая база (1)/Попсокеты ДП/'
    # for index, file in enumerate(os.listdir(directory), start=1):
    #     file_name, exp = os.path.splitext(file)
    #     yandex_path_file = yandex_path + file_name + '/' + file
    #
    #     try:
    #         flag = upload_file(os.path.join(directory, file), yandex_path_file)
    #         if flag:
    #             logger.success(f'{index} {file_name}')
    #     except Exception as ex:
    #         logger.error(ex)

    directory = r'D:\PyCharm\GenBarcode\output_DP'
    for index, file in enumerate(os.listdir(directory)[1500:], start=1):
        file_name, exp = os.path.splitext(file)
        yandex_path = '/Новая база (1)/Попсокеты ДП/' + file_name
        data_art = get_info(path=yandex_path)
        if data_art:
            data_art_push = {
                "art": data_art['name'],
                "brand": "Дочке понравилось",
                "category": "Попсокеты",
                "quantity": 1,
                "size": 6,
                "directory_url": data_art['public_url'],
                "images": [['1.png', None]],
                "skin": [['Подложка.png', None]],
                "mockup": [
                    ['Мокап.png', None],
                    ['Мокап-2.png', None],
                    ['Мокап-3.png', None],
                    ['Мокап-4.png', None],
                ],
                "sizes_images": [['Размер.png', None]],
                "sticker": [[f"{data_art['name']}.pdf", None]],
            }
            create_prod(data_art_push)
        else:
            time.sleep(15)
        if index == 500:
            break
