import os
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_strategy_lab"]
users = db["users"]


def get_stage(plan):
    if "stage" in plan:
        return plan["stage"]

    if "inputStage" in plan:
        return get_stage(plan["inputStage"])

    if "inputStages" in plan:
        for stage in plan["inputStages"]:
            result = get_stage(stage)
            if result:
                return result

    return "UNKNOWN"


def run_query(title, cursor):

    result = cursor.explain()

    execution = result["executionStats"]
    winning_plan = result["queryPlanner"]["winningPlan"]

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print("Stage:", get_stage(winning_plan))
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


# =========================================================
# PART 1 - Five queries with all five indexes
# =========================================================

print("\n")
print("#" * 60)
print("PART 1 - ALL FIVE INDEXES")
print("#" * 60)

run_query(
    "Q1 - Email lookup",
    users.find({
        "email": "user5000@example.com"
    })
)

run_query(
    "Q2 - Department lookup",
    users.find({
        "department": "Engineering"
    })
)

run_query(
    "Q3 - Age range",
    users.find({
        "age": {
            "$gte": 25,
            "$lte": 35
        }
    })
)

run_query(
    "Q4 - Salary greater than 80000",
    users.find({
        "salary": {
            "$gt": 80000
        }
    })
)

run_query(
    "Q5 - Name lookup",
    users.find({
        "name": "User 15000"
    })
)


# =========================================================
# PART 2 - Keep only the critical email index
# =========================================================

print("\n")
print("#" * 60)
print("DROPPING NON-CRITICAL INDEXES")
print("#" * 60)

indexes_to_drop = [
    "name_idx",
    "age_idx",
    "department_idx",
    "salary_idx"
]

for index_name in indexes_to_drop:
    users.drop_index(index_name)
    print(f"Dropped: {index_name}")


print("\nRemaining indexes:")

for index in users.list_indexes():
    print(
        f"  {index['name']} -> {index['key']}"
    )


# =========================================================
# PART 3 - Same five queries with only email index
# =========================================================

print("\n")
print("#" * 60)
print("PART 2 - ONLY EMAIL INDEX")
print("#" * 60)

run_query(
    "Q1 - Email lookup",
    users.find({
        "email": "user5000@example.com"
    })
)

run_query(
    "Q2 - Department lookup",
    users.find({
        "department": "Engineering"
    })
)

run_query(
    "Q3 - Age range",
    users.find({
        "age": {
            "$gte": 25,
            "$lte": 35
        }
    })
)

run_query(
    "Q4 - Salary greater than 80000",
    users.find({
        "salary": {
            "$gt": 80000
        }
    })
)

run_query(
    "Q5 - Name lookup",
    users.find({
        "name": "User 15000"
    })
)


client.close()