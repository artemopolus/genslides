import argparse
import py7zr
from pathlib import Path


def extract_subdir(archive_path: Path, relative_path: str):
    relative_path = relative_path.replace("\\", "/").rstrip("/") + "/"

    output_root = Path(archive_path).parent

    print(f"Целевая папка: {output_root}")

    with py7zr.SevenZipFile(archive_path, mode="r") as z:
        all_files = z.getnames()

        # ищем совпадения
        targets = [f for f in all_files if relative_path in f]

        if not targets:
            print("❌ Ничего не найдено. Проверь путь внутри архива.")
            print("Доступные пути (первые 50):")
            for f in all_files[:50]:
                print(f)
            return

        print(f"Найдено файлов: {len(targets)}")
        print("Извлечение...")

        z.extract(targets=targets, path=output_root)

        print("✅ Готово")


def main():
    parser = argparse.ArgumentParser(
        description="Extract specific folder from 7z archive"
    )

    parser.add_argument(
        "--archive",
        required=True,
        help="Путь к .7z архиву"
    )

    parser.add_argument(
        "--relative",
        required=True,
        help="Относительный путь внутри архива (например: dir_helper_nexus_v1/controls/summary_v1)"
    )

    args = parser.parse_args()

    archive_path = Path(args.archive)

    if not archive_path.exists():
        print(f"❌ Архив не найден: {archive_path}")
        return

    extract_subdir(archive_path, args.relative)


if __name__ == "__main__":
    main()