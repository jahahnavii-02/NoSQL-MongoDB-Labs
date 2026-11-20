from pymongo import MongoClient
from datetime import datetime
import os

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/"))

db = client["sales_analytics_lab"]
orders = db["orders"]

# Clear previous data so the experiment starts clean
orders.delete_many({})

# ---------------------------------------------------------
# INSERT AT LEAST 20 ORDERS
# ---------------------------------------------------------

order_documents = [
    {
        "customer": "Aarav",
        "product": "Laptop",
        "quantity": 1,
        "unit_price": 750,
        "order_date": datetime(2026, 1, 5),
        "status": "Completed"
    },
    {
        "customer": "Priya",
        "product": "Mouse",
        "quantity": 2,
        "unit_price": 25,
        "order_date": datetime(2026, 1, 12),
        "status": "Completed"
    },
    {
        "customer": "Rahul",
        "product": "Keyboard",
        "quantity": 1,
        "unit_price": 60,
        "order_date": datetime(2026, 1, 20),
        "status": "Pending"
    },
    {
        "customer": "Sneha",
        "product": "Monitor",
        "quantity": 2,
        "unit_price": 220,
        "order_date": datetime(2026, 1, 25),
        "status": "Completed"
    },
    {
        "customer": "Vikram",
        "product": "Headphones",
        "quantity": 1,
        "unit_price": 120,
        "order_date": datetime(2026, 2, 3),
        "status": "Shipped"
    },
    {
        "customer": "Aarav",
        "product": "Keyboard",
        "quantity": 2,
        "unit_price": 60,
        "order_date": datetime(2026, 2, 10),
        "status": "Completed"
    },
    {
        "customer": "Priya",
        "product": "Laptop",
        "quantity": 1,
        "unit_price": 800,
        "order_date": datetime(2026, 2, 15),
        "status": "Completed"
    },
    {
        "customer": "Rahul",
        "product": "Mouse",
        "quantity": 3,
        "unit_price": 25,
        "order_date": datetime(2026, 2, 22),
        "status": "Cancelled"
    },
    {
        "customer": "Sneha",
        "product": "Laptop",
        "quantity": 1,
        "unit_price": 780,
        "order_date": datetime(2026, 3, 2),
        "status": "Completed"
    },
    {
        "customer": "Vikram",
        "product": "Monitor",
        "quantity": 1,
        "unit_price": 250,
        "order_date": datetime(2026, 3, 8),
        "status": "Completed"
    },
    {
        "customer": "Aarav",
        "product": "Headphones",
        "quantity": 2,
        "unit_price": 110,
        "order_date": datetime(2026, 3, 14),
        "status": "Shipped"
    },
    {
        "customer": "Priya",
        "product": "Keyboard",
        "quantity": 2,
        "unit_price": 65,
        "order_date": datetime(2026, 3, 20),
        "status": "Completed"
    },
    {
        "customer": "Rahul",
        "product": "Laptop",
        "quantity": 1,
        "unit_price": 720,
        "order_date": datetime(2026, 4, 4),
        "status": "Completed"
    },
    {
        "customer": "Sneha",
        "product": "Mouse",
        "quantity": 4,
        "unit_price": 25,
        "order_date": datetime(2026, 4, 11),
        "status": "Pending"
    },
    {
        "customer": "Vikram",
        "product": "Keyboard",
        "quantity": 1,
        "unit_price": 70,
        "order_date": datetime(2026, 4, 18),
        "status": "Completed"
    },
    {
        "customer": "Aarav",
        "product": "Monitor",
        "quantity": 1,
        "unit_price": 230,
        "order_date": datetime(2026, 5, 3),
        "status": "Completed"
    },
    {
        "customer": "Priya",
        "product": "Headphones",
        "quantity": 2,
        "unit_price": 115,
        "order_date": datetime(2026, 5, 9),
        "status": "Shipped"
    },
    {
        "customer": "Rahul",
        "product": "Keyboard",
        "quantity": 3,
        "unit_price": 60,
        "order_date": datetime(2026, 5, 16),
        "status": "Completed"
    },
    {
        "customer": "Sneha",
        "product": "Monitor",
        "quantity": 2,
        "unit_price": 240,
        "order_date": datetime(2026, 5, 22),
        "status": "Completed"
    },
    {
        "customer": "Vikram",
        "product": "Laptop",
        "quantity": 1,
        "unit_price": 760,
        "order_date": datetime(2026, 6, 5),
        "status": "Completed"
    }
]

result = orders.insert_many(order_documents)

print("=" * 60)
print("ACTIVITY 5.1 - SALES ANALYTICS PIPELINE")
print("=" * 60)

print("\nInserted orders:", len(result.inserted_ids))

# ---------------------------------------------------------
# 1. MONTHLY REVENUE
# ---------------------------------------------------------

monthly_revenue_pipeline = [
    {
        "$group": {
            "_id": {
                "year": {"$year": "$order_date"},
                "month": {"$month": "$order_date"}
            },
            "monthly_revenue": {
                "$sum": {
                    "$multiply": ["$quantity", "$unit_price"]
                }
            }
        }
    },
    {
        "$sort": {
            "_id.year": 1,
            "_id.month": 1
        }
    },
    {
        "$project": {
            "_id": 0,
            "year": "$_id.year",
            "month": "$_id.month",
            "monthly_revenue": 1
        }
    }
]

monthly_revenue = list(orders.aggregate(monthly_revenue_pipeline))

print("\n1. MONTHLY REVENUE")
print("-" * 60)

for document in monthly_revenue:
    print(document)

# ---------------------------------------------------------
# 2. TOP 3 CUSTOMERS BY TOTAL SPENDING
# ---------------------------------------------------------

top_customers_pipeline = [
    {
        "$project": {
            "customer": 1,
            "product": 1,
            "order_total": {
                "$multiply": ["$quantity", "$unit_price"]
            }
        }
    },
    {
        "$group": {
            "_id": "$customer",
            "total_spending": {"$sum": "$order_total"},
            "products_bought": {"$addToSet": "$product"}
        }
    },
    {
        "$sort": {
            "total_spending": -1
        }
    },
    {
        "$limit": 3
    },
    {
        "$project": {
            "_id": 0,
            "customer": "$_id",
            "total_spending": 1,
            "products_bought": 1
        }
    }
]

top_customers = list(orders.aggregate(top_customers_pipeline))

print("\n2. TOP 3 CUSTOMERS BY TOTAL SPENDING")
print("-" * 60)

for document in top_customers:
    print(document)

# ---------------------------------------------------------
# 3. AVERAGE ORDER VALUE PER STATUS
# ---------------------------------------------------------

average_order_pipeline = [
    {
        "$project": {
            "status": 1,
            "order_value": {
                "$multiply": ["$quantity", "$unit_price"]
            }
        }
    },
    {
        "$group": {
            "_id": "$status",
            "average_order_value": {
                "$avg": "$order_value"
            },
            "number_of_orders": {
                "$sum": 1
            }
        }
    },
    {
        "$sort": {
            "_id": 1
        }
    },
    {
        "$project": {
            "_id": 0,
            "status": "$_id",
            "average_order_value": 1,
            "number_of_orders": 1
        }
    }
]

average_orders = list(orders.aggregate(average_order_pipeline))

print("\n3. AVERAGE ORDER VALUE PER STATUS")
print("-" * 60)

for document in average_orders:
    print(document)

print("\n" + "=" * 60)
print("ACTIVITY 5.1 COMPLETED")
print("=" * 60)

client.close()