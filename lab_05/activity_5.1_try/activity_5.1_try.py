from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient(
    os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
)

db = client["sales_analytics_lab"]
orders = db["orders"]

print("=" * 60)
print("ACTIVITY 5.1 - TRY IT YOURSELF")
print("ORDER VALUE BUCKET ANALYSIS")
print("=" * 60)

# ---------------------------------------------------------
# CALCULATE TOTAL ORDER VALUE AND CATEGORIZE USING $BUCKET
# ---------------------------------------------------------

bucket_pipeline = [
    {
        "$project": {
            "customer": 1,
            "product": 1,
            "total_order_value": {
                "$multiply": ["$quantity", "$unit_price"]
            }
        }
    },
    {
        "$bucket": {
            "groupBy": "$total_order_value",
            "boundaries": [0, 50, 200, float("inf")],
            "default": "Other",
            "output": {
                "number_of_orders": {
                    "$sum": 1
                },
                "total_revenue": {
                    "$sum": "$total_order_value"
                },
                "orders": {
                    "$push": {
                        "customer": "$customer",
                        "product": "$product",
                        "total_order_value": "$total_order_value"
                    }
                }
            }
        }
    }
]

bucket_results = list(orders.aggregate(bucket_pipeline))

print("\nORDER VALUE CATEGORIES")
print("-" * 60)

for document in bucket_results:

    bucket = document["_id"]

    if bucket == 0:
        category = "Small (< $50)"
    elif bucket == 50:
        category = "Medium ($50 - $200)"
    elif bucket == 200:
        category = "Large (> $200)"
    else:
        category = "Other"

    print("\nCategory:", category)
    print("Number of orders:", document["number_of_orders"])
    print("Total revenue:", document["total_revenue"])

    print("Orders:")
    for order in document["orders"]:
        print(
            " ",
            order["customer"],
            "-",
            order["product"],
            "- $",
            order["total_order_value"]
        )

print("\n" + "=" * 60)
print("TRY IT YOURSELF COMPLETED")
print("=" * 60)

client.close()