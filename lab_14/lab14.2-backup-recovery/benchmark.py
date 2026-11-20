import csv
import os
import time
import getpass
import subprocess
from pathlib import Path
from datetime import datetime

CONTAINER = "lab13-mongo1"
SOURCE_DB = "lab14_benchmark"
RESTORE_DB = "lab14_benchmark_restore"
COLLECTION = "products"

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "benchmark_results"
OUTPUT.mkdir(exist_ok=True)

def docker_exec(args, password):
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

def mongo_eval(script, password):
    command = (
        'mongosh --host localhost --port 27017 '
        '--username ctiAdmin '
        '--password="$MONGO_BACKUP_PASSWORD" '
        '--authenticationDatabase admin --quiet --eval '
        + "'" + script.replace("'", "'\\''") + "'"
    )
    return docker_exec(["sh", "-lc", command], password)

def run():
    password = getpass.getpass("Enter ctiAdmin password: ")
    results = []

    for count in [1000, 10000, 100000]:
        print(f"\n========== {count} DOCUMENTS ==========")

        mongo_eval(
            f"""
            const d = db.getSiblingDB('{SOURCE_DB}');
            d.{COLLECTION}.drop();
            for (let start=1; start<={count}; start+=1000) {{
                let batch=[];
                for (let i=start; i<Math.min(start+1000,{count}+1); i++) {{
                    batch.push({{
                        test_id:i,
                        name:'Benchmark Product '+i,
                        category:'NoSQL',
                        price:i*10,
                        status:'original'
                    }});
                }}
                d.{COLLECTION}.insertMany(batch);
            }}
            print('Inserted: '+d.{COLLECTION}.countDocuments());
            """,
            password
        )

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        container_path = f"/tmp/lab14_benchmark_{count}_{stamp}"
        local_path = OUTPUT / f"benchmark_{count}_{stamp}"

        try:
            # Backup measurement
            start = time.perf_counter()

            docker_exec([
                "sh", "-lc",
                'mongodump --host=localhost --port=27017 '
                '--username=ctiAdmin '
                '--password="$MONGO_BACKUP_PASSWORD" '
                '--authenticationDatabase=admin '
                f'--db={SOURCE_DB} --collection={COLLECTION} '
                f'--out={container_path}'
            ], password)

            local_path.mkdir(parents=True, exist_ok=True)

            subprocess.run(
                ["docker", "cp",
                 f"{CONTAINER}:{container_path}/{SOURCE_DB}",
                 str(local_path)],
                check=True, capture_output=True, text=True
            )

            backup_seconds = time.perf_counter() - start

            bson = local_path / SOURCE_DB / f"{COLLECTION}.bson"
            if not bson.exists() or bson.stat().st_size == 0:
                raise RuntimeError("Backup BSON missing or empty.")

            backup_size = bson.stat().st_size

            # Restore measurement into a separate database
            mongo_eval(
                f"db.getSiblingDB('{RESTORE_DB}').{COLLECTION}.drop();",
                password
            )

            start = time.perf_counter()

            docker_exec([
                "sh", "-lc",
                'mongorestore --host=localhost --port=27017 '
                '--username=ctiAdmin '
                '--password="$MONGO_BACKUP_PASSWORD" '
                '--authenticationDatabase=admin '
                f'--db={RESTORE_DB} --collection={COLLECTION} '
                f'--drop {container_path}/{SOURCE_DB}/{COLLECTION}.bson'
            ], password)

            restore_seconds = time.perf_counter() - start

            check = mongo_eval(
                f"print(db.getSiblingDB('{RESTORE_DB}')."
                f"{COLLECTION}.countDocuments());",
                password
            )

            restored_count = int(check.strip().splitlines()[-1])

            if restored_count != count:
                raise RuntimeError(
                    f"Restore mismatch: expected {count}, got {restored_count}"
                )

            print("Documents:", restored_count)
            print(f"Backup time: {backup_seconds:.3f} seconds")
            print(f"Restore time: {restore_seconds:.3f} seconds")
            print("Backup size:", backup_size, "bytes")

            results.append([
                count,
                round(backup_seconds, 3),
                round(restore_seconds, 3),
                backup_size,
                restored_count
            ])

        finally:
            subprocess.run(
                ["docker", "exec", CONTAINER, "rm", "-rf", container_path],
                capture_output=True, text=True
            )

    csv_path = OUTPUT / "benchmark_results.csv"

    with open(csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Documents", "Backup_Time_Seconds",
            "Restore_Time_Seconds", "Backup_Size_Bytes",
            "Restored_Documents"
        ])
        writer.writerows(results)

    print("\nALL BENCHMARKS COMPLETED")
    print("Results saved to:", csv_path)

if __name__ == "__main__":
    run()
