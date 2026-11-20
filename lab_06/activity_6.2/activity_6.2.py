import os
import time
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_strategy_lab"]
users = db["users"]

print("=" * 60)
print("LAB 6.2 - INDEX STRATEGY COMPARISON")
print("=" * 60)

# Start with a completely clean collection
users.drop()

print("\nCollection reset successfully.")

# Verify that only the default _id index exists
print("\nIndexes before insertion:")

for index in users.list_indexes():
    print(f"  {index['name']} -> {index['key']}")

# Generate 10,000 documents
departments = [
    "Engineering",
    "Sales",
    "Marketing",
    "HR"
]

documents = []

for i in range(1, 10001):
    documents.append({
        "name": f"User {i}",
        "email": f"user{i}@example.com",
        "age": 20 + (i % 50),
        "department": departments[i % 4],
        "salary": 40000 + (i * 10)
    })

# Measure insertion time
start_time = time.perf_counter()

users.insert_many(documents)

end_time = time.perf_counter()

insert_time = end_time - start_time

# Display results
print("\n--- NO SECONDARY INDEXES ---")

print(
    f"Documents inserted: {users.count_documents({})}"
)

print(
    f"Insertion time: {insert_time:.6f} seconds"
)

print("\nIndexes after insertion:")

for index in users.list_indexes():
    print(f"  {index['name']} -> {index['key']}")

client.close()