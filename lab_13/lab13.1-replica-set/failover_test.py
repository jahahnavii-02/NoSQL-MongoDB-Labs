from pymongo import MongoClient
from pymongo.errors import PyMongoError
from getpass import getpass
import time

print("MongoDB Replica Set - PyMongo Failover Test")

password = getpass("Enter ctiAdmin password: ")

client = MongoClient(
    "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/",
    username="ctiAdmin",
    password=password,
    authSource="admin",
    replicaSet="rs0",
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    retryWrites=True
)

db = client["lab13_failover_test"]
collection = db["heartbeat"]

# Create an independent test record
collection.update_one(
    {"_id": "failover-check"},
    {"$set": {"message": "Replica set failover test", "active": True}},
    upsert=True
)

print("\nConnected successfully.")
print("Continuous reads started. Press Ctrl+C to stop.\n")

previous_primary = None

try:
    while True:
        try:
            hello = client.admin.command("hello")
            current_primary = hello.get("primary", "Detecting...")

            if current_primary != previous_primary:
                print(f"\nPrimary detected: {current_primary}")
                previous_primary = current_primary

            record = collection.find_one({"_id": "failover-check"})
            if record:
                print(f"READ SUCCESS | Primary: {current_primary}")

        except PyMongoError as error:
            print(f"Temporary connection issue: {error}")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nFailover test stopped.")

finally:
    client.close()