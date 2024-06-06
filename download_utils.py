import asyncio
import os
import time
from datetime import datetime
from pprint import pprint

import aiohttp
import requests
from loguru import logger

from config import headers_yandex, url_upload, url_publish


def get_download_url(public_url):
    try:
        url = f'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={public_url}'
        response = requests.get(url, headers=headers_yandex)
        if response.status_code == 200:
            dow_url = response.json().get('href', None)
            logger.success(dow_url)
            return dow_url
        else:
            logger.error(response.status_code)
            logger.error(response.text)
    except Exception as ex:
        logger.error(ex)


def download_file(destination_path, public_url=None, url=None):
    """
    Скачивание файла по публичной ссылке.
    url: URL файла для скачивания.
    destination_path: Путь, куда файл будет сохранен.
    """
    if url is None and public_url:
        try:
            url = get_download_url(public_url)
        except Exception as ex:
            logger.error(ex)
    if url:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(destination_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            file.write(chunk)
                logger.info(f"File downloaded successfully: {destination_path}")
            else:
                logger.error(f"Error {response.status_code} while downloading file: {url}")
        except requests.RequestException as e:
            logger.error(f"Error during downloading file: {e}")


def get_info(path):
    """Получения url папки.
    path: Путь к папке."""
    url = f'https://cloud-api.yandex.net/v1/disk/resources?path={path}&limit=1000'
    response = requests.get(url, headers=headers_yandex)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logger.error(f"Error {response.status_code}: {response.text}")
        return None


def get_info_publish_folder(public_url):
    result_data = []
    res = requests.get(
        f'https://cloud-api.yandex.net/v1/disk/public/resources?public_key={public_url}&fields=_embedded&limit=1000')
    if res.status_code == 200:
        data = res.json().get('_embedded', {}).get('items', [])
        for i in data:
            file_name = i.get('name', None).lower()
            if file_name:
                if 'мокап' in file_name or 'подложка' in file_name or 'упаковка' in file_name:
                    result_data.append({
                        'name': i.get('name', None),
                        'image': i.get('sizes', [])[0].get('url', None),
                        'preview': i.get('preview', None),
                        'file': i.get('file', None)
                    })

        return result_data
    else:
        logger.error(res.status_code)


def upload_file(loadfile, savefile, replace=False):
    """Загрузка файла.
    savefile: Путь к файлу на Диске
    loadfile: Путь к загружаемому файлу
    replace: true or false Замена файла на Диске"""
    resp = requests.get(f'{url_upload}/upload?path={savefile}&overwrite={replace}', headers=headers_yandex)
    res = resp.json()
    if resp.status_code == 409:
        logger.info(f'Файл существует {savefile}')
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


if __name__ == '__main__':
    start = datetime.now()
    data = get_info_publish_folder('https://yadi.sk/d/KQl1IIUvtPOvxw')
    link_str = [i.get('file') for i in data]
    print(link_str)
    logger.success(datetime.now() - start)
