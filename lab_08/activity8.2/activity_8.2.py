import time
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Connect to the MongoDB replica set running in Docker
uri = (
    "mongodb://mongo-primary:27017,"
    "mongo-secondary1:27017,"
    "mongo-secondary2:27017/"
    "?replicaSet=rs0"
)

client = MongoClient(
    uri,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=5000
)

db = client["lab8"]
collection = db["students"]

print("Connecting to MongoDB replica set...")

try:
    # Verify replica-set connectivity
    hello = client.admin.command("hello")

    print("Connected to replica set:", hello.get("setName"))
    print("Reading data continuously...\n")

    # Read data repeatedly to observe replica-set behavior
    for i in range(1, 11):
        try:
            # Identify the server handling the request
            hello = client.admin.command("hello")

            server = hello.get("me", "Unknown")
            is_primary = hello.get("isWritablePrimary", False)

            # Read a document from the students collection
            document = collection.find_one()

            print(
                f"Read {i}: "
                f"Server = {server} | "
                f"Is Primary = {is_primary} | "
                f"Document = {document}"
            )

        except PyMongoError as error:
            print(f"Read {i}: Connection/election event: {error}")
            print("The driver will attempt to reconnect.")

        time.sleep(2)

except PyMongoError as error:
    print("MongoDB connection failed:", error)

finally:
    client.close()
    print("\nConnection closed.")