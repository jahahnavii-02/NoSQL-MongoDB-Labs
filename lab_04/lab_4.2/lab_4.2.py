from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database and collection
db = client["product_inventory"]

# Drop the old collection if it exists
if "inventory" in db.list_collection_names():
    db.inventory.drop()

inventory = db["inventory"]

print("Connected to MongoDB successfully.")
print("Database: product_inventory")
print("Collection: inventory")

# Insert sample products
products = [
    {
        "sku": "A",
        "name": "Product A",
        "price": 50,
        "stock": 20,
        "is_active": True
    },
    {
        "sku": "B",
        "name": "Product B",
        "price": 75,
        "stock": 30,
        "is_active": True
    },
    {
        "sku": "C",
        "name": "Product C",
        "price": 100,
        "stock": 40,
        "is_active": True
    },
    {
        "sku": "D",
        "name": "Product D",
        "price": 125,
        "stock": 25,
        "is_active": True
    },
    {
        "sku": "E",
        "name": "Product E",
        "price": 150,
        "stock": 15,
        "is_active": True
    }
]

result = inventory.insert_many(products)

print(f"Inserted {len(result.inserted_ids)} products successfully.")

print("\n--- Initial Inventory ---")
for product in inventory.find().sort("sku", 1):
    print(product)

    # Upsert function
def upsert_product(sku, price):
    result = inventory.update_one(
        {"sku": sku},
        {
            "$set": {
                "price": price
            },
            "$setOnInsert": {
                "sku": sku,
                "name": f"Product {sku}",
                "stock": 0,
                "is_active": True
            }
        },
        upsert=True
    )

    if result.upserted_id is not None:
        print(f"\nNew product inserted with SKU: {sku}")
    elif result.modified_count > 0:
        print(f"\nPrice updated for SKU: {sku}")
    else:
        print(f"\nNo changes made for SKU: {sku}")


# Test upsert with an existing SKU
upsert_product("A", 60)

# Test upsert with a new SKU
upsert_product("F", 200)

print("\n--- Inventory After Upsert ---")
for product in inventory.find().sort("sku", 1):
    print(product)

    from pymongo import UpdateOne

# Perform 5 bulk update operations
bulk_operations = [
    UpdateOne(
        {"sku": "A"},
        {"$inc": {"stock": 10}}
    ),
    UpdateOne(
        {"sku": "B"},
        {"$inc": {"stock": 10}}
    ),
    UpdateOne(
        {"sku": "C"},
        {"$inc": {"stock": 10}}
    ),
    UpdateOne(
        {"sku": "D"},
        {"$set": {"is_active": False}}
    ),
    UpdateOne(
        {"sku": "E"},
        {"$set": {"is_active": False}}
    )
]

bulk_result = inventory.bulk_write(bulk_operations)

print("\n--- Bulk Write Result ---")
print(f"Matched documents: {bulk_result.matched_count}")
print(f"Modified documents: {bulk_result.modified_count}")
print(f"Upserted documents: {bulk_result.upserted_count}")

print("\n--- Inventory After Bulk Write ---")
for product in inventory.find().sort("sku", 1):
    print(product)

    # Export inventory to JSON
from bson.json_util import dumps

all_products = list(inventory.find())

with open("inventory.json", "w", encoding="utf-8") as file:
    file.write(dumps(all_products, indent=4))

print("\nInventory exported to inventory.json successfully.")

# Close MongoDB connection
client.close()