from pymongo import MongoClient
import time

# Connect directly to the current replica-set primary
primary = MongoClient(
    "mongodb://localhost:27018/?directConnection=true",
    serverSelectionTimeoutMS=5000
)

db = primary["test"]
collection = db["students"]

print("Connected to MongoDB replica set")
print("Reading data continuously...\n")

# Continuously read data
for i in range(10):
    try:
        document = collection.find_one()

        # Identify the server handling the request
        server = primary.admin.command("hello")

        print(
            f"Read {i + 1}: "
            f"Server = {server.get('me')} | "
            f"Is Primary = {server.get('isWritablePrimary')} | "
            f"Document = {document}"
        )

        time.sleep(2)

    except Exception as e:
        print("Connection error:", e)
        print("Attempting to reconnect...\n")
        time.sleep(3)

primary.close()

print("\nConnection closed.")