import os
import re
from stop_words import get_stop_words
import xml.etree.ElementTree as ET
from nltk import FreqDist
import pymorphy2
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urlparse, urljoin
from os import listdir
from os.path import isfile, join

# Создаём список файлов в папке
files = []

# добавляем анализатор слов
morph = pymorphy2.MorphAnalyzer()

# Указываем путь к папке
path_text = 'texts'

# Указываем путь к папке с картинками
path_img = 'C:/img'

# Массив имён файлов
mas_file_name = []

# Массив ключевых слов
mas_name = []

# Массив частот употребления слов в тексте
mas_str_count = []

# Массив для новых файлов
mas_new_keywords = []

# Массив картинок
mas_img = []

file_for_link = []

links = []

mas_files_for_links = []

def download_images(url, folder):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('img')

    for i, img in enumerate(images):
        img_url = img.get('src')
        img_url = urljoin(url, img_url)  # Make absolute URL if it's relative
        img_data = requests.get(img_url).content
        img_name = path_img + '/' + folder + '/' + f'image{i+1}.jpg'

        with open(img_name, 'wb') as img_file:
            mas_img.append(img_name)
            img_file.write(img_data)

def save_page_text(url, limit=2):
    # Проверка ограничения на количество файлов
    if limit <= 0:
        return
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Используем BeautifulSoup для извлечения заголовка страницы
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip()

            # Очищаем недопустимые символы из заголовка, чтобы создать имя файла
            title = ''.join(char for char in title if char.isalnum() or char.isspace())
            filename = f"{title}.txt"

            #Создаем и записываем текстовый файл
            with open(path_text + '/' + filename, 'w', encoding='utf-8') as file:
                file.write(soup.get_text())
                try:
                    os.mkdir(path_img + '/' + filename)
                    download_images(url, filename)
                except Exception as e:
                    print(f"Ошибка при загрузке картинки {url}: {str(e)}")

            print(mas_img)
            print(f"Сохранено: {filename}")

            # Уменьшаем ограничение и ищем ссылки на другие страницы
            limit -= 1
            if limit > 0:
                links = soup.find_all('a', href=True)
                for link in links:
                    next_url = link['href']
                    if next_url.startswith("http"):
                        save_page_text(next_url, limit)
    except Exception as e:
        print(f"Ошибка при обработке {url}: {str(e)}")


# Формирование XML и HTML файлов
def keywords_most_freq_with_stop(some_text, file_name):
    stop_words = get_stop_words("ru")

    # Разделение на слова
    tokenized_text = re.findall(r'\b\w+\b', some_text.lower())

    # Приведение к нормальной форме
    tokenized_text = [morph.parse(word)[0].normal_form for word in tokenized_text if word not in stop_words]

    # <keyword "name">
    pair_name = [word_freq_pair[0] for word_freq_pair in FreqDist(tokenized_text).most_common(3)]
    # <keyword "count">
    pair_count = [word_freq_pair[1] for word_freq_pair in FreqDist(tokenized_text).most_common(3)]

    # Формирование XML - файла
    dataXML = ET.Element('data')
    dataXML.text = '\n  '

    textXML = ET.SubElement(dataXML, 'text')
    textXML.text = ' ' + text + '\n  '
    textXML.tail = '\n  '

    keywordsXML = ET.SubElement(dataXML, 'keywords')
    keywordsXML.text = '\n    '

    mas_keys = []

    # В данном цикле используем анализатор слов для приведения к именительному падежу
    for name, count in zip(pair_name, pair_count):
        word_noun = name
        p = morph.parse(word_noun)[0].normal_form
        # Добавляем ключевые слова
        keywordXML = ET.SubElement(keywordsXML, 'keyword')
        keywordXML.set('name', "".join(p))
        str_count = str(count)
        keywordXML.set('count', str_count)
        keywordXML.tail = '\n '
        keywordXML.tail = '\n    '
        keywordsXML.tail = '\n'
        mas_name.append(p)
        mas_keys.append(p)
        mas_file_name.append(file_name)
        mas_str_count.append(str_count)

    # Сохраняем xml - файл
    tree = ET.ElementTree(dataXML)
    tree.write('XML/' + file_name[:-3] + 'xml', xml_declaration=True, encoding='utf-8')

    mas_files_for_links.append(file_name[:-3])

def create_image_html(file_name, img_links):
    # Формируем HTML-ФАЙЛ с картинками
    html_file_name = 'HTML/' + file_name + 'html'
    mas_img_files = []
    temp_path = path_img + '/' + file_name + 'txt'
    mas_img_files = [f for f in listdir(temp_path) if isfile(join(temp_path, f))]
    print(mas_img_files)
    # print(mas_keys)

    with open(html_file_name, 'w', encoding='utf-8') as f:
        dataHTML = ET.Element('html')
        dataHTML.set('lang', 'en')
        dataHTML.text = '\n'

        headHTML = ET.SubElement(dataHTML, 'head')
        headHTML.text = '\n  '
        headHTML.tail = '\n'

        metaHTML = ET.SubElement(headHTML, 'meta')
        metaHTML.set('charset', 'UTF-8')
        metaHTML.set('name', 'viewport')
        metaHTML.set('content', 'width=device-width, initial-scale=1.0')
        metaHTML.tail = '\n  '

        titleHTML = ET.SubElement(headHTML, 'title')
        titleHTML.text = '' + path_text + '/' + file_name
        titleHTML.tail = '\n'

        bodyHTML = ET.SubElement(dataHTML, 'body')
        bodyHTML.text = '\n    '
        bodyHTML.tail = '\n'

        i = 0
        icnt = len(img_links)

        for img_name in mas_img_files:
            tmp = temp_path + '/' + img_name
            aHTML = ET.SubElement(bodyHTML, 'a')
            aHTML.set('href', img_links[i])
            aHTML.set('target', '_blank')

            i = i + 1
            if i >= icnt:
                i = 0
            aHTML = ET.SubElement(aHTML, 'img')
            aHTML.set('src', tmp)

        treeHTML = ET.ElementTree(dataHTML)
        treeHTML.write(html_file_name, encoding='utf-8')
        f.close()
def set_links_in_files():
    # Получаем ссылку на ключевое слово в документе
    res_mas = zip(mas_name, zip(mas_str_count, mas_file_name))
    masDict = defaultdict(list)

    for key, val in res_mas:
        masDict[key].append(val)
    for key in masDict:
        masDict[key] = sorted(masDict[key], reverse=True)
        if (len(masDict[key]) > 1):
            masDictRes = masDict[key]
            # print(masDictRes)
            for i in range(len(masDictRes)):
                key_word = key
                count_key_word = masDictRes[i][0]
                # print(key_word, count_key_word)

                keys_for_links = []

                for j in range(len(masDictRes)):
                    if (masDictRes[j][0] < count_key_word):
                        # print(masDictRes[j][0], count_key_word)
                        file_for_add_link = masDictRes[i][1][:-3]
                        print(key_word, count_key_word, masDictRes[i][1], masDictRes[j][1])

                        link = masDictRes[j][1][:-3] + 'html'

                        file_for_link.append(file_for_add_link)
                        links.append(link)

            mas_for_link = []
            mas_for_link = defaultdict(list)
            file_zip = zip(file_for_link, links)
            for key, val in file_zip:
                mas_for_link[key].append(val)

            for el in mas_files_for_links:
                if el not in mas_for_link:
                    mas_for_link[el].append('#')

            for key in mas_for_link:
                create_image_html(key, mas_for_link[key])
            break


starting_url = input("Введите URL начальной страницы: ")
save_page_text(starting_url)

files = os.listdir(path_text)

for filename in files:
    with open(path_text + '/' + filename, 'r', encoding='utf-8') as f:
        text = f.read()
    # Вызываем функцию создания файлов
    keywords_most_freq_with_stop(text, filename)

# Вызываем функцию генерации ссылок
set_links_in_files()


