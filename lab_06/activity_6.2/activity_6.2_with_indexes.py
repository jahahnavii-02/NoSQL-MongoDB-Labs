import os
import time
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_strategy_lab"]
users = db["users"]

print("=" * 60)
print("LAB 6.2 - INSERT PERFORMANCE WITH 5 INDEXES")
print("=" * 60)

# ---------------------------------------------------------
# Verify existing documents
# ---------------------------------------------------------

print("\nExisting documents:", users.count_documents({}))

# ---------------------------------------------------------
# Create 5 indexes
# ---------------------------------------------------------

print("\nCreating 5 indexes...")

users.create_index(
    [("name", 1)],
    name="name_idx"
)

users.create_index(
    [("email", 1)],
    unique=True,
    name="email_idx"
)

users.create_index(
    [("age", 1)],
    name="age_idx"
)

users.create_index(
    [("department", 1)],
    name="department_idx"
)

users.create_index(
    [("salary", 1)],
    name="salary_idx"
)

print("5 indexes created successfully.")

# ---------------------------------------------------------
# Display indexes
# ---------------------------------------------------------

print("\nCurrent indexes:")

for index in users.list_indexes():
    print(
        f"  {index['name']} -> {index['key']}"
    )

# ---------------------------------------------------------
# Generate another 10,000 documents
# ---------------------------------------------------------

departments = [
    "Engineering",
    "Sales",
    "Marketing",
    "HR"
]

documents = []

for i in range(10001, 20001):

    documents.append({
        "name": f"User {i}",
        "email": f"user{i}@example.com",
        "age": 20 + (i % 50),
        "department": departments[i % 4],
        "salary": 40000 + (i * 10)
    })

# ---------------------------------------------------------
# Measure insertion time
# ---------------------------------------------------------

start_time = time.perf_counter()

users.insert_many(documents)

end_time = time.perf_counter()

indexed_insert_time = end_time - start_time

# ---------------------------------------------------------
# Calculate percentage slowdown
# ---------------------------------------------------------

baseline_time = 0.629731

slowdown = (
    (indexed_insert_time - baseline_time)
    / baseline_time
) * 100

# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\n--- WITH 5 SECONDARY INDEXES ---")

print(
    f"Documents inserted in this run: "
    f"{len(documents)}"
)

print(
    f"Total documents in collection: "
    f"{users.count_documents({})}"
)

print(
    f"Insertion time with 5 indexes: "
    f"{indexed_insert_time:.6f} seconds"
)

print(
    f"Percentage slowdown: "
    f"{slowdown:.2f}%"
)

client.close()