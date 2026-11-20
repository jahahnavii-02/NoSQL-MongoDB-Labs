import os
import time
import statistics
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "lab15" / "lab15.1-multi-tenant-api" / ".env"
load_dotenv(ENV_FILE)

client = MongoClient(os.environ["MONGO_URI"])
db = client["tasktracker_migration"]

shared = db["tasks"]
TENANTS = [f"tenant_{i:03d}" for i in range(1, 6)]

ITERATIONS = 50


def measure(operation):
    timings = []

    for _ in range(ITERATIONS):
        start = time.perf_counter()
        operation()
        timings.append((time.perf_counter() - start) * 1000)

    return round(statistics.mean(timings), 4)


def shared_listing():
    list(
        shared.find({"tenant_id": TENANTS[0]}).sort(
            "created_at", -1
        )
    )


def separate_listing():
    list(
        db[f"tasks_tenant_{TENANTS[0]}"].find({}).sort(
            "created_at", -1
        )
    )


def shared_creation():
    document = {
        "tenant_id": TENANTS[0],
        "owner_id": "benchmark_user",
        "description": "Temporary benchmark task",
        "priority": "medium",
        "status": "open",
        "created_at": datetime.now(timezone.utc)
    }

    result = shared.insert_one(document)
    shared.delete_one({"_id": result.inserted_id})


def separate_creation():
    collection = db[f"tasks_tenant_{TENANTS[0]}"]

    document = {
        "tenant_id": TENANTS[0],
        "owner_id": "benchmark_user",
        "description": "Temporary benchmark task",
        "priority": "medium",
        "status": "open",
        "created_at": datetime.now(timezone.utc)
    }

    result = collection.insert_one(document)
    collection.delete_one({"_id": result.inserted_id})


def shared_analytics():
    list(shared.aggregate([
        {"$group": {
            "_id": "$tenant_id",
            "total_tasks": {"$sum": 1}
        }}
    ]))


def separate_analytics():
    for tenant_id in TENANTS:
        db[f"tasks_tenant_{tenant_id}"].count_documents({})


try:
    client.admin.command("ping")

    if shared.count_documents({}) != 500:
        raise RuntimeError("Shared dataset count is not 500.")

    print("Starting benchmark...")
    print("Iterations per operation:", ITERATIONS)

    # Warm-up
    shared_listing()
    separate_listing()
    shared_analytics()
    separate_analytics()

    results = []

    operations = [
        ("Task Listing", shared_listing, separate_listing),
        ("Task Creation", shared_creation, separate_creation),
        ("Cross-Tenant Analytics", shared_analytics, separate_analytics)
    ]

    for name, shared_op, separate_op in operations:
        shared_time = measure(shared_op)
        separate_time = measure(separate_op)

        results.append({
            "operation": name,
            "shared_ms": shared_time,
            "separate_ms": separate_time
        })

        print(f"\n{name}")
        print(f"Shared collection: {shared_time} ms")
        print(f"Separate collections: {separate_time} ms")

    # Save benchmark evidence
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "benchmark_results.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        import csv
        writer = csv.DictWriter(
            file,
            fieldnames=["operation", "shared_ms", "separate_ms"]
        )
        writer.writeheader()
        writer.writerows(results)

    print("\nBenchmark CSV saved:", output_file)

    print("Shared documents after benchmark:",
          shared.count_documents({}))

    print("Benchmark completed successfully.")

finally:
    client.close()