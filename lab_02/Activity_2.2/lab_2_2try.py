"""
Lab 2.2 Try - Bookstore Price Update
Increase price by 10% for books published before 2010.
"""

from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://127.0.0.1:27017/")

db = client["bookstore"]
col = db["books"]

# -------------------------------------------------
# BOOK DATA
# -------------------------------------------------

BOOKS = [
    {
        "title": "The Pragmatic Programmer",
        "author": "David Thomas & Andrew Hunt",
        "year": 2019,
        "genre": "Software Engineering",
        "price": 49.99,
        "isbn": "978-0135957059",
        "tags": ["programming", "career", "best-practices"],
        "publisher": {
            "name": "Addison-Wesley",
            "location": "Boston"
        }
    },
    {
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "year": 2017,
        "genre": "Databases",
        "price": 45.99,
        "isbn": "978-1449373320",
        "tags": ["databases", "distributed-systems", "architecture"],
        "publisher": {
            "name": "O'Reilly Media",
            "location": "Sebastopol"
        }
    },
    {
        "title": "Deep Learning",
        "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
        "year": 2016,
        "genre": "Machine Learning",
        "price": 72.00,
        "isbn": "978-0262035613",
        "tags": ["AI", "neural-networks", "theory"],
        "publisher": {
            "name": "MIT Press",
            "location": "Cambridge"
        }
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "year": 2008,
        "genre": "Software Engineering",
        "price": 39.99,
        "isbn": "978-0132350884",
        "tags": ["programming", "software-quality", "best-practices"],
        "publisher": {
            "name": "Prentice Hall",
            "location": "Boston"
        }
    },
    {
        "title": "Hands-On Machine Learning",
        "author": "Aurelien Geron",
        "year": 2022,
        "genre": "Machine Learning",
        "price": 59.99,
        "isbn": "978-1098125974",
        "tags": ["AI", "scikit-learn", "tensorflow", "practical"],
        "publisher": {
            "name": "O'Reilly Media",
            "location": "Sebastopol"
        }
    }
]

# -------------------------------------------------
# CREATE
# -------------------------------------------------

print("=== Lab 2.2 Try - Price Update ===")
print("=" * 55)

print("\n=== CREATE: Inserting 5 books ===")

# Start fresh every time
col.delete_many({})

insert_result = col.insert_many(BOOKS)

print(f"[OK] Inserted {len(insert_result.inserted_ids)} books")

# -------------------------------------------------
# READ: Books before 2010
# -------------------------------------------------

print("\n=== READ: Books published before 2010 ===")

old_books = col.find(
    {"year": {"$lt": 2010}},
    {"title": 1, "year": 1, "price": 1, "_id": 0}
)

for book in old_books:
    print(
        f"  {book['title']:<40} "
        f"({book['year']}) - ${book['price']:.2f}"
    )

# -------------------------------------------------
# UPDATE: Increase price by 10%
# -------------------------------------------------

print("\n=== UPDATE: 10% price increase for books before 2010 ===")

before = {
    b["title"]: b["price"]
    for b in col.find(
        {"year": {"$lt": 2010}},
        {"title": 1, "price": 1, "_id": 0}
    )
}

update_result = col.update_many(
    {"year": {"$lt": 2010}},
    [
        {
            "$set": {
                "price": {
                    "$round": [
                        {"$multiply": ["$price", 1.10]},
                        2
                    ]
                }
            }
        }
    ]
)

print(f"[OK] Updated {update_result.modified_count} book(s)")

after = {
    b["title"]: b["price"]
    for b in col.find(
        {"year": {"$lt": 2010}},
        {"title": 1, "price": 1, "_id": 0}
    )
}

for title, old_price in before.items():
    print(
        f"  {title:<40} "
        f"${old_price:.2f} -> ${after[title]:.2f}"
    )

# -------------------------------------------------
# VERIFY
# -------------------------------------------------

print("\n=== VERIFY: Final Collection ===")

print(f"Remaining books: {col.count_documents({})}")

for book in col.find({}, {"title": 1, "price": 1, "_id": 0}):
    print(f"  {book['title']:<40} ${book['price']:.2f}")

# -------------------------------------------------
# COMPLETE
# -------------------------------------------------

print("\n" + "=" * 55)
print("Lab 2.2 Try Complete")
print("=" * 55)

client.close()