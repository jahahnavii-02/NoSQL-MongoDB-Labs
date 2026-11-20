import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

# Load existing Lab 15.1 connection configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "lab15" / "lab15.1-multi-tenant-api" / ".env"

load_dotenv(ENV_FILE)

client = MongoClient(
    os.environ["MONGO_URI"],
    serverSelectionTimeoutMS=5000
)

db = client["tasktracker_migration"]
tasks = db["tasks"]

TENANTS = [f"tenant_{i:03d}" for i in range(1, 6)]
TASKS_PER_TENANT = 100

try:
    client.admin.command("ping")
    print("MongoDB connection successful.")

    # Safety check: never overwrite existing experiment data
    if "tasks" in db.list_collection_names():
        existing_count = tasks.count_documents({})

        if existing_count > 0:
            print(f"Existing dataset found: {existing_count} documents.")
            print("Stopping to protect existing experiment data.")
            raise SystemExit(1)

    if "tasks" not in db.list_collection_names():
        db.create_collection("tasks")

    documents = []

    base_time = datetime.now(timezone.utc)

    for tenant_id in TENANTS:
        for number in range(1, TASKS_PER_TENANT + 1):

            documents.append({
                "tenant_id": tenant_id,
                "owner_id": f"user_{tenant_id}_01",
                "description": (
                    f"Task {number} for {tenant_id}"
                ),
                "priority": ["low", "medium", "high"][
                    (number - 1) % 3
                ],
                "status": ["open", "in_progress", "completed"][
                    (number - 1) % 3
                ],
                "created_at": (
                    base_time - timedelta(minutes=number)
                )
            })

    result = tasks.insert_many(documents)

    # Create indexes matching the shared-collection design
    tasks.create_index(
        [("tenant_id", ASCENDING),
         ("created_at", DESCENDING)],
        name="tenant_created_at"
    )

    tasks.create_index(
        [("tenant_id", ASCENDING),
         ("owner_id", ASCENDING)],
        name="tenant_owner"
    )

    print("\n========== DATASET VERIFICATION ==========")

    print("Inserted documents:", len(result.inserted_ids))
    print("Total documents:", tasks.count_documents({}))

    for tenant_id in TENANTS:
        count = tasks.count_documents({
            "tenant_id": tenant_id
        })
        print(f"{tenant_id}: {count} tasks")

    print("\nDataset preparation completed.")

finally:
    client.close()