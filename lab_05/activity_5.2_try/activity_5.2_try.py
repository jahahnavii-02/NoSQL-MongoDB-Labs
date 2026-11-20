from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient(
    os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
)

db = client["sales_lookup_lab"]

orders = db["orders"]

print("=" * 60)
print("ACTIVITY 5.2 - TRY IT YOURSELF")
print("$lookup WITH PIPELINE SUB-EXPRESSION")
print("=" * 60)

# ---------------------------------------------------------
# $LOOKUP WITH PIPELINE
# Filter products on the foreign side
# ---------------------------------------------------------

lookup_pipeline = [
    {
        "$lookup": {
            "from": "products",
            "let": {
                "order_product_id": "$product_id"
            },
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {
                                    "$eq": [
                                        "$product_id",
                                        "$$order_product_id"
                                    ]
                                },
                                {
                                    "$eq": [
                                        "$category",
                                        "Electronics"
                                    ]
                                }
                            ]
                        }
                    }
                }
            ],
            "as": "product_info"
        }
    },
    {
        "$unwind": "$product_info"
    },
    {
        "$project": {
            "_id": 0,
            "order_date": 1,
            "customer": 1,
            "product_name": "$product_info.name",
            "category": "$product_info.category",
            "quantity": 1,
            "total": {
                "$multiply": [
                    "$quantity",
                    "$product_info.base_price"
                ]
            }
        }
    },
    {
        "$sort": {
            "order_date": 1
        }
    }
]

filtered_results = list(orders.aggregate(lookup_pipeline))

print("\nORDERS FOR ELECTRONICS PRODUCTS")
print("-" * 60)

for document in filtered_results:
    print(document)

print("\n" + "=" * 60)
print("TRY IT YOURSELF COMPLETED")
print("=" * 60)

client.close()