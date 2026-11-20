import os
import random
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))

db = client["index_lab"]
products = db["products"]

# Start clean
products.drop()

categories = [
    "Electronics",
    "Clothing",
    "Books",
    "Home",
    "Sports"
]

tag_pool = [
    "new",
    "sale",
    "premium",
    "popular",
    "organic",
    "limited",
    "budget",
    "featured",
    "trending",
    "best-seller"
]

documents = []

# Generate 50,000 products
for i in range(1, 50001):

    product = {
        "name": f"Product {i}",
        "category": random.choice(categories),
        "price": round(random.uniform(100, 100000), 2),
        "rating": round(random.uniform(1, 5), 1),
        "stock": random.randint(0, 1000),
        "tags": random.sample(tag_pool, random.randint(1, 4))
    }

    documents.append(product)

    # Insert in batches of 1,000
    if len(documents) == 1000:
        products.insert_many(documents)
        documents = []

# Insert remaining documents
if documents:
    products.insert_many(documents)

print("50,000 products inserted successfully.")
print("Collection:", products.name)
print("Document count:", products.count_documents({}))

client.close()