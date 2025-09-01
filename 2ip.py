#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pip install beautifulsoup4
"""
Парсер заголовков mail.ru для WSL
Установка: pip3 install requests beautifulsoup4 lxml
"""


import requests
from bs4 import BeautifulSoup
import sys
import subprocess
import os


def check_wsl_environment():
    """Проверяем что мы в WSL и настраиваем окружение"""
    print("🔍 Проверяем среду WSL...")

    # Проверяем что мы в Linux (WSL)
    if not sys.platform.startswith('linux'):
        print("⚠️  Этот код оптимизирован для WSL/Linux")
        print("   Но будет работать и в других средах")

    # Проверяем доступ к интернету
    try:
        requests.get('https://google.com', timeout=5)
        print("✓ Интернет соединение работает")
    except:
        print("✗ Нет интернет соединения")
        return False

    return True


def install_dependencies():
    """Устанавливаем необходимые зависимости для WSL"""
    print("\n📦 Проверяем зависимости...")

    dependencies = {
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'lxml': 'lxml'
    }

    missing_deps = []

    for import_name, package_name in dependencies.items():
        try:
            if import_name == 'bs4':
                __import__('bs4')
            else:
                __import__(import_name)
            print(f"✓ {package_name} установлен")
        except ImportError:
            print(f"✗ {package_name} не установлен")
            missing_deps.append(package_name)

    if missing_deps:
        print(f"\n⏳ Устанавливаем недостающие зависимости...")
        try:
            # Устанавливаем через pip3
            cmd = [sys.executable, "-m", "pip", "install"] + missing_deps
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                print("✓ Зависимости успешно установлены!")
                return True
            else:
                print(f"✗ Ошибка установки: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("✗ Таймаут при установке зависимостей")
            return False
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            return False
    else:
        print("✓ Все зависимости установлены!")
        return True


def get_mail_ru_titles():
    """Основная функция для получения заголовков с mail.ru"""
    try:
        print("\n🌐 Подключаемся к mail.ru...")

        # URL и заголовки
        url = "https://mail.ru"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Отправляем запрос с таймаутом
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"✗ Ошибка HTTP: {response.status_code}")
            return

        print("✓ Страница успешно загружена")

        # Парсим HTML с lxml parser (быстрее и надежнее)
        soup = BeautifulSoup(response.content, 'lxml')

        print("🔍 Ищем заголовки новостей...")

        # Список для хранения заголовков
        titles = []

        # 1. Поиск по конкретным классам mail.ru
        selectors = [
            '.news__list__item__link',  # Основные новости
            '.js-topnews__item',  # Топ новости
            '.ph__project__news__item__link',  # Новости в хедере
            '[class*="news-tabs__item"]',  # Новости в табах
            '[class*="title"] a',  # Ссылки с классом title
            '.svelte-1jw2u6k',  # Новые классы Svelte
            '[data-qa*="news"]',  # По data-qa атрибутам
            '[data-testid*="news"]',  # По data-testid атрибутам
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 20 and text not in titles:
                    titles.append(text)

        # 2. Поиск по заголовкам h1-h4
        for i in range(1, 5):
            headers = soup.find_all(f'h{i}')
            for header in headers:
                text = header.get_text(strip=True)
                if text and len(text) > 15 and text not in titles:
                    titles.append(text)

        # 3. Поиск по атрибутам, характерным для новостей
        news_elements = soup.find_all(attrs={
            'data-module': True,
            'data-newsid': True,
            'data-type': 'news'
        })

        for elem in news_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 15 and text not in titles:
                titles.append(text)

        # Выводим результаты
        if titles:
            print(f"\n📰 НАЙДЕНО {len(titles)} ЗАГОЛОВКОВ:\n")
            print("=" * 80)

            for i, title in enumerate(titles[:25], 1):
                print(f"{i:2d}. {title}")

            print("=" * 80)
            print(f"Показано {min(25, len(titles))} из {len(titles)} заголовков")

            # Сохраняем в файл
            save_to_file(titles)

        else:
            print("✗ Не удалось найти заголовки")
            debug_page(soup)

    except requests.exceptions.RequestException as e:
        print(f"✗ Ошибка сети: {e}")
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")


def save_to_file(titles):
    """Сохраняет заголовки в файл"""
    try:
        with open('mail_ru_titles.txt', 'w', encoding='utf-8') as f:
            f.write("Заголовки новостей с mail.ru\n")
            f.write("=" * 50 + "\n\n")
            for i, title in enumerate(titles, 1):
                f.write(f"{i}. {title}\n")
        print(f"💾 Результаты сохранены в файл: mail_ru_titles.txt")
    except Exception as e:
        print(f"✗ Ошибка сохранения файла: {e}")


def debug_page(soup):
    """Отладочная информация для анализа структуры страницы"""
    print("\n🐛 Отладочная информация:")
    print("Попробуем найти возможные селекторы...")

    # Ищем все классы содержащие 'news'
    news_classes = set()
    for element in soup.find_all(class_=True):
        for class_name in element['class']:
            if 'news' in class_name.lower():
                news_classes.add(class_name)

    if news_classes:
        print("Найдены классы с 'news':", list(news_classes)[:10])

    # Ищем все data-атрибуты
    data_attrs = set()
    for element in soup.find_all(attrs=True):
        for attr in element.attrs:
            if attr.startswith('data-') and any(x in attr for x in ['news', 'item', 'link']):
                data_attrs.add(attr)

    if data_attrs:
        print("Найдены data-атрибуты:", list(data_attrs)[:10])


def main():
    """Главная функция"""
    print("🚀 Парсер заголовков mail.ru для WSL")
    print("=" * 50)

    # Проверяем среду
    if not check_wsl_environment():
        return

    # Устанавливаем зависимости
    if not install_dependencies():
        print("\n❌ Не удалось установить зависимости")
        print("Попробуйте выполнить вручную:")
        print("sudo apt update && sudo apt install python3-pip")
        print("pip3 install requests beautifulsoup4 lxml")
        return

    # Запускаем парсинг
    get_mail_ru_titles()

    print("\n" + "=" * 50)
    print("✅ Готово! Для повторного запуска:")
    print(f"   python3 {os.path.basename(__file__)}")


if __name__ == "__main__":
    main()
