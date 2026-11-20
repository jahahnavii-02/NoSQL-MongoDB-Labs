"""
NoSQL Lab 11.2 - Real Shard Key Hotspot Detection
MongoDB 7.0 / two-shard cluster.

Run from project root:
    python .\lab11\lab_02_shard_key_hotspot.py

Connects to the existing mongos at localhost:27117.
Uses the lab11 database and only resets the two named experiment
collections. It does not reset the cluster or other lab data.
"""

from datetime import datetime, timedelta, timezone
from pprint import pprint
from pymongo import MongoClient, ASCENDING, HASHED
from pymongo.errors import PyMongoError
from bson import ObjectId
import sys


MONGOS_URI = "mongodb://localhost:27117/"
DB_NAME = "lab11"
HOTSPOT_NAME = "hotspot_data"
EVEN_NAME = "even_data"
DOCUMENT_COUNT = 10_000
BATCH_SIZE = 1_000


def section(title):
    print("\n" + "=" * 76)
    print(title)
    print("=" * 76)


def main():
    client = MongoClient(MONGOS_URI, serverSelectionTimeoutMS=5000)

    try:
        client.admin.command("ping")
        db = client[DB_NAME]

        section("1. Verify sharded cluster")
        print("MongoDB ping: OK")
        pprint(client.admin.command("listShards"))

        # Enable sharding for the experiment database.
        try:
            client.admin.command("enableSharding", DB_NAME)
        except PyMongoError as exc:
            if "already enabled" not in str(exc).lower():
                raise

        hotspot = db[HOTSPOT_NAME]
        even = db[EVEN_NAME]

        # These are dedicated lab collections. Drop only these two so the
        # experiment starts with exactly 10,000 new documents in each.
        for name in (HOTSPOT_NAME, EVEN_NAME):
            if name in db.list_collection_names():
                db[name].drop()
                print(f"Reset experiment collection: {DB_NAME}.{name}")

        section("2. Create actual shard-key configurations")
        client.admin.command(
            "shardCollection",
            f"{DB_NAME}.{HOTSPOT_NAME}",
            key={"ts": ASCENDING},
        )
        client.admin.command(
            "shardCollection",
            f"{DB_NAME}.{EVEN_NAME}",
            key={"user_id": HASHED},
        )

        print(f"{HOTSPOT_NAME}: shard key {{'ts': 1}}")
        print(f"{EVEN_NAME}: shard key {{'user_id': 'hashed'}}")

        section("3. Insert 10,000 documents into each collection")

        # Use increasing timestamps. Keep dates in a realistic, narrow,
        # increasing interval to demonstrate the monotonic-key workload.
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)

        for offset in range(0, DOCUMENT_COUNT, BATCH_SIZE):
            stop = min(offset + BATCH_SIZE, DOCUMENT_COUNT)

            timestamp_docs = [
                {
                    "_id": f"ts-{i:05d}",
                    "ts": start + timedelta(seconds=i),
                    "sequence": i,
                    "payload": "timestamp-hotspot-test",
                }
                for i in range(offset, stop)
            ]

            hashed_docs = [
                {
                    "_id": f"user-{i:05d}",
                    "user_id": ObjectId(),
                    "sequence": i,
                    "payload": "hashed-distribution-test",
                }
                for i in range(offset, stop)
            ]

            hotspot.insert_many(timestamp_docs, ordered=True)
            even.insert_many(hashed_docs, ordered=True)
            print(f"Inserted through document {stop}/{DOCUMENT_COUNT}")

        print(f"\n{HOTSPOT_NAME} count: {hotspot.count_documents({})}")
        print(f"{EVEN_NAME} count: {even.count_documents({})}")

        section("4. Collect actual per-shard statistics")
        for name in (HOTSPOT_NAME, EVEN_NAME):
            print(f"\n--- {DB_NAME}.{name} stats() ---")
            stats = db.command("collStats", name)
            print("Namespace:", stats.get("ns"))
            print("Total documents:", stats.get("count"))
            print("Total data size:", stats.get("size"))
            print("Total storage size:", stats.get("storageSize"))
            print("Shard breakdown:")
            pprint(stats.get("shards", {}))

        section("5. Explain timestamp range query")
        ts_query = {
            "ts": {
                "$gte": start,
                "$lt": start + timedelta(days=1),
            }
        }
        ts_explain = hotspot.find(ts_query).explain("executionStats")
        pprint(ts_explain)

        section("6. Explain hashed-key range query")
        # This is intentionally a range on the hashed shard-key field.
        # Hashed indexes are not efficient for range scans; the explain
        # output shows the actual routing and execution behavior.
        min_id = ObjectId("650000000000000000000000")
        max_id = ObjectId("660000000000000000000000")
        hashed_query = {"user_id": {"$gte": min_id, "$lt": max_id}}
        hashed_explain = even.find(hashed_query).explain("executionStats")
        pprint(hashed_explain)

        section("7. Experiment summary")
        print("Counts and query plans above are actual values returned by MongoDB.")
        print("Do not assume a fixed 9,500/500 or 5,000/5,000 distribution.")
        print("Shard distribution depends on chunks, balancing, and cluster state.")
        print("Compare the explain output for targeted shards, SHARD_MERGE,")
        print("and execution statistics. Hashed keys trade range efficiency")
        print("for more even distribution of key values.")

    except PyMongoError as exc:
        print("\nMongoDB operation failed:")
        print(exc)
        print(
            "\nCheck the existing mongos endpoint and cluster state. "
            "Do not reinitialize the cluster or delete Docker volumes."
        )
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()