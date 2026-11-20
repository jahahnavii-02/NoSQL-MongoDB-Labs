from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database and collection
db = client["product_inventory"]
inventory = db["inventory_import"]

print("Connected to MongoDB successfully.")
print("Database: product_inventory")
print("Collection: inventory_import")

# Data to be imported
products = [
    {
        "sku": "A",
        "name": "Product A",
        "price": 60,
        "stock": 30,
        "is_active": True
    },
    {
        "sku": "B",
        "name": "Product B",
        "price": 75,
        "stock": 40,
        "is_active": True
    },
    {
        "sku": "C",
        "name": "Product C",
        "price": 100,
        "stock": 50,
        "is_active": True
    },
    {
        "sku": "D",
        "name": "Product D",
        "price": 125,
        "stock": 25,
        "is_active": False
    },
    {
        "sku": "E",
        "name": "Product E",
        "price": 150,
        "stock": 15,
        "is_active": False
    }
]

print(f"\nPrepared {len(products)} products for import.")

from pymongo import UpdateOne

# Create idempotent bulk operations
bulk_operations = []

for product in products:
    bulk_operations.append(
        UpdateOne(
            {"sku": product["sku"]},
            {"$set": product},
            upsert=True
        )
    )

# Perform the bulk import
result = inventory.bulk_write(bulk_operations)

print("\n--- First Bulk Import ---")
print(f"Matched documents: {result.matched_count}")
print(f"Modified documents: {result.modified_count}")
print(f"Upserted documents: {result.upserted_count}")
# Run the same import again to demonstrate idempotency
result_second = inventory.bulk_write(bulk_operations)

print("\n--- Second Bulk Import ---")
print(f"Matched documents: {result_second.matched_count}")
print(f"Modified documents: {result_second.modified_count}")
print(f"Upserted documents: {result_second.upserted_count}")

print("\n--- Final Inventory ---")

for product in inventory.find().sort("sku", 1):
    print(product)


# Export imported data to JSON
from bson.json_util import dumps

all_products = list(inventory.find())

with open("inventory_import.json", "w", encoding="utf-8") as file:
    file.write(dumps(all_products, indent=4))

print("\nInventory exported to inventory_import.json successfully.")


# Close MongoDB connection
client.close()