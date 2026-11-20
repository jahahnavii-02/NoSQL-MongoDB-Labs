import os
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_lab"]
products = db["products"]


# ---------------------------------------------------------
# Run the representative queries multiple times
# ---------------------------------------------------------

for i in range(10):

    # Q1: Category + sort by price
    list(
        products.find(
            {"category": "Electronics"}
        ).sort("price", 1)
    )

    # Q2: Price range
    list(
        products.find(
            {
                "price": {
                    "$gte": 10000,
                    "$lte": 50000
                }
            }
        )
    )

    # Q3: Tag search
    list(
        products.find(
            {"tags": "premium"}
        )
    )

    # Q4: Text search
    list(
        products.find(
            {
                "$text": {
                    "$search": "123"
                }
            }
        )
    )

    # Q5: Rating + stock
    list(
        products.find(
            {
                "rating": {"$gte": 4},
                "stock": {"$gt": 500}
            }
        )
    )


print("Representative queries executed 10 times.")


# ---------------------------------------------------------
# Check actual index usage
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("INDEX USAGE STATISTICS")
print("=" * 60)

stats = products.aggregate([
    {
        "$indexStats": {}
    }
])

for stat in stats:

    index_name = stat["name"]
    operations = stat["accesses"]["ops"]

    print(
        f"Index: {index_name}"
    )

    print(
        f"Operations: {operations}"
    )

    print(
        f"Since: {stat['accesses']['since']}"
    )

    print("-" * 60)


client.close()