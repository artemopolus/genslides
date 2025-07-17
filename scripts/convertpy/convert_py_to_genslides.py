#!/usr/bin/env python3
"""
Скрипт для извлечения методов и информации о классах из Python-файла
с помощью парсера genslides.task_tools.py_parser.
"""

import sys
import json
import argparse
from pathlib import Path, PureWindowsPath

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
    output_file = Path(output_file_path)
    if output_file.is_dir():
        output_file = output_file / target_file.stem
        output_file = output_file.with_suffix(".json")
    else:
        return

    # Считываем содержимое файла
    with target_file.open("r", encoding="utf-8") as f:
        code = f.read()
        # print(f"📄 Прочитано {len(code)} символ(ов) из {target_file}")

    output_jsonfile = {
            "filename": target_file.name,
            "path": target_file.absolute().as_posix(),
            "version": "0.1",
            "description":"Json File for genslides app",
            "targets":[] 
        }

    base_imports = pyparser.get_import_statements( code )
    output_jsonfile["targets"].append({
        "type":"imports",
        "description": "imports",
        "body": "\n".join(base_imports)
    })

    base_global_vars = pyparser.get_global_variable_lines( code )
    base_global_vars_text = ""
    for idx, name, text in base_global_vars:
        base_global_vars += text

    if len(base_global_vars):
        output_jsonfile["targets"].append({
                "type":"variables",
                "parent_class": "None",
                "description": "global_vars",
                "body": base_global_vars_text
        })


    
    base_global_method_names = pyparser.get_global_functions( code )
    if len(base_global_method_names):
        base_global_method_text = ""
        for name in base_global_method_names:
            base_global_method_text += pyparser.get_function_info( name )
        output_jsonfile["targets"].append({
                "type":"method",
                "parent_class": "None",
                "description": "global methods",
                "body": base_global_method_text
        })


    base_class_names = pyparser.get_class_names_lines( code )
    for target_class_name, target_class_line in base_class_names:
        output_jsonfile["targets"].append({
                "type":"class",
                "parent_class": target_class_name,
                "name": target_class_name,
                "body": target_class_line
            })


        # Извлекаем информацию о методах и классах целевого класса
        target_methods, target_internal_classes = pyparser.get_class_info(code, target_class_name)
        for method_name in target_methods:
            target_method_body_text = pyparser.get_class_function_body(code, target_class_name, method_name)
            output_jsonfile["targets"].append({
                "type":"method",
                "parent_class": target_class_name,
                "name": method_name,
                "description": f"method {method_name} : class {target_class_name}",
                "body": target_method_body_text
            })

        # TODO:
        # for classname in target_internal_classes:


        # Вывод результатов
    print(f"Output written to {PureWindowsPath(output_file.resolve())}")
    try:
        with output_file.open("w", encoding="utf-8") as json_file:
        # with open(output_file_path, "w", encoding="utf-8") as json_file:
            json.dump(output_jsonfile, json_file, indent=4)
    except IOError as e:
        print(f"Error writing to file {output_file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Process python files in a directory to extract function information.")
    parser.add_argument("--path", required=True, help="Path to the folder with python source files")
    parser.add_argument("--output", required=True, help="Path to the folder to save output JSON files")
    global args
    args = parser.parse_args()

    print(f"Processed files in {args.path}")
    convert_file(args.path, args.output)


if __name__ == "__main__":
    main()

