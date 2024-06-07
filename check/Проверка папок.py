import os


def main(directory):
    for root, dirs, files in os.walk(directory):
        if len(files) < 1:
            print(root)

if __name__ == '__main__':
    directory = r'G:\Загрузка на wb'
    main(directory)