import sys
import os

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from config.connection import get_db, reset_collection, banner


def main():

    banner("Lab 1.2: Try Yourself - E-Commerce")

    db = get_db("nosql_labs")

    col = reset_collection(
        "nosql_labs",
        "ecommerce_mapping"
    )

    ecommerce = [
        {
            "data_domain": "Product Catalog",
            "family": "Document",
            "database": "MongoDB",
            "reason": "Flexible product documents with different attributes"
        },
        {
            "data_domain": "Shopping Cart",
            "family": "Key-Value",
            "database": "Redis",
            "reason": "Fast access using customer or cart ID"
        },
        {
            "data_domain": "Order History",
            "family": "Wide-Column",
            "database": "Apache Cassandra",
            "reason": "High-volume writes and queries by customer and time"
        },
        {
            "data_domain": "Product Recommendations",
            "family": "Graph",
            "database": "Neo4j",
            "reason": "Efficiently represents relationships between users and products"
        }
    ]

    col.insert_many(ecommerce)

    print("E-Commerce data inserted successfully.")
    print("\n--- E-Commerce NoSQL Mapping ---")

    for item in col.find({}, {"_id": 0}):
        print(
            f"{item['data_domain']} -> "
            f"{item['family']} -> "
            f"{item['database']}"
        )
        print(f"Reason: {item['reason']}")
        print()

    banner("Lab 1.2 Try Yourself Complete")


if __name__ == "__main__":
    main()