import glob
import json
import time
from pprint import pprint

import requests
from loguru import logger

from config import headers, dir_wb, api_key, token_y, limit

# Все карточки товара
url_all_cards = "https://suppliers-api.wildberries.ru/content/v2/get/cards/list"
# Родительские категории товаров
url_parents = "https://suppliers-api.wildberries.ru/content/v2/object/parent/all"
# Список предметов (подкатегорий)
url_category = "https://suppliers-api.wildberries.ru/content/v2/object/all"
# Характеристики предмета (подкатегории)
url_characteristics = "https://suppliers-api.wildberries.ru/content/v2/object/charcs"
# Генерация баркодов
url_barcode = "https://suppliers-api.wildberries.ru/content/v2/barcodes"
# Обновление карточки
url_update = "https://suppliers-api.wildberries.ru/content/v2/cards/update"


def get_parents():
    data = {
        "locale": 'ru'
    }
    data_json = json.dumps(data)
    response = requests.get(url_parents, headers=headers, data=data_json)
    if response.status_code == 200:
        response_data = response.json()
        with open(f'{dir_wb}\\parents.json', 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)
    else:
        logger.error(response.status_code)
        logger.error(response.text)


def get_category(name):
    # Параметры запроса
    params = {
        'name': name,
        'limit': 1000,
        'locale': 'ru',
        'offset': 0
    }
    url = "https://suppliers-api.wildberries.ru/content/v2/object/all"
    # Выполнение GET-запроса
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        response_data = response.json()
        pprint(response_data)
        with open(f'{dir_wb}\\category {parentID}.json', 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)
    else:
        logger.error(response.status_code)
        logger.error(response.text)


