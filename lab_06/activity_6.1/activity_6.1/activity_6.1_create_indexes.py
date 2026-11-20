import os
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_lab"]
products = db["products"]

# Create indexes
print("Creating indexes...")

# Q1: Category + sort by price
products.create_index(
    [("category", 1), ("price", 1)],
    name="category_price_idx"
)

# Q2: Price range
products.create_index(
    [("price", 1)],
    name="price_idx"
)

# Q3: Tag lookup
products.create_index(
    [("tags", 1)],
    name="tags_idx"
)

# Q4: Text search on product name
products.create_index(
    [("name", "text")],
    name="name_text_idx"
)

# Q5: Rating + stock
products.create_index(
    [("rating", 1), ("stock", 1)],
    name="rating_stock_idx"
)

print("\nIndexes created successfully!")

print("\nCurrent indexes:")
for index in products.list_indexes():
    print(
        f"  {index['name']} -> "
        f"{index['key']}"
    )

client.close()