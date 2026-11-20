from getpass import getpass
from pymongo import MongoClient, ASCENDING, DESCENDING

password = getpass("Enter ctiAdmin password: ")

client = MongoClient(
    host="localhost",
    port=27130,
    username="ctiAdmin",
    password=password,
    authSource="admin",
    directConnection=True,
    serverSelectionTimeoutMS=5000
)

db = client["tasktracker"]

try:
    client.admin.command("ping")
    print("\nMongoDB connected successfully.")

    # Create collections if they do not already exist.
    for name in ["users", "tasks", "rate_limits"]:
        if name not in db.list_collection_names():
            db.create_collection(name)
            print(f"Created collection: {name}")
        else:
            print(f"Collection already exists: {name}")

    # USERS: unique username within each tenant.
    db.users.create_index(
        [("tenant_id", ASCENDING), ("username", ASCENDING)],
        unique=True,
        name="tenant_username_unique"
    )

    # TASKS: tenant-scoped listing.
    db.tasks.create_index(
        [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
        name="tenant_created_at"
    )

    # TASKS: owner-scoped access.
    db.tasks.create_index(
        [("tenant_id", ASCENDING), ("owner_id", ASCENDING)],
        name="tenant_owner"
    )

    # RATE LIMITS: one counter per key and time window.
    db.rate_limits.create_index(
        [("key", ASCENDING), ("window_start", ASCENDING)],
        unique=True,
        name="rate_limit_key_window"
    )

    # Automatically expire rate-limit records.
    db.rate_limits.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="rate_limit_ttl"
    )

    print("\n========== INDEX VERIFICATION ==========")

    for collection in ["users", "tasks", "rate_limits"]:
        print(f"\n{collection}:")
        for index in db[collection].list_indexes():
            print(index)

    print("\nTaskTracker schema and indexes created successfully.")

finally:
    client.close()
