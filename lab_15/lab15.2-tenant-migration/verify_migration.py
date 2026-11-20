import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "lab15" / "lab15.1-multi-tenant-api" / ".env"
load_dotenv(ENV_FILE)

client = MongoClient(os.environ["MONGO_URI"])
db = client["tasktracker_migration"]

TENANTS = [f"tenant_{i:03d}" for i in range(1, 6)]

try:
    source = db["tasks"]

    print("========== MIGRATION VALIDATION ==========")

    source_count = source.count_documents({})
    migrated_total = 0
    total_leakage = 0

    for tenant_id in TENANTS:
        collection = db[f"tasks_tenant_{tenant_id}"]

        count = collection.count_documents({})
        wrong_tenant = collection.count_documents({
            "tenant_id": {"$ne": tenant_id}
        })

        source_tenant_count = source.count_documents({
            "tenant_id": tenant_id
        })

        migrated_total += count
        total_leakage += wrong_tenant

        print(f"\n{tenant_id}")
        print("Source count:", source_tenant_count)
        print("Migrated count:", count)
        print("Cross-tenant records:", wrong_tenant)
        print(
            "Count match:",
            source_tenant_count == count
        )

    print("\n========== FINAL VALIDATION ==========")
    print("Original documents:", source_count)
    print("Migrated documents:", migrated_total)
    print("Missing documents:", source_count - migrated_total)
    print("Cross-tenant leakage:", total_leakage)
    print("Source preserved:", source.count_documents({}) == 500)

finally:
    client.close()