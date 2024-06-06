from datetime import datetime
from peewee import *

db = SqliteDatabase('base/base.db')


class Characteristic(Model):
    name = CharField(verbose_name='Название характеристики')
    id_wb = IntegerField(verbose_name='Id wb')

    class Meta:
        database = db


class CharacteristicValue(Model):
    characteristic = ForeignKeyField(Characteristic, verbose_name='Характеристика', backref='values')
    value = CharField(verbose_name='Значение')

    class Meta:
        database = db


class Article(Model):
    join_group = IntegerField(verbose_name='Номер склейки')
    url_crm = CharField(verbose_name='URL CRM')
    public_url = CharField(verbose_name='URL яндекс диска', null=True)
    art = CharField(verbose_name='Артикул', index=True, unique=True)
    name = TextField(verbose_name='Наименование')
    descriptions = TextField(verbose_name='Описание')
    category = CharField(verbose_name='Категория', null=True)
    brand = CharField(verbose_name='Бренд', null=True)
    price = IntegerField(verbose_name='Цена')
    length = IntegerField(verbose_name='Длина')
    width = IntegerField(verbose_name='Ширина')
    height = IntegerField(verbose_name='Высота')

    art_wb = IntegerField(verbose_name='Артикул wb', null=True)

    created_wb = BooleanField(verbose_name='Заведен', default=False)
    download_images = BooleanField(verbose_name='Фото загружены', default=False)
    joined = BooleanField(verbose_name='Склеен', default=False)
    folder_images_for_download = CharField(verbose_name='Папка', null=True)
    barcode = BigIntegerField(verbose_name='barcode', null=True)

    url_task = TextField(verbose_name='Ссылка на задачу', null=True)
    created_at = DateTimeField(verbose_name='Время создания', default=datetime.now)
    updated_at = DateTimeField(verbose_name='Время обновления', null=True)

    def __str__(self):
        return self.art

    class Meta:
        database = db


class ArticleCharacteristicValue(Model):
    article = ForeignKeyField(Article, verbose_name='Артикул')
    characteristic_value = ForeignKeyField(CharacteristicValue, verbose_name='Значение характеристики')

    class Meta:
        database = db


if __name__ == '__main__':
    # Создание таблиц, если они не существуют
    def create_tables():
        with db:
            db.create_tables([Characteristic, CharacteristicValue, ArticleCharacteristicValue, Article])


    # Запуск функции создания таблиц
    create_tables()
