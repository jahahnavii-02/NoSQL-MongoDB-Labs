from pymongo import MongoClient
from pymongo.errors import PyMongoError

URI = (
    "mongodb://mongo-primary:27017,"
    "mongo-secondary1:27017,"
    "mongo-secondary2:27017/"
    "?replicaSet=rs0"
)


def main():
    client = None

    try:
        client = MongoClient(
            URI,
            serverSelectionTimeoutMS=15000
        )
        client.admin.command("ping")

        config = client.admin.command("replSetGetConfig")["config"]

        print("Replica Set:", config["_id"])
        print("\nReplica Set Members:")

        arbiter_found = False

        for member in config["members"]:
            is_arbiter = member.get("arbiterOnly", False)

            print(
                f'{member["host"]} | '
                f'arbiterOnly: {is_arbiter} | '
                f'priority: {member.get("priority", 1)}'
            )

            if is_arbiter:
                arbiter_found = True

        print("\nArbiter Verification:")
        if arbiter_found:
            print("SUCCESS: An arbiter is configured.")
            print("The arbiter votes in elections but stores no data.")
            print(
                "It provides an additional vote without the storage "
                "cost of another data-bearing MongoDB node."
            )
        else:
            print("No arbiter is configured.")

    except PyMongoError as error:
        print("MongoDB verification failed:", error)

    finally:
        if client is not None:
            client.close()
            print("\nConnection closed.")


if __name__ == "__main__":
    main()