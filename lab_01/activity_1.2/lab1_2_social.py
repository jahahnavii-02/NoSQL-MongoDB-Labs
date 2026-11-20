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

    banner("Lab 1.2: Social Media Analytics")

    db = get_db("nosql_labs")

    col = reset_collection(
        "nosql_labs",
        "social_media_mapping"
    )

    social_media = [
        {
            "data_domain": "Raw Post Storage",
            "family": "Wide-Column",
            "database": "Apache Cassandra",
            "reason": "High write throughput and time-series access pattern"
        },
        {
            "data_domain": "Real-Time Analytics",
            "family": "Key-Value",
            "database": "Redis",
            "reason": "Fast counters and trending-topic caches"
        }
    ]

    col.insert_many(social_media)

    print("Social Media Analytics data inserted successfully.")
    print("\n--- Social Media Analytics Mapping ---")

    for item in col.find({}, {"_id": 0}):
        print(
            f"{item['data_domain']} -> "
            f"{item['family']} -> "
            f"{item['database']}"
        )
        print(f"Reason: {item['reason']}")
        print()

    banner("Lab 1.2 Social Media Complete")


if __name__ == "__main__":
    main()