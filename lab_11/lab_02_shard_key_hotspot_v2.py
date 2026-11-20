"""
Lab 11.2 - Shard Key Hotspot Detection (Version 2)

Simulates the difference between:
1. A monotonically increasing range shard key.
2. A hashed shard key.

IMPORTANT:
This is a simulation, not a real MongoDB sharded-cluster measurement.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient
from pymongo.errors import PyMongoError


# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "shard_test"
COLLECTION_NAME = "hotspot_v2"
DOCUMENT_COUNT = 10_000
SHARD_COUNT = 4
LAB_TAG = "lab11_hotspot_v2"


def hash_bucket(value):
    """Map a value into one of the simulated shard buckets."""
    digest = hashlib.md5(str(value).encode("utf-8")).hexdigest()
    return int(digest, 16) % SHARD_COUNT


def print_distribution(title, counts):
    """Print counts and percentages for each simulated shard."""
    print(f"\n{title}")
    for shard, count in enumerate(counts):
        percentage = count / DOCUMENT_COUNT * 100
        print(f"Shard {shard}: {count:5d} documents ({percentage:5.1f}%)")


def main():
    print("=" * 58)
    print("Lab 11.2 V2: Shard Key Hotspot Detection")
    print("=" * 58)

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)

    try:
        client.admin.command("ping")
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Do not overwrite this version's previous results.
        existing = collection.count_documents({"lab_tag": LAB_TAG})
        if existing:
            print(
                f"Found {existing} existing V2 documents. "
                "Stopping to avoid duplicate inserts."
            )
            print("Existing data has been left unchanged.")
            return

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        docs = []

        for i in range(DOCUMENT_COUNT):
            timestamp = start + timedelta(seconds=i)
            docs.append({
                "lab_tag": LAB_TAG,
                "sequence": i,
                "ts": timestamp,
                "hashed_ts": str(int(timestamp.timestamp())),
            })

        collection.insert_many(docs)
        print(f"\nInserted {len(docs)} documents into {DATABASE_NAME}.{COLLECTION_NAME}")

        # Simulation A: range shard key with increasing timestamps.
        # New writes go to the highest-key range in this simplified model.
        monotonic_buckets = [0] * SHARD_COUNT
        monotonic_buckets[-1] = DOCUMENT_COUNT

        # Simulation B: hashed timestamps distribute across buckets.
        hashed_buckets = [0] * SHARD_COUNT
        for doc in docs:
            bucket = hash_bucket(doc["hashed_ts"])
            hashed_buckets[bucket] += 1

        print_distribution("Monotonic timestamp (range-key simulation):",
                           monotonic_buckets)
        print_distribution("Hashed timestamp (hash-bucket simulation):",
                           hashed_buckets)

        print("\nConclusion:")
        print(
            "The range-key model concentrates new writes on the highest-key "
            "shard, while hashing spreads values across simulated buckets."
        )
        print(
            "These are simulated bucket counts, not measurements from "
            "actual MongoDB shards."
        )
        print("\nLab 11.2 V2 Complete")

    except PyMongoError as error:
        print(f"\nMongoDB error: {error}")
        print("Check that MongoDB is running at localhost:27017.")

    finally:
        client.close()


if __name__ == "__main__":
    main()