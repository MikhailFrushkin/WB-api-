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


def create_folder(path):
    """Создание папки. \n path: Путь к создаваемой папке."""
    res = requests.put(f'{url_upload}?path={path}', headers=headers_yandex)
    if res.status_code == 201:
        public_folder(path)


def public_folder(path):
    """Публикация папки и файлов.
    path: Путь к папке."""
    requests.put(f'{url_publish}?path={path}', headers=headers_yandex)


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


def delete_folder(path):
    """Удаление папки на Яндекс.Диске.
    path: Путь к удаляемой папке."""
    res = requests.delete(f'https://cloud-api.yandex.net/v1/disk/resources?path={path}',
                          headers=headers_yandex)
    if res.status_code in [202, 204]:
        logger.info(f"Folder '{path}' deleted successfully.")
    else:
        logger.error(f"Error {res.status_code}: {res.text}")


def get_info_publish_folder(public_url):
    result_data = []
    res = requests.get(
        f'https://cloud-api.yandex.net/v1/disk/public/resources?public_key={public_url}&fields=_embedded&limit=1000')
    if res.status_code == 200:
        data = res.json().get('_embedded', {}).get('items', [])
        pprint(data)
        for i in data:
            file_name = i.get('name', None)
            if file_name:
                try:
                    result_data.append({
                        'name': i.get('name', None),
                        'image': i.get('sizes', [])[0].get('url', None),
                        'preview': i.get('preview', None),
                        'file': i.get('file', None)
                    })
                except:
                    pass

        return result_data
    else:
        logger.error(res.status_code)


async def async_upload_file(loadfile, savefile, replace=False):
    async with aiohttp.ClientSession() as session:
        response = await session.get(f'{url_upload}/upload?path={savefile}&overwrite={replace}', headers=headers_yandex)
        res = await response.json()
        if response.status == 200:
            async with session.put(res['href'], data=open(loadfile, 'rb')) as put_response:
                if put_response.status != 200:
                    await put_response.text()
        else:
            logger.error(res)


async def async_backup(savepath, loadpath, delete=False):
    folder = '{0}'.format(loadpath.split(f'{os.path.sep}')[-1])
    full_savepath = f'{savepath}/{folder}'
    create_folder(savepath)

    if delete:
        delete_folder(full_savepath)
        await asyncio.sleep(5)

    create_folder(full_savepath)

    tasks = []
    for address, _, files in os.walk(loadpath):
        for file in files:
            source_path = f'{address}{os.path.sep}{file}'
            destination_path = f'{savepath}/{folder}/{file}'
            task = async_upload_file(source_path, destination_path)
            tasks.append(task)

    await asyncio.gather(*tasks)


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


def backup(savepath, loadpath, delete=False):
    """Загрузка папки на Диск.
    savepath: Путь к папке на Диске для сохранения
    loadpath: Путь к загружаемой папке"""
    create_folder(savepath)
    folder = '{0}'.format(loadpath.split(f'{os.path.sep}')[-1])
    full_savepath = f'{savepath}/{folder}'
    if delete:
        delete_folder(full_savepath)
        time.sleep(5)
    # Создание новой папки
    create_folder(full_savepath)

    for address, _, files in os.walk(loadpath):
        for file in files:
            source_path = f'{address}{os.path.sep}{file}'
            destination_path = f'{savepath}/{folder}/{file}'
            flag = upload_file(source_path, destination_path)
            if not flag:
                raise ConnectionError('Ошибка загрузки')


if __name__ == '__main__':
    start = datetime.now()
    data = get_info_publish_folder('https://disk.yandex.com.am/d/k0Dxzy243834hg')
    link_str = [i.get('file') for i in data]
    print(';'.join(link_str))
    print(link_str)
    logger.success(datetime.now() - start)