def get_characteristics(subjectID):
    url = f'https://suppliers-api.wildberries.ru/content/v2/object/charcs/{subjectID}'
    params = {
        'locale': 'ru'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        response_data = response.json()
        pprint(response_data)
        with open(f'{dir_wb}\\characteristics {subjectID}.json', 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)
    else:
        logger.error(response.status_code)
        logger.error(response.text)


def parser_wb_cards() -> list[dict]:
    """Получение карточек товаров"""
    max_attempts = 5
    attempts = 0
    time_sleep = 15

    result = []  # Здесь будем хранить все полученные данные
    data = {
        "settings": {
            "cursor": {
                "limit": limit
            },
            "filter": {
                "withPhoto": -1,
                "objectIDs": [3560]
            }
        }
    }

    while True:
        data_json = json.dumps(data)
        try:
            response = requests.post(url_all_cards, headers=headers, data=data_json)
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при отправке запроса: {e}")
            break

        if response.status_code == 200:
            response_data = response.json()
            result.extend(response_data.get("cards", []))
            total = response_data['cursor']['total']
            nmID = response_data['cursor']['nmID']
            updatedAt = response_data['cursor']['updatedAt']
            current_count = len(result)
            logger.info(f"Получено {current_count}")

            if total < limit:
                break
            # Обновляем курсор для следующего запроса
            data["settings"]["cursor"]["updatedAt"] = updatedAt
            data["settings"]["cursor"]["nmID"] = nmID
        elif response.status_code == 500 or response.status_code == 504:
            attempts += 1
            if attempts >= max_attempts:
                logger.error(f"Достигнут лимит попыток ({max_attempts}). Прекращаем выполнение.")
                break
            logger.warning(f"Ошибка {response.status_code}: {response.text}. Повторный запрос через 15 секунд.")
            time.sleep(time_sleep)
        else:
            logger.error(f"Ошибка {response.status_code}: {response.text}")
            break

    with open(f'{dir_wb}/wildberries_data_cards.json', 'w', encoding='utf-8') as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    logger.success(f"Все данные сохранены в файл 'wildberries_data_cards.json'")
    return result


def read_json_data(dir_wb: str, dir_result: str):
    data = {}
    json_files = glob.glob(f'{dir_wb}/*.json')
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            for item in json_data:
                try:
                    data[item.get('vendorCode')] = {
                        'art_wb': item.get('nmID', None),
                        'subjectName': item.get('subjectName', None),
                        'brand': item.get('brand', None),
                        'title': item.get('title', None),
                        'description': item.get('description', None),
                        'dimensions': {
                            'length': item.get('dimensions', {}).get('length', None),
                            'width': item.get('dimensions', {}).get('width', None),
                            'height': item.get('dimensions', {}).get('height', None),
                        },
                        'characteristics': dict(
                            [(i.get('name'), i.get('value')) for i in item.get('characteristics', [])]
                        ),
                        'skus': item.get('sizes', [])[0].get('skus', None),
                        'createdAt': item.get('createdAt', None),
                        'updatedAt': item.get('updatedAt', None)
                    }
                except Exception as ex:
                    logger.error(ex)
                    logger.error(item.get('vendorCode'))

    with open(f'{dir_result}/result_wb.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_barcode(count):
    data = {
        "count": count
    }
    data_json = json.dumps(data)
    response = requests.post(url_barcode, headers=headers, data=data_json)
    if response.status_code == 200:
        response_data = response.json()
        pprint(response_data)
        with open(f'{dir_wb}\\barcode.json', 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)
    else:
        logger.error(response.status_code)
        logger.error(response.text)


def create_card_wb(data: dict, list_sku: list):
    url_create_card = 'https://suppliers-api.wildberries.ru/content/v2/cards/upload'

    for index, (art, data_art) in enumerate(data.items()):
        try:
            if index < 1550:
                continue
            sku = list_sku[index]
            data_push = [
                {
                    "subjectID": 3560,
                    "variants": [
                        {
                            "vendorCode": art,
                            "title": data_art.get('title'),
                            "description": data_art.get('description').replace('АniKoya', "'Дочке понравилось'")
                            .replace('AniKoya', "'Дочке понравилось'"),
                            "brand": "Дочке понравилось",
                            "dimensions": {
                                "length": data_art.get('dimensions', {}).get('length', 15),
                                "width": data_art.get('dimensions', {}).get('width', 11),
                                "height": data_art.get('dimensions', {}).get('height', 1),
                            },
                            "characteristics": [
                                {
                                    "id": 89008,
                                    "value": 15
                                },
                                {
                                    "id": 378533,
                                    "value": ['Попсокет',
                                              'Держатель для  телефона',
                                              'Попсокет кольцо']
                                },
                                {
                                    "id": 14177451,
                                    "value": "Россия"
                                },
                                {
                                    "id": 17596,
                                    "value": ["пластик"]
                                },
                                {
                                    "id": 14177449,
                                    "value": data_art.get('characteristics', {}).get('Цвет', ''),
                                },
                                {
                                    "id": 14177452,
                                    "value": data_art.get('description').replace('АniKoya',
                                                                                 "'Дочке понравилось'").replace(
                                        'AniKoya', "'Дочке понравилось'")
                                },
                                {
                                    "id": 15000000,
                                    "value": data_art.get('title')
                                },
                                {
                                    "id": 90630,
                                    "value": data_art.get('characteristics', {}).get('Высота предмета', 4.4),
                                },
                                {
                                    "id": 90652,
                                    "value": data_art.get('characteristics', {}).get('Глубина предмета', 1),
                                },
                                {
                                    "id": 90673,
                                    "value": data_art.get('characteristics', {}).get('Ширина предмета', 4.4),
                                }

                            ],
                            "sizes": [
                                {
                                    "price": 1000,
                                    "skus": [
                                        f"{sku}"
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
            data_json = json.dumps(data_push)
            response = requests.post(url_create_card, headers=headers, data=data_json)
            if response.status_code == 200:
                logger.success(f'{index} Создан артикул: {art}')
            elif response.status_code == 429:
                logger.error(f'{response.text} {art}')
                time.sleep(60)
            else:
                pass
                # logger.error(response.status_code)
                # logger.error(response.text)

        except Exception as ex:
            logger.error(ex)
            time.sleep(20)


def push_media(art_id: int, images_list: []):
    url = 'https://suppliers-api.wildberries.ru/content/v3/media/save'
    data = {
        "nmId": art_id,
        "data": images_list
    }
    data_json = json.dumps(data)
    response = requests.post(url, headers=headers, data=data_json)
    if response.status_code == 200:
        logger.success(f'Загрузились картинки для {art_id}')
    else:
        logger.error(response.status_code)
        logger.error(response.text)


def get_url_images(art):
    headers_y = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {token_y}'}
    path_atr = f'Новая база (1)/Попсокеты ДП/{art}'
    result_data = {}
    url = f'https://cloud-api.yandex.net/v1/disk/resources?path={path_atr}&limit=1000'
    response = requests.get(url, headers=headers_y)
    if response.status_code == 200:
        data = response.json().get('_embedded', {}).get('items', [])
        for i in data:
            file_name = i.get('name', None)
            if file_name:
                try:
                    result_data[i.get('name')] = i.get('file', None)
                except Exception as ex:
                    logger.error(url)
                    logger.error(ex)

    else:
        logger.error(f"Error {response.status_code}: {response.text}")
        return None
    return result_data


def push_media_in_comp(art_id: int, index: int, file_name: str, path_image: str, art: str):
    url = 'https://suppliers-api.wildberries.ru/content/v3/media/file'
    headers = {
        "Authorization": api_key,
        "X-Nm-Id": str(art_id),  # Преобразуем в строку
        "X-Photo-Number": f"{index}",  # Преобразуем в строк
    }
    files = [
        ("uploadfile", (f"{file_name}", open(f"{path_image}", "rb"), "image/png"))
    ]

    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        logger.success(f'Загрузились картинка {index}-{file_name} для {art_id}-{art}')
        return True
    else:
        logger.error(response.status_code)
        logger.error(response.text)


if __name__ == '__main__':
    logger.add(
        "logs/main.log",
        rotation="200 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file!s} | {line} | {message}"
    )
    subjectID = 1559
    parentID = 200
    name = 'Значки'
    # parser_wb_cards()
    # get_parents()
    # get_category()
    # get_characteristics()

    # get_barcode(1903)
    # data = art_on_push()
    # with open('dir_wb/barcode.json', 'r', encoding='utf-8') as f:
    #     list_sku = json.load(f).get('data')
    # create_card_wb(data, list_sku)

    # data_arts_wb = parser_wb_cards()
    # with open('dir_wb/wildberries_data_cards.json', 'r', encoding='utf-8') as f:
    #     data_arts_wb_in_file = json.load(f)
    # filtered_list = [d for d in data_arts_wb_in_file if d.get("subjectID") == 3560]

    # for index_main, item in enumerate(filtered_list, start=1):
    #     count = 0
    #     try:
    #         art_id = item['nmID']
    #         art = item['vendorCode']
    #         directory = rf'D:\rebase_pop\Готовые переименованные\{art}'
    #         image_list = ['Подложка.png', 'Размер.png', 'Мокап.png', 'Мокап-2.png', 'Мокап-4.png', 'Мокап-3.png']
    #
    #         for index, file_name in enumerate(image_list, start=1):
    #             if push_media_in_comp(art_id, index, file_name, os.path.join(directory, file_name), art):
    #                 count += 1
    #                 time.sleep(0.5)
    #         logger.debug(f'{index_main} Успешных загрузок для артикула {art}: {count}')
    #         with open('result.txt', 'a') as f:
    #             f.write(f'{art}: {count}\n')
    #     except Exception as ex:
    #         logger.error(ex)
    #         time.sleep(30)
    # Разбиваем список на чанки по 50 элементов
    # chunk_size = 50
    # chunks = [filtered_list[i:i + chunk_size] for i in range(0, len(filtered_list), chunk_size)]
    #
    # # Проходимся по каждому чанку
    # for chunk_index, chunk in enumerate(chunks):
    #     push_data = []
    #     for index_main, item in enumerate(chunk):
    #         try:
    #             for i in item['characteristics']:
    #                 if i['id'] == 90673:
    #                     i['value'] = 4
    #                 elif i['id'] == 90630:
    #                     i['value'] = 4
    #                 elif i['id'] == 90652:
    #                     i['value'] = 0.5
    #             push_data.append(item)
    #
    #         except Exception as ex:
    #             logger.error(ex)
    #     data_json = json.dumps(push_data)
    #     try:
    #         response = requests.post(url_update, headers=headers, data=data_json)
    #         print(response.status_code)
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"Ошибка при отправке запроса: {e}")
    #     logger.success(f'Изменено {chunk_index * 50 + len(push_data)}')
    #     time.sleep(10)
    # get_parents()
    # get_category(name)
    get_characteristics(subjectID)