from pathlib import Path

from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent
env = Env()
env.read_env()
api_key = env.str('token_4')
headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}
limit = 1000

token_y = env.str('token_y')
headers_yandex = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {token_y}'}
url_upload = 'https://cloud-api.yandex.net/v1/disk/resources'
url_publish = 'https://cloud-api.yandex.net/v1/disk/resources/publish'

# domain = 'http://127.0.0.1:8000/api_rest'
domain = 'https://mycego.online/api_rest'
url_api_created_prod = f'{domain}/create_prod/'
url_api_prod_list = f'{domain}/products-list/'

dir_wb = 'dir_wb'
