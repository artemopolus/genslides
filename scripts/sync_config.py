#!/usr/bin/env python3

import argparse
import json
import shutil
from pathlib import Path
from copy import deepcopy
from datetime import datetime


def sync_json(sync_path: Path, local_path: Path):

    # Создаем резервную копию локального файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = local_path.with_name(
        f"{local_path.name}.{timestamp}.bak"
    )

    shutil.copy2(local_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Загружаем JSON
    with sync_path.open("r", encoding="utf-8") as f:
        sync_data = json.load(f)

    with local_path.open("r", encoding="utf-8") as f:
        local_data = json.load(f)

    # Индексируем локальный файл по полю type
    local_by_type = {
        item["type"]: item
        for item in local_data
        if isinstance(item, dict) and "type" in item
    }

    added_fields = 0

    for sync_item in sync_data:
        if not isinstance(sync_item, dict):
            continue


        item_type = sync_item.get("type")

        local_item = local_by_type.get(item_type)

        # Если такого словаря нет вообще — добавляем его целиком
        if local_item is None:
            local_data.append(deepcopy(sync_item))
            local_by_type[item_type] = local_data[-1]
            print(f"Added object '{item_type}'")
            continue

        # Иначе добавляем только отсутствующие поля
        for key, value in sync_item.items():
            if key not in local_item:
                local_item[key] = deepcopy(value)
                added_fields += 1
                print(f"[{item_type}] Added field '{key}'")


    # Сохраняем результат
    with local_path.open("w", encoding="utf-8") as f:
        json.dump(local_data, f, ensure_ascii=False, indent=3)

    print(f"\nDone. Added {added_fields} field(s).")


def main():
    parser = argparse.ArgumentParser(
        description="Синхронизация структуры локального JSON с эталонным."
    )
    parser.add_argument(
        "--local",
        required=True,
        help="Путь до локального JSON."
    )
    parser.add_argument(
        "--sync",
        required=True,
        help="Путь до синхронизируемого JSON."
    )

    args = parser.parse_args()

    sync_json(
        Path(args.sync),
        Path(args.local)
    )


if __name__ == "__main__":
    main()