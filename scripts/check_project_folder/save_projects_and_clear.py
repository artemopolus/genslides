import json
import argparse
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


# =========================
# NORMALIZATION
# =========================
def norm(p: Path) -> str:
    return str(p.resolve()).lower().rstrip("\\/")


# =========================
# LOAD A
# =========================
def load_A(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = set()

    for item in data.get("actioners", []):
        if item.get("type") == "project":
            result.add(norm(Path(item["act_path"])))

    return result


# =========================
# BUILD B
# =========================
def build_B(root: Path):
    result = set()
    for pj in root.rglob("project.json"):
        result.add(norm(pj.parent))
    return result


# =========================
# SAFETY CHECK
# =========================
def is_safe(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


# =========================
# ARCHIVE FULL B (AUTO NAME)
# =========================
def create_archive(root: Path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 👇 имя берём автоматически из папки B
    folder_name = root.resolve().name

    archive_name = f"{folder_name}_{timestamp}.7z"
    archive_path = root.parent / archive_name

    cmd = ["7z", "a", str(archive_path), str(root)]

    print(f"\n📦 Creating archive:\n{archive_path}\n")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        raise RuntimeError("❌ Archive creation failed")

    return archive_path


# =========================
# DELETE EXTRA
# =========================
def delete_extra(extra_dirs, root: Path):
    print("\n🗑️ Deleting extra directories...\n")

    for d in sorted(extra_dirs):
        p = Path(d)

        if not is_safe(p, root):
            print(f"⚠️ SKIP unsafe: {p}")
            continue

        if p.exists():
            print(f"Deleting: {p}")
            shutil.rmtree(p, ignore_errors=False)
        else:
            print(f"⚠️ Missing: {p}")


# =========================
# MAIN
# =========================
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--a-file", required=True)
    parser.add_argument("--b-root", required=True)

    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delete-extra", action="store_true")

    args = parser.parse_args()

    A_file = Path(args.a_file)
    B_root = Path(args.b_root)

    if not A_file.exists():
        print("❌ A file not found")
        sys.exit(1)

    if not B_root.exists():
        print("❌ B root not found")
        sys.exit(1)

    # =========================
    # DATA
    # =========================
    A = load_A(A_file)
    B = build_B(B_root)

    extra = B - A
    missing = A - B

    print("\n=== SUMMARY ===")
    print(f"A expected : {len(A)}")
    print(f"B found    : {len(B)}")
    print(f"Extra      : {len(extra)}")
    print(f"Missing    : {len(missing)}")

    if missing:
        print("\n❌ Missing paths:")
        for p in sorted(missing):
            print(p)
        sys.exit(2)

    # =========================
    # ARCHIVE
    # =========================
    if args.dry_run:
        print("\n🧪 DRY RUN - no archive created")
        return

    archive_path = create_archive(B_root)

    print(f"\n✅ Archive created:\n{archive_path}")

    # =========================
    # DELETE
    # =========================
    if args.delete_extra:
        print("\n⚠️ DELETE EXTRA ENABLED")
        delete_extra(extra, B_root)
        print("\n✅ Deletion done")
    else:
        print("\nℹ️ Extra not deleted")


if __name__ == "__main__":
    main()