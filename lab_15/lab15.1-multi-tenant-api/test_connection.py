from getpass import getpass
from pymongo import MongoClient

print("TaskTracker MongoDB Connection Test")
password = getpass("Enter ctiAdmin password: ")

try:
    client = MongoClient(
        host="localhost",
        port=27130,
        username="ctiAdmin",
        password=password,
        authSource="admin",
        directConnection=True,
        serverSelectionTimeoutMS=5000
    )

    print("\nTesting MongoDB connection...")
    print("Ping:", client.admin.command("ping"))

    db = client["tasktracker"]
    print("Database selected:", db.name)
    print("Existing collections:", db.list_collection_names())

    print("\nConnection test successful!")

except Exception as error:
    print("\nConnection test failed:", type(error).__name__)
    print(str(error))

finally:
    if "client" in locals():
        client.close()
