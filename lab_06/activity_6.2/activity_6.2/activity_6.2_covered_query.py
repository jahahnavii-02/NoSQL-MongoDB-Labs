import os
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_strategy_lab"]
users = db["users"]

print("=" * 60)
print("LAB 6.2 - COVERED QUERY")
print("=" * 60)

# Create an index containing all fields needed
# by the query and projection.
users.create_index(
    [
        ("department", 1),
        ("age", 1),
        ("email", 1)
    ],
    name="covered_query_idx"
)

print("\nCovered-query index created.")

# ---------------------------------------------------------
# Covered query
# ---------------------------------------------------------

query = {
    "department": "Engineering",
    "age": {
        "$gte": 20,
        "$lte": 30
    }
}

projection = {
    "_id": 0,
    "email": 1,
    "department": 1,
    "age": 1
}

cursor = users.find(
    query,
    projection
)

# ---------------------------------------------------------
# Explain
# ---------------------------------------------------------

result = cursor.explain()

execution = result["executionStats"]

print("\n" + "=" * 60)
print("COVERED QUERY EXPLAIN RESULT")
print("=" * 60)

print(
    "Documents examined:",
    execution["totalDocsExamined"]
)

print(
    "Keys examined:",
    execution["totalKeysExamined"]
)

print(
    "Documents returned:",
    execution["nReturned"]
)

print("\nWinning plan:")
print(result["queryPlanner"]["winningPlan"])

# ---------------------------------------------------------
# Verify whether FETCH exists
# ---------------------------------------------------------

def contains_fetch(plan):

    if plan.get("stage") == "FETCH":
        return True

    if "inputStage" in plan:
        if contains_fetch(plan["inputStage"]):
            return True

    if "inputStages" in plan:
        for stage in plan["inputStages"]:
            if contains_fetch(stage):
                return True

    return False


has_fetch = contains_fetch(
    result["queryPlanner"]["winningPlan"]
)

print("\n" + "=" * 60)

if has_fetch:
    print("FETCH stage present.")
    print("Covered query was NOT achieved.")
else:
    print("FETCH stage absent.")
    print("Covered query achieved successfully.")

print("=" * 60)

client.close()