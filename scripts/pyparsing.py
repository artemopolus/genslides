#!/usr/bin/env python3
"""
Скрипт для извлечения методов и информации о классах из Python-файла
с помощью парсера genslides.task_tools.py_parser.
"""

import sys
from pathlib import Path

# === Добавляем корень проекта в sys.path, чтобы можно было импортировать genslides ===
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# === Импортируем парсер Python-кода ===
import genslides.task_tools.py_parser as pyparser


def read_file_for_methods():
    """
    Считывает файл, извлекает информацию о методах и классах,
    используя py_parser.get_class_info().
    """
    # Путь к файлу, который нужно проанализировать
    target_file = Path("genslides/commanager/group.py")

    # Считываем содержимое файла
    with target_file.open("r", encoding="utf-8") as f:
        text = f.read()
        print(f"📄 Прочитано {len(text)} символ(ов) из {target_file}")

    # Извлекаем информацию о методах и классах целевого класса
    methods, classes = pyparser.get_class_info(text, "Actioner")

    # Вывод результатов
    print("\n🔍 Найденные методы:")
    print(methods)

    print("\n🏷️ Найденные классы:")
    print(classes)


if __name__ == "__main__":
    read_file_for_methods()

