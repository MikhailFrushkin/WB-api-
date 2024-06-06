from bd import Article


def main():
    articles = Article.select().where(Article.created_wb is False)
    print(articles)
    print(len(articles))


if __name__ == '__main__':
    main()
