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
    banner("Lab 1.1: Try Yourself")

    db = get_db("nosql_labs")

    col = reset_collection(
        "nosql_labs",
        "mystery_products"
    )

    products = [
        {
            "name": "DynamoDB",
            "family": "Key-Value / Document",
            "hint": "AWS managed, single-digit ms latency, used for shopping carts"
        },
        {
            "name": "InfluxDB",
            "family": "Wide-Column / Time-Series",
            "hint": "Purpose-built for time-series data, SQL-like query language"
        },
        {
            "name": "OrientDB",
            "family": "Multi-Model",
            "hint": "Supports both document and graph models in one engine"
        }
    ]

    col.insert_many(products)

    print(
        f"[OK] Inserted {len(products)} mystery products."
    )

    print("\n--- Mystery Products ---")

    for product in col.find():
        print(
            f"{product['name']} -> "
            f"{product['family']}"
        )

    banner("Lab 1.1 Try Yourself Complete")


if __name__ == "__main__":
    main()