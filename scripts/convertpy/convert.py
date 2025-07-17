#!/usr/bin/env python3
"""
Скрипт для извлечения методов и информации о классах из Python-файла
с помощью парсера genslides.task_tools.py_parser.
"""

import sys
import argparse
from pathlib import Path

# === Добавляем корень проекта в sys.path, чтобы можно было импортировать genslides ===
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# === Импортируем парсер Python-кода ===
import genslides.task_tools.py_parser as pyparser


def convert_file( target_file_path, output_file_path ):
    """
    Считывает файл, извлекает информацию о методах и классах,
    используя py_parser.get_class_info().
    """
    # Путь к файлу, который нужно проанализировать
    target_file = Path(target_file_path)

    # Считываем содержимое файла
    with target_file.open("r", encoding="utf-8") as f:
        code = f.read()
        print(f"📄 Прочитано {len(code)} символ(ов) из {target_file}")

    output_jsonfile = {
            "filename": target_file.name,
            "path": target_file.absolute().as_posix(),
            "targets":[] 
        }
    print( output_jsonfile )

    base_imports = pyparser.get_import_statements( code )
    print("Глобальные импорты:")
    print(base_imports)
    output_jsonfile["targets"].append({
        "function_name": "imports",
        "function_info": "\n".join(base_imports)
    })

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
        print("\n🏷️ Найденные внутренние классы:")
        print(target_internal_classes)

def main():
    parser = argparse.ArgumentParser(description="Process python files in a directory to extract function information.")
    parser.add_argument("--path", required=True, help="Path to the folder with python source files")
    parser.add_argument("--output", required=True, help="Path to the folder to save output JSON files")
    global args
    args = parser.parse_args()

    convert_file(args.path, args.output)

    print(f"Processed files in {args.path}")
    print(f"Output written to {args.output}")

if __name__ == "__main__":
    main()

