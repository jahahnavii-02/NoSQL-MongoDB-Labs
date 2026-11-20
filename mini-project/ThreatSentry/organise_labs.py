from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent

# Folder renaming map
RENAMES = {
    "lab_3": "lab03",
    "lab4": "lab04",
    "lab5": "lab05",
    "lab6": "lab06",
    "lab7": "lab07",
    "lab8": "lab08",
    "lab9": "lab09",
}

# Numbering corrections
REPLACEMENTS = [
    (r"Labs?\s*1\?18", "Labs 1–18"),
    (r"Labs?\s*1-18", "Labs 1–18"),
    (r"Labs?\s*1–18", "Labs 1–18"),
    (r"Labs?\s*1\?17", "Labs 1–17"),
    (r"Labs?\s*1-17", "Labs 1–17"),
    (r"Labs?\s*1\?16", "Labs 1–16"),
    (r"Labs?\s*1-16", "Labs 1–16"),
]

def rename_folders():
    print("\n--- Folder renaming ---")

    for old_name, new_name in RENAMES.items():
        old_path = ROOT / old_name
        new_path = ROOT / new_name

        if old_path.exists():
            if new_path.exists():
                print(f"SKIPPED: {new_name} already exists")
                continue

            old_path.rename(new_path)
            print(f"RENAMED: {old_name} -> {new_name}")
        else:
            print(f"NOT FOUND: {old_name}")

def correct_readme():
    print("\n--- README correction ---")

    readme = ROOT / "README.md"

    if not readme.exists():
        print("README.md not found")
        return

    backup = ROOT / "README_backup.md"

    if not backup.exists():
        shutil.copy2(readme, backup)
        print("Backup created: README_backup.md")

    content = readme.read_text(encoding="utf-8")

    original = content

    for pattern, replacement in REPLACEMENTS:
        content = re.sub(
            pattern,
            replacement,
            content,
            flags=re.IGNORECASE
        )

    # Correct folder links in README
    for old_name, new_name in RENAMES.items():
        content = content.replace(old_name, new_name)

    if content != original:
        readme.write_text(content, encoding="utf-8")
        print("README.md updated successfully")
    else:
        print("No corrections required")

def main():
    print("NoSQL MongoDB Labs Organizer")
    print(f"Repository: {ROOT}")

    rename_folders()
    correct_readme()

    print("\nOrganization complete!")
    print("Please verify the folder structure before committing.")

if __name__ == "__main__":
    main()