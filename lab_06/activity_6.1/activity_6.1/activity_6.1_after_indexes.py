import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_lab"]
products = db["products"]


def get_stage(plan):
    """
    Recursively find the important execution stage.
    """
    if "stage" in plan:
        if plan["stage"] in [
            "IXSCAN",
            "COLLSCAN",
            "TEXT_MATCH",
            "FETCH",
            "SORT"
        ]:
            return plan["stage"]

    if "inputStage" in plan:
        return get_stage(plan["inputStage"])

    if "inputStages" in plan:
        for stage in plan["inputStages"]:
            result = get_stage(stage)
            if result:
                return result

    if "shards" in plan:
        for shard in plan["shards"].values():
            result = get_stage(shard["winningPlan"])
            if result:
                return result

    return plan.get("stage", "UNKNOWN")


def show_explain(title, cursor):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    result = cursor.explain()

    execution = result["executionStats"]
    winning_plan = result["queryPlanner"]["winningPlan"]

    print("Stage:", get_stage(winning_plan))
    print(
        "Total documents examined:",
        execution["totalDocsExamined"]
    )
    print(
        "Total keys examined:",
        execution["totalKeysExamined"]
    )
    print(
        "Documents returned:",
        execution["nReturned"]
    )


# ---------------------------------------------------------
# Q1: Category + sort by price
# ---------------------------------------------------------

show_explain(
    "Q1 - Category = Electronics, sorted by price",

    products.find(
        {"category": "Electronics"}
    ).sort("price", 1)
)


# ---------------------------------------------------------
# Q2: Price range
# ---------------------------------------------------------

show_explain(
    "Q2 - Price between 10,000 and 50,000",

    products.find(
        {
            "price": {
                "$gte": 10000,
                "$lte": 50000
            }
        }
    )
)


# ---------------------------------------------------------
# Q3: Tag search
# ---------------------------------------------------------

show_explain(
    "Q3 - Products with tag 'premium'",

    products.find(
        {"tags": "premium"}
    )
)


# ---------------------------------------------------------
# Q4: Text search
# ---------------------------------------------------------

show_explain(
    "Q4 - Text search for '123'",

    products.find(
        {
            "$text": {
                "$search": "123"
            }
        }
    )
)


# ---------------------------------------------------------
# Q5: Rating + stock
# ---------------------------------------------------------

show_explain(
    "Q5 - Rating >= 4 and stock > 500",

    products.find(
        {
            "rating": {"$gte": 4},
            "stock": {"$gt": 500}
        }
    )
)


client.close()