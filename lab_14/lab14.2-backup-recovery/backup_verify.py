import os
import time
import getpass
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import schedule

CONTAINER = "lab13-mongo1"
DATABASE = "lab14_backup_verification"
COLLECTION = "backup_test"
BACKUP_ROOT = Path(__file__).resolve().parent / "backups"
RETENTION_DAYS = 7

def docker_command(args, password):
    env = os.environ.copy()
    env["MONGO_BACKUP_PASSWORD"] = password
    result = subprocess.run(
        ["docker", "exec", "-e", "MONGO_BACKUP_PASSWORD",
         CONTAINER] + args,
        env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout

def cleanup_old_backups():
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)

    for folder in BACKUP_ROOT.iterdir():
        if folder.is_dir() and folder.name.startswith("backup_"):
            modified = datetime.fromtimestamp(folder.stat().st_mtime)
            if modified < cutoff:
                shutil.rmtree(folder)
                print("Expired backup removed:", folder.name)

def run_backup(password):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = "backup_" + stamp
    container_path = "/tmp/" + backup_name
    host_path = BACKUP_ROOT / backup_name

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    print("\nStarting backup:", stamp)

    try:
        docker_command([
            "sh", "-lc",
            'mongodump --host=localhost --port=27017 '
            '--username=ctiAdmin '
            '--password="$MONGO_BACKUP_PASSWORD" '
            '--authenticationDatabase=admin '
            f'--db={DATABASE} --collection={COLLECTION} '
            f'--out={container_path}'
        ], password)

        run = subprocess.run(
            ["docker", "cp",
             f"{CONTAINER}:{container_path}", str(host_path)],
            capture_output=True, text=True
        )

        if run.returncode != 0:
            raise RuntimeError(run.stderr)

        bson_files = list(host_path.rglob("*.bson"))
        if not bson_files or bson_files[0].stat().st_size == 0:
            raise RuntimeError("BSON backup missing or empty.")

        print("Backup verified:", host_path)
        print("BSON size:", bson_files[0].stat().st_size, "bytes")

        cleanup_old_backups()

    except Exception as error:
        print("BACKUP FAILED:", error)
        raise

    finally:
        subprocess.run(
            ["docker", "exec", CONTAINER, "rm", "-rf", container_path],
            capture_output=True, text=True
        )

def main():
    password = getpass.getpass("Enter ctiAdmin password: ")

    print("\n1. Run one backup")
    print("2. Start hourly backup scheduler")

    choice = input("Select 1 or 2: ").strip()

    if choice == "1":
        run_backup(password)

    elif choice == "2":
        print("Hourly scheduler started. Press Ctrl+C to stop.")
        schedule.every().hour.do(run_backup, password)

        while True:
            schedule.run_pending()
            time.sleep(1)

    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
