import os
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_lab"]
products = db["products"]


def show_explain(title, cursor):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    result = cursor.explain()

    execution = result["executionStats"]
    winning_plan = result["queryPlanner"]["winningPlan"]

    print("Stage:", winning_plan.get("stage"))
    print("Total documents examined:",
          execution["totalDocsExamined"])
    print("Total keys examined:",
          execution["totalKeysExamined"])
    print("Documents returned:",
          execution["nReturned"])


# ---------------------------------------------------------
# Q1: Find products by category and sort by price
# ---------------------------------------------------------
show_explain(
    "Q1 - Category = Electronics, sorted by price",
    products.find(
        {"category": "Electronics"}
    ).sort("price", 1)
)


# ---------------------------------------------------------
# Q2: Find products within a price range
# ---------------------------------------------------------
show_explain(
    "Q2 - Price between 10,000 and 50,000",
    products.find(
        {"price": {"$gte": 10000, "$lte": 50000}}
    )
)


# ---------------------------------------------------------
# Q3: Find products containing a specific tag
# ---------------------------------------------------------
show_explain(
    "Q3 - Products with tag 'premium'",
    products.find(
        {"tags": "premium"}
    )
)


# ---------------------------------------------------------
# Q4: Search product name
# Baseline uses regex because $text requires a text index.
# ---------------------------------------------------------
show_explain(
    "Q4 - Product name search",
    products.find(
        {"name": {"$regex": "^Product 123"}}
    )
)


# ---------------------------------------------------------
# Q5: Find products by rating and stock
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