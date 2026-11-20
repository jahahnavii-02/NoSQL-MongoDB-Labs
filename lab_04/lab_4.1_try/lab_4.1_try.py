from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database and collection
db = client["product_inventory"]
products = db["products"]

print("Connected to MongoDB successfully.")
print("Database: product_inventory")
print("Collection: products")

# Regex Text Search

search_string = "wireless"

print(f"\n--- Products containing '{search_string}' in their name ---")

regex_products = products.find({
    "name": {
        "$regex": search_string,
        "$options": "i"
    }
})

for product in regex_products:
    print(product)

# Export products collection to JSON
from bson.json_util import dumps

all_products = list(products.find())

with open("products.json", "w", encoding="utf-8") as file:
    file.write(dumps(all_products, indent=4))

print("\nProducts exported to products.json successfully.")

# Close MongoDB connection
client.close()
