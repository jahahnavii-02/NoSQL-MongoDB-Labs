import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "lab15" / "lab15.1-multi-tenant-api" / ".env"
load_dotenv(ENV_FILE)

client = MongoClient(
    os.environ["MONGO_URI"],
    serverSelectionTimeoutMS=5000
)

db = client["tasktracker_migration"]
source = db["tasks"]

TENANTS = [f"tenant_{i:03d}" for i in range(1, 6)]

try:
    client.admin.command("ping")

    source_count = source.count_documents({})
    print("Source documents:", source_count)

    if source_count != 500:
        raise RuntimeError(
            "Expected 500 source documents. Migration stopped."
        )

    total_migrated = 0

    for tenant_id in TENANTS:
        collection_name = f"tasks_tenant_{tenant_id}"
        destination = db[collection_name]

        # Prevent accidental duplicate migration
        if collection_name in db.list_collection_names():
            existing = destination.count_documents({})
            if existing:
                raise RuntimeError(
                    f"{collection_name} already contains "
                    f"{existing} documents. Stopping."
                )

        tenant_tasks = list(
            source.find({"tenant_id": tenant_id})
        )

        if len(tenant_tasks) != 100:
            raise RuntimeError(
                f"Unexpected task count for {tenant_id}"
            )

        if tenant_tasks:
            destination.insert_many(tenant_tasks)

        destination.create_index(
            [("created_at", DESCENDING)],
            name="created_at"
        )

        destination.create_index(
            [("owner_id", ASCENDING)],
            name="owner_id"
        )

        migrated_count = destination.count_documents({})

        print(
            f"{tenant_id}: "
            f"{migrated_count} documents migrated"
        )

        total_migrated += migrated_count

    print("\n========== MIGRATION SUMMARY ==========")
    print("Source documents:", source_count)
    print("Migrated documents:", total_migrated)

    print(
        "Source preserved:",
        source.count_documents({}) == source_count
    )

    print(
        "Migration successful:",
        total_migrated == source_count
    )

finally:
    client.close()