from pymongo import MongoClient
from pymongo.read_preferences import Secondary
from pymongo.errors import PyMongoError
import time

# Lab 8.1: Deploy a Local Replica Set
# Objective: Insert a document into the primary,
# verify replication on both secondaries, and check member health.

URI = (
    "mongodb://mongo-primary:27017,"
    "mongo-secondary1:27017,"
    "mongo-secondary2:27017/"
    "?replicaSet=rs0"
)

DATABASE_NAME = "lab8"
COLLECTION_NAME = "students"


def main():
    client = None
    secondary_clients = []

    try:
        # Connect to the replica set.
        client = MongoClient(
            URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000
        )

        client.admin.command("ping")
        print("Connected to MongoDB replica set.")

        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Wait for a writable primary and insert the document.
        document = {
            "name": "Jahnavi",
            "course": "AIML",
            "lab": "Lab 8.1",
            "test": "replication-check"
        }

        result = collection.insert_one(document)
        document_id = result.inserted_id

        print("\nDocument inserted successfully.")
        print("Inserted document ID:", document_id)

        # Verify the document on both secondary members.
        secondary_nodes = [
            ("mongo-secondary1:27017", "Secondary 1"),
            ("mongo-secondary2:27017", "Secondary 2")
        ]

        print("\nVerifying replication on secondaries...")

        for address, label in secondary_nodes:
            secondary_client = MongoClient(
                f"mongodb://{address}/?directConnection=true",
                read_preference=Secondary(),
                serverSelectionTimeoutMS=10000
            )
            secondary_clients.append(secondary_client)

            secondary_collection = (
                secondary_client[DATABASE_NAME][COLLECTION_NAME]
            )

            replicated_document = None

            # Allow a short period for replication to catch up.
            for attempt in range(10):
                replicated_document = secondary_collection.find_one(
                    {"_id": document_id}
                )

                if replicated_document is not None:
                    break

                time.sleep(1)

            print(f"\n{label} ({address}):")
            if replicated_document:
                print(replicated_document)
            else:
                print("Document not found on this secondary yet.")

        # Display replica-set status.
        print("\nReplica Set Status:")
        status = client.admin.command("replSetGetStatus")
        print("Replica set name:", status["set"])

        for member in status["members"]:
            print(
                f'{member["name"]} | '
                f'{member["stateStr"]} | '
                f'health: {member["health"]}'
            )

    except PyMongoError as error:
        print("\nMongoDB operation failed:")
        print(error)
        print(
            "\nCheck that the replica-set containers are running "
            "and that the replica set is named rs0."
        )

    finally:
        for secondary_client in secondary_clients:
            secondary_client.close()

        if client is not None:
            client.close()

        print("\nConnections closed.")


if __name__ == "__main__":
    main()