from pymongo import MongoClient
import random
import time


# -----------------------------------------
# MongoDB connection
# -----------------------------------------

client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000
)

db = client["cti_platform"]
collection = db["working_set_test"]


# -----------------------------------------
# Configuration
# -----------------------------------------

TOTAL_DOCUMENTS = 100000
DURATION_SECONDS = 60
REPORT_INTERVAL = 10


# -----------------------------------------
# Get WiredTiger cache information
# -----------------------------------------

def get_cache_stats():

    stats = db.command("serverStatus")

    cache = stats["wiredTiger"]["cache"]

    return {
        "maximum": cache["maximum bytes configured"],
        "current": cache["bytes currently in the cache"],
        "pages_read": cache["pages read into cache"],
        "pages_written": cache["pages written from cache"]
    }


# -----------------------------------------
# Print cache status
# -----------------------------------------

def print_cache_status(label, stats):

    usage = (
        stats["current"] /
        stats["maximum"]
    ) * 100

    print("\n----------------------------------------")
    print(label)
    print("----------------------------------------")

    print(
        f"Maximum cache: "
        f"{stats['maximum']:,} bytes"
    )

    print(
        f"Current cache: "
        f"{stats['current']:,} bytes"
    )

    print(
        f"Cache utilization: "
        f"{usage:.2f}%"
    )

    print(
        f"Pages read into cache: "
        f"{stats['pages_read']:,}"
    )

    print(
        f"Pages written from cache: "
        f"{stats['pages_written']:,}"
    )


# -----------------------------------------
# Initial status
# -----------------------------------------

print("\n========================================")
print("LAB 7.2 RANDOM READ CACHE EXPERIMENT")
print("========================================")

print(
    f"Collection: {collection.name}"
)

print(
    f"Documents available: "
    f"{collection.count_documents({}):,}"
)


initial = get_cache_stats()

print_cache_status(
    "INITIAL CACHE STATUS",
    initial
)


# -----------------------------------------
# Random read experiment
# -----------------------------------------

print("\nStarting random reads...")
print(
    f"Duration: {DURATION_SECONDS} seconds"
)

start_time = time.time()
last_report = start_time
read_count = 0


while time.time() - start_time < DURATION_SECONDS:

    random_id = random.randint(
        0,
        TOTAL_DOCUMENTS - 1
    )

    # Random point read
    collection.find_one(
        {"report_id": random_id}
    )

    read_count += 1

    current_time = time.time()

    # Report every 10 seconds
    if current_time - last_report >= REPORT_INTERVAL:

        elapsed = current_time - start_time

        stats = get_cache_stats()

        print_cache_status(
            f"AFTER {elapsed:.0f} SECONDS",
            stats
        )

        print(
            f"Random reads performed: "
            f"{read_count:,}"
        )

        last_report = current_time


# -----------------------------------------
# Final status
# -----------------------------------------

final = get_cache_stats()

print("\n========================================")
print("RANDOM READ EXPERIMENT COMPLETED")
print("========================================")

print(
    f"Total random reads: "
    f"{read_count:,}"
)

print_cache_status(
    "FINAL CACHE STATUS",
    final
)

print("\nLab 7.2 cache experiment completed.")