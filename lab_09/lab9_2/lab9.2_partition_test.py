import csv
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient, WriteConcern
from pymongo.errors import PyMongoError

# Configure MONGO_URI when running in a different environment.
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://mongo-secondary1:27017/?directConnection=true"
)

DATABASE_NAME = "lab9"
COLLECTION_NAME = "partition_test"
OUTPUT_FILE = Path(__file__).with_name("lab9_2_results.csv")


def test_write(client, label, write_concern):
    collection = client[DATABASE_NAME][COLLECTION_NAME].with_options(
        write_concern=WriteConcern(**write_concern)
    )

    document = {
        "test": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "write_concern": str(write_concern),
    }

    started = time.perf_counter()
    status = "SUCCESS"
    details = ""

    try:
        result = collection.insert_one(document)
        details = f"acknowledged={result.acknowledged}"
    except PyMongoError as exc:
        status = "ERROR"
        details = f"{type(exc).__name__}: {exc}"

    elapsed = time.perf_counter() - started

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test": label,
        "write_concern": str(write_concern),
        "status": status,
        "elapsed_seconds": round(elapsed, 4),
        "details": details,
    }

    print(
        f"{label} | {status} | "
        f"{elapsed:.3f}s | {details}"
    )
    return row


def main():
    rows = []

    print("Lab 9.2 - Network Partition Write Test")
    print(f"MongoDB URI: {MONGO_URI}")
    print("Run this script once while connected, and again during a partition.")
    print("The script does not disconnect or reconnect Docker networks.")

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )

    try:
        client.admin.command("ping")
        print("MongoDB connection successful.")

        rows.append(
            test_write(client, "w1_test", {"w": 1})
        )
        rows.append(
            test_write(
                client,
                "majority_test",
                {"w": "majority", "wtimeout": 5000},
            )
        )
    except PyMongoError as exc:
        print(f"Connection or test error: {type(exc).__name__}: {exc}")
    finally:
        client.close()

    file_exists = OUTPUT_FILE.exists()
    with OUTPUT_FILE.open("a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "timestamp",
            "test",
            "write_concern",
            "status",
            "elapsed_seconds",
            "details",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists or OUTPUT_FILE.stat().st_size == 0:
            writer.writeheader()

        writer.writerows(rows)

    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()