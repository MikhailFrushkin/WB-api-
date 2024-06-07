import openpyxl
from peewee import *

from bd import Article

db = SqliteDatabase('../base/base.db')
# Подключение к базе данных
db.connect()
# Создание новой книги и листа Excel
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Articles"

# Добавление заголовков
ws.append(["join_group", "art", "art_wb", "url_task"])

# Извлечение данных из базы данных и добавление их в лист
query = Article.select(Article.join_group, Article.art, Article.art_wb, Article.url_task)
for article in query:
    ws.append([article.join_group, article.art, article.art_wb, article.url_task])

# Сохранение книги Excel
wb.save("articles.xlsx")
# Закрытие подключения к базе данных
db.close()