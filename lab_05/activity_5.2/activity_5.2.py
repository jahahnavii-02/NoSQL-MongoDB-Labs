from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient(
    os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
)

db = client["sales_lookup_lab"]

products = db["products"]
orders = db["orders"]

# Clear previous data
products.delete_many({})
orders.delete_many({})

# ---------------------------------------------------------
# INSERT PRODUCTS
# ---------------------------------------------------------

product_documents = [
    {
        "product_id": 101,
        "name": "Laptop",
        "category": "Electronics",
        "base_price": 750
    },
    {
        "product_id": 102,
        "name": "Mouse",
        "category": "Accessories",
        "base_price": 25
    },
    {
        "product_id": 103,
        "name": "Keyboard",
        "category": "Accessories",
        "base_price": 60
    },
    {
        "product_id": 104,
        "name": "Monitor",
        "category": "Electronics",
        "base_price": 220
    },
    {
        "product_id": 105,
        "name": "Headphones",
        "category": "Audio",
        "base_price": 120
    },
    {
        "product_id": 106,
        "name": "Webcam",
        "category": "Accessories",
        "base_price": 90
    }
]

products.insert_many(product_documents)

# ---------------------------------------------------------
# INSERT ORDERS
# ---------------------------------------------------------

order_documents = [
    {
        "customer": "Aarav",
        "product_id": 101,
        "quantity": 1,
        "order_date": "2026-01-05"
    },
    {
        "customer": "Priya",
        "product_id": 102,
        "quantity": 2,
        "order_date": "2026-01-12"
    },
    {
        "customer": "Rahul",
        "product_id": 103,
        "quantity": 1,
        "order_date": "2026-01-20"
    },
    {
        "customer": "Sneha",
        "product_id": 104,
        "quantity": 2,
        "order_date": "2026-01-25"
    },
    {
        "customer": "Vikram",
        "product_id": 105,
        "quantity": 1,
        "order_date": "2026-02-03"
    },
    {
        "customer": "Aarav",
        "product_id": 103,
        "quantity": 2,
        "order_date": "2026-02-10"
    },
    {
        "customer": "Priya",
        "product_id": 101,
        "quantity": 1,
        "order_date": "2026-02-15"
    },
    {
        "customer": "Rahul",
        "product_id": 102,
        "quantity": 3,
        "order_date": "2026-02-22"
    },
    {
        "customer": "Sneha",
        "product_id": 101,
        "quantity": 1,
        "order_date": "2026-03-02"
    },
    {
        "customer": "Vikram",
        "product_id": 104,
        "quantity": 1,
        "order_date": "2026-03-08"
    }
]

orders.insert_many(order_documents)

print("=" * 60)
print("ACTIVITY 5.2 - JOIN DATA WITH $lookup")
print("=" * 60)

print("\nProducts inserted:", products.count_documents({}))
print("Orders inserted:", orders.count_documents({}))

# ---------------------------------------------------------
# 1. $LOOKUP - JOIN ORDERS WITH PRODUCTS
# ---------------------------------------------------------

lookup_pipeline = [
    {
        "$lookup": {
            "from": "products",
            "localField": "product_id",
            "foreignField": "product_id",
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
            "product_name": "$product_info.name",
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

joined_orders = list(orders.aggregate(lookup_pipeline))

print("\n1. ORDERS JOINED WITH PRODUCTS")
print("-" * 60)

for document in joined_orders:
    print(document)

# ---------------------------------------------------------
# 2. FIND PRODUCTS THAT HAVE NEVER BEEN ORDERED
# ---------------------------------------------------------

unused_products_pipeline = [
    {
        "$lookup": {
            "from": "orders",
            "localField": "product_id",
            "foreignField": "product_id",
            "as": "orders"
        }
    },
    {
        "$match": {
            "orders": {
                "$size": 0
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "product_id": 1,
            "name": 1,
            "category": 1,
            "base_price": 1
        }
    }
]

unused_products = list(products.aggregate(unused_products_pipeline))

print("\n2. PRODUCTS THAT HAVE NEVER BEEN ORDERED")
print("-" * 60)

for document in unused_products:
    print(document)

print("\n" + "=" * 60)
print("ACTIVITY 5.2 COMPLETED")
print("=" * 60)

client.close()