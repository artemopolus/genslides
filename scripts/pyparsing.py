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
        code = f.read()
        print(f"📄 Прочитано {len(code)} символ(ов) из {target_file}")

    base_imports = pyparser.get_import_statements( code )
    print("Глобальные импорты:")
    print(base_imports)

    base_global_vars = pyparser.get_global_variable_lines( code )
    print("Глобальные переменные:")
    print( base_global_vars )
    base_global_methods = pyparser.get_global_functions( code )
    print("Глобальные функции:")
    print( base_global_methods )

    base_classes = pyparser.get_class_names( code )
    print("Найданные классы:")
    print(base_classes)
    for target in base_classes:

        # Извлекаем информацию о методах и классах целевого класса
        target_methods, target_internal_classes = pyparser.get_class_info(code, target)

        # Вывод результатов

        if len(target_methods):
            print("\n🔍 Найденные внутренние методы:")
            print(target_methods[0])
            target_method_body_example = pyparser.get_class_function_body(code, target, target_methods[0])
            print(target_method_body_example)
            print(f"Function '{target}' arguments:")
            print( pyparser.get_class_function_body(code, target, target_methods[0], return_type= "params") )
        print("\n🏷️ Найденные внутренние классы:")
        print(target_internal_classes)



if __name__ == "__main__":
    read_file_for_methods()

