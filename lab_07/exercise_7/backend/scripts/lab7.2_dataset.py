from pymongo import MongoClient
from datetime import datetime
import random
import string
import time


# --------------------------------
# MongoDB connection
# --------------------------------

client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000
)

db = client["cti_platform"]
collection = db["working_set_test"]


# --------------------------------
# Clear previous experiment data
# --------------------------------

print("Removing previous working-set data...")

collection.drop()


# --------------------------------
# Generate approximately 2 KB text
# --------------------------------

def generate_text(length=1700):
    return ''.join(
        random.choices(
            string.ascii_letters + string.digits + " ",
            k=length
        )
    )


# --------------------------------
# Generate documents
# --------------------------------

TOTAL_DOCUMENTS = 100000
BATCH_SIZE = 1000

documents = []

start_time = time.time()

print("\nStarting insertion...")
print(f"Target documents: {TOTAL_DOCUMENTS}")


for i in range(TOTAL_DOCUMENTS):

    document = {
        "report_id": i,

        "title": f"Annual Threat Report {i}",

        "category": random.choice([
            "Ransomware",
            "Malware",
            "Phishing",
            "Vulnerability",
            "DDoS"
        ]),

        "severity": random.choice([
            "Low",
            "Medium",
            "High",
            "Critical"
        ]),

        "description": generate_text(1700),

        "source": "Cyber Threat Intelligence Database",

        "year": random.randint(2020, 2026),

        "created_at": datetime.now()
    }

    documents.append(document)

    if len(documents) == BATCH_SIZE:

        collection.insert_many(
            documents,
            ordered=False
        )

        documents = []

        if (i + 1) % 10000 == 0:
            print(
                f"Inserted {i + 1:,} documents..."
            )


# Insert any remaining documents

if documents:
    collection.insert_many(
        documents,
        ordered=False
    )


# --------------------------------
# Final statistics
# --------------------------------

elapsed = time.time() - start_time

count = collection.count_documents({})

print("\n===================================")
print("LAB 7.2 DATASET CREATED")
print("===================================")

print(
    f"Documents inserted: {count:,}"
)

print(
    f"Insertion time: {elapsed:.2f} seconds"
)


# --------------------------------
# MongoDB collection statistics
# --------------------------------

stats = db.command(
    "collStats",
    "working_set_test"
)

print("\nCollection statistics:")

print(
    f"Storage size: "
    f"{stats.get('storageSize', 0):,} bytes"
)

print(
    f"Data size: "
    f"{stats.get('size', 0):,} bytes"
)

print(
    f"Total collection size: "
    f"{stats.get('totalSize', 0):,} bytes"
)


print("\nLab 7.2 dataset creation completed.")