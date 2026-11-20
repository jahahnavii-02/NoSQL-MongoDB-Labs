from pymongo import MongoClient
from rich.console import Console
from rich.table import Table

console = Console()

# MongoDB connection
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["nosql_labs"]
col = db["database_products"]


def banner(text):
    console.print("\n" + "=" * 70)
    console.print(f"=== {text} ===")
    console.print("=" * 70)


def main():

    # Clear previous data so duplicate records are not created
    col.delete_many({})

    # Database products and their NoSQL classification
    products = [
        {
            "name": "Amazon S3",
            "family": "Document/Column",
            "data_model": "Object/Key-Value",
            "vendor": "AWS",
            "use_case": "Static asset storage, data lakes, backups",
            "open_source": False
        },
        {
            "name": "Couchbase",
            "family": "Document",
            "data_model": "JSON Document",
            "vendor": "Couchbase Inc.",
            "use_case": "Session management, caching layer, user profiles",
            "open_source": True
        },
        {
            "name": "Apache HBase",
            "family": "Wide-Column",
            "data_model": "Column-Family",
            "vendor": "Apache",
            "use_case": "Time-series logs, streaming, big data analytics",
            "open_source": True
        },
        {
            "name": "Amazon Neptune",
            "family": "Graph",
            "data_model": "Property Graph / RDF",
            "vendor": "AWS",
            "use_case": "Knowledge graphs and relationship analysis",
            "open_source": False
        },
        {
            "name": "Memcached",
            "family": "Key-Value",
            "data_model": "Key-Value",
            "vendor": "Open Source",
            "use_case": "In-memory caching",
            "open_source": True
        },
        {
            "name": "Redis",
            "family": "Key-Value",
            "data_model": "Key-Value / Data Structures",
            "vendor": "Redis",
            "use_case": "Caching, sessions, real-time analytics",
            "open_source": True
        },
        {
            "name": "MongoDB",
            "family": "Document",
            "data_model": "JSON/BSON Document",
            "vendor": "MongoDB Inc.",
            "use_case": "Flexible application data and content management",
            "open_source": True
        },
        {
            "name": "Apache Cassandra",
            "family": "Wide-Column",
            "data_model": "Column-Family",
            "vendor": "Apache",
            "use_case": "High-volume writes and distributed data",
            "open_source": True
        },
        {
            "name": "Neo4j",
            "family": "Graph",
            "data_model": "Property Graph",
            "vendor": "Neo4j",
            "use_case": "Recommendation systems and relationship analysis",
            "open_source": True
        },
        {
            "name": "Elasticsearch",
            "family": "Document",
            "data_model": "JSON Document",
            "vendor": "Elastic",
            "use_case": "Search, logging and analytics",
            "open_source": True
        }
    ]

    # Insert into MongoDB
    result = col.insert_many(products)

    console.print(
        f"[OK] Inserted {len(result.inserted_ids)} database products."
    )

    # Display all products
    banner("Database Products Classification")

    table = Table(
        title="NoSQL Database Product Survey"
    )

    table.add_column("Product")
    table.add_column("Family")
    table.add_column("Data Model")
    table.add_column("Vendor")
    table.add_column("Use Case")

    for item in col.find({}, {"_id": 0}):
        table.add_row(
            item["name"],
            item["family"],
            item["data_model"],
            item["vendor"],
            item["use_case"]
        )

    console.print(table)

    # Group products by database family
    banner("Products Grouped by Database Family")

    grouped = {}

    for item in col.find({}, {"_id": 0}):
        family = item["family"]

        if family not in grouped:
            grouped[family] = []

        grouped[family].append(item["name"])

    group_table = Table(title="Database Family Summary")

    group_table.add_column("Family")
    group_table.add_column("Count")
    group_table.add_column("Products")

    for family, names in grouped.items():
        group_table.add_row(
            family,
            str(len(names)),
            ", ".join(names)
        )

    console.print(group_table)

    banner("Lab 1.1 Main Question Complete")


if __name__ == "__main__":
    main()