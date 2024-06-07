import asyncio
import os
import time
from datetime import datetime
from pprint import pprint

import aiohttp
import requests
from loguru import logger

from bd import Article
from config import headers_yandex, url_upload, url_publish


def download_file(destination_path, url):
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
                        'file': i.get('file', None)
                    })

        return result_data
    else:
        logger.error(res.status_code)


def download_files_art():
    directory = r'G:\Загрузка на wb'
    arts = Article.select().where(Article.folder_images_for_download == None)
    for art in arts:
        folder_art = os.path.join(directory, art.art)

        if os.path.exists(folder_art):
            art.folder_images_for_download = folder_art
            art.save()
        else:
            os.makedirs(folder_art, exist_ok=True)
            try:
                data = get_info_publish_folder(art.public_url)
                for image in data:
                    file_name = image.get('name')
                    url = image.get('file')
                    destination_path = os.path.join(folder_art, file_name)
                    download_file(destination_path=destination_path, url=url)
            except Exception as ex:
                logger.error(ex)
            else:
                art.folder_images_for_download = folder_art
                art.save()


if __name__ == '__main__':
    start = datetime.now()
    download_files_art()
    logger.success(datetime.now() - start)
