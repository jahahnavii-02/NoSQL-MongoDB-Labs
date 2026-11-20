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

    banner("Lab 1.2: Ride-Sharing NoSQL Mapping")

    db = get_db("nosql_labs")

    col = reset_collection(
        "nosql_labs",
        "ride_sharing_mapping"
    )

    ride_sharing = [
        {
            "data_domain": "Driver Locations",
            "family": "Key-Value",
            "database": "Redis",
            "reason": "Frequently updated and read by driver ID"
        },
        {
            "data_domain": "User Profiles",
            "family": "Document",
            "database": "MongoDB",
            "reason": "Self-contained profiles with nested fields"
        },
        {
            "data_domain": "Ride History",
            "family": "Document / Wide-Column",
            "database": "MongoDB / Cassandra",
            "reason": "Append-only data queried by rider ID and date range"
        },
        {
            "data_domain": "Driver-Rider Relationships",
            "family": "Graph",
            "database": "Neo4j",
            "reason": "Efficient traversal of relationships and connections"
        }
    ]

    col.insert_many(ride_sharing)

    print("Ride-Sharing data inserted successfully.")
    print("\n--- Ride-Sharing NoSQL Mapping ---")

    for item in col.find({}, {"_id": 0}):
        print(
            f"{item['data_domain']} -> "
            f"{item['family']} -> "
            f"{item['database']}"
        )
        print(f"Reason: {item['reason']}")
        print()

    banner("Lab 1.2 Main Question Complete")


if __name__ == "__main__":
    main()