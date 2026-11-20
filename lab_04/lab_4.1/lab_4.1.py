from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database
db = client["product_inventory"]

# Remove old collection if it already exists
if "products" in db.list_collection_names():
    db.products.drop()

# Schema validation
validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "price", "stock", "tags"],
        "properties": {
            "name": {
                "bsonType": "string",
                "description": "Product name must be a string"
            },
            "price": {
                "bsonType": ["int", "long", "double", "decimal"],
                "minimum": 0.01,
                "description": "Price must be a positive number"
            },
            "stock": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Stock must be a non-negative integer"
            },
            "tags": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string"
                },
                "description": "Tags must be an array of strings"
            }
        }
    }
}

# Create products collection with validation
db.create_collection(
    "products",
    validator=validator,
    validationLevel="strict",
    validationAction="error"
)

products = db["products"]

print("Connected to MongoDB successfully.")
print("Database: product_inventory")
print("Collection: products")
print("Schema validation created successfully.")

# Insert sample products
product_data = [
    {
        "name": "Wireless Mouse",
        "price": 25,
        "stock": 50,
        "tags": ["electronics", "wireless"]
    },
    {
        "name": "Bluetooth Speaker",
        "price": 45,
        "stock": 30,
        "tags": ["electronics", "wireless", "premium"]
    },
    {
        "name": "USB Cable",
        "price": 20,
        "stock": 100,
        "tags": ["electronics", "accessories"]
    },
    {
        "name": "Laptop Stand",
        "price": 35,
        "stock": 0,
        "tags": ["office", "accessories"]
    },
    {
        "name": "Gaming Keyboard",
        "price": 75,
        "stock": 15,
        "tags": ["electronics", "gaming"]
    },
    {
        "name": "Premium Headphones",
        "price": 150,
        "stock": 10,
        "tags": ["electronics", "wireless", "premium"]
    },
    {
        "name": "Smart Watch",
        "price": 120,
        "stock": 0,
        "tags": ["electronics", "wearable", "premium"]
    },
    {
        "name": "Phone Charger",
        "price": 30,
        "stock": 40,
        "tags": ["electronics", "accessories"]
    },
    {
        "name": "Webcam",
        "price": 50,
        "stock": 20,
        "tags": ["electronics", "camera"]
    },
    {
        "name": "Desk Lamp",
        "price": 40,
        "stock": 0,
        "tags": ["home", "lighting"]
    },
    {
        "name": "Wireless Earbuds",
        "price": 90,
        "stock": 25,
        "tags": ["electronics", "wireless", "premium"]
    },
    {
        "name": "External SSD",
        "price": 180,
        "stock": 8,
        "tags": ["electronics", "storage", "premium"]
    }
]

result = products.insert_many(product_data)

print(f"Inserted {len(result.inserted_ids)} products successfully.")

# Comparison Operators

# 1. Products with price between 20 and 50
print("\n--- Products with price between 20 and 50 ---")

price_range_products = products.find({
    "price": {"$gte": 20, "$lte": 50}
})

for product in price_range_products:
    print(product)


# 2. Products that are out of stock
print("\n--- Out of Stock Products ---")

out_of_stock_products = products.find({
    "stock": {"$eq": 0}
})

for product in out_of_stock_products:
    print(product)

# Logical Operators

# 1. Products that are out of stock OR priced above 100
print("\n--- Out of Stock OR Price Above 100 ---")

logical_or_products = products.find({
    "$or": [
        {"stock": 0},
        {"price": {"$gt": 100}}
    ]
})

for product in logical_or_products:
    print(product)


# 2. Products that are in stock AND tagged as premium
print("\n--- In Stock AND Premium ---")

logical_and_products = products.find({
    "$and": [
        {"stock": {"$gt": 0}},
        {"tags": "premium"}
    ]
})

for product in logical_and_products:
    print(product)


# Close MongoDB connection
# Array Operators

# 1. Products having both 'electronics' and 'wireless' tags
print("\n--- Products with BOTH electronics AND wireless tags ---")

both_tags_products = products.find({
    "tags": {
        "$all": ["electronics", "wireless"]
    }
})

for product in both_tags_products:
    print(product)


# 2. Products with exactly 2 tags
print("\n--- Products with exactly 2 tags ---")

exactly_two_tags_products = products.find({
    "tags": {
        "$size": 2
    }
})

for product in exactly_two_tags_products:
    print(product)


# Close MongoDB connection
# Pagination

def get_products(page, items_per_page):
    skip_count = (page - 1) * items_per_page

    return products.find().sort("name", 1).skip(skip_count).limit(items_per_page)


print("\n--- Pagination: Page 1 ---")

page_1_products = get_products(1, 5)

for product in page_1_products:
    print(product)


print("\n--- Pagination: Page 2 ---")

page_2_products = get_products(2, 5)

for product in page_2_products:
    print(product)


# Export products collection to JSON
from bson.json_util import dumps

all_products = list(products.find())

with open("products.json", "w", encoding="utf-8") as file:
    file.write(dumps(all_products, indent=4))

print("\nProducts exported to products.json successfully.")

# Close MongoDB connection
client.close()