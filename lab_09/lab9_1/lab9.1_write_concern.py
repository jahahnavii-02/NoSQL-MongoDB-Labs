import csv
import os
import sys
import time
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import PyMongoError


# Use MONGO_URI supplied by Docker, or default to Windows localhost.
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27018/?directConnection=true"
)

DATABASE_NAME = "lab9"
COLLECTION_NAME = "write_concern_results"
DOCUMENTS_PER_TEST = 1000
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "lab9_1_results.csv")
TIMEOUT_MS = 15000

CONFIGURATIONS = [
    ("w:1", 1, False),
    ("w:1", 1, True),
    ("w:majority", "majority", False),
    ("w:majority", "majority", True),
    ("w:3", 3, False),
    ("w:3", 3, True),
]


def main():
    print("=" * 75)
    print("LAB 9.1 - MEASURE WRITE CONCERN LATENCY")
    print(f"Documents per configuration: {DOCUMENTS_PER_TEST}")
    print(f"MongoDB endpoint: {MONGO_URI}")
    print("=" * 75)

    results = []

    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        client.admin.command("ping")
        database = client[DATABASE_NAME]

    except PyMongoError as exc:
        print("\nMongoDB connection failed.")
        print(f"Endpoint: {MONGO_URI}")
        print(f"Error: {exc}")
        print(
            "\nCheck that MongoDB is running and that MONGO_URI "
            "points to a reachable MongoDB server."
        )
        return 1

    try:
        for label, w_value, journal in CONFIGURATIONS:
            print(f"\nTesting {label}, j={journal} ...")

            collection = database[COLLECTION_NAME].with_options(
                write_concern=client[DATABASE_NAME][COLLECTION_NAME]
                .with_options()
                .write_concern.with_options(
                    w=w_value,
                    j=journal,
                    wtimeout=TIMEOUT_MS,
                )
            )

            successful = 0
            error_message = ""
            started = time.perf_counter()

            for index in range(DOCUMENTS_PER_TEST):
                document = {
                    "test_label": label,
                    "journal": journal,
                    "sequence": index,
                    "created_at": datetime.now(timezone.utc),
                }

                try:
                    collection.insert_one(document)
                    successful += 1
                except PyMongoError as exc:
                    error_message = str(exc)
                    print(f"Error: {error_message}")
                    break

            elapsed = time.perf_counter() - started
            average_ms = (
                elapsed * 1000 / successful if successful else None
            )

            print(
                f"Successful inserts: "
                f"{successful}/{DOCUMENTS_PER_TEST}"
            )
            print(f"Total time: {elapsed:.4f} seconds")
            print(
                "Average latency: "
                + (f"{average_ms:.3f} ms/write" if average_ms is not None
                   else "N/A")
            )

            results.append({
                "concern": label,
                "journal": journal,
                "requested": DOCUMENTS_PER_TEST,
                "successful": successful,
                "total_seconds": round(elapsed, 4),
                "average_ms": (
                    round(average_ms, 3)
                    if average_ms is not None else ""
                ),
                "error": error_message,
            })

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "concern",
                    "journal",
                    "requested",
                    "successful",
                    "total_seconds",
                    "average_ms",
                    "error",
                ],
            )
            writer.writeheader()
            writer.writerows(results)

        print("\nCOMPARISON TABLE")
        print("-" * 75)
        print(
            f"{'Concern':<15}{'Journal':<10}{'Success':<12}"
            f"{'Total (s)':<15}{'Average (ms)':<15}"
        )
        print("-" * 75)

        for result in results:
            average = (
                str(result["average_ms"])
                if result["average_ms"] != "" else "N/A"
            )
            print(
                f"{result['concern']:<15}"
                f"{str(result['journal']):<10}"
                f"{result['successful']:<12}"
                f"{result['total_seconds']:<15}"
                f"{average:<15}"
            )

        print("-" * 75)
        print(f"Results saved to: {os.path.abspath(OUTPUT_CSV)}")

        print("\nINTERPRETATION")
        print("- w:1 requests acknowledgement from the primary.")
        print("- w:majority requests acknowledgement from a majority.")
        print("- w:3 requests acknowledgement from all three data-bearing members.")
        print("- The arbiter does not store data.")
        print("- j=True requests journal acknowledgement.")
        print("- Actual latency depends on the system and network.")

        if any(row["successful"] == 0 for row in results):
            print(
                "\nWARNING: One or more tests failed. Check the recorded "
                "errors before interpreting the timing comparison."
            )

    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())