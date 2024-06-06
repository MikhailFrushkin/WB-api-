import os


def main():
    directory = r'D:\rebase_pop\готовые'
    set_list_images = set()
    for root, dirs, files in os.walk(directory):
        if len(files) != 6:
            print(root)


if __name__ == '__main__':
    main()
