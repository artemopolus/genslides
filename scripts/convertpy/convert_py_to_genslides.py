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



def main():
    parser = argparse.ArgumentParser(description="Process python files in a directory to extract function information.")
    parser.add_argument("--path", required=True, help="Path to the folder with python source files")
    parser.add_argument("--output", required=True, help="Path to the folder to save output JSON files")
    global args
    args = parser.parse_args()

    print(f"Processed files in {args.path}")
    result = pyparser.convert_genslide_json_file(args.path, args.output)
    print(result["report"])



if __name__ == "__main__":
    main()

