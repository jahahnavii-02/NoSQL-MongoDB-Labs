from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Connect to the MongoDB replica set
uri = (
    "mongodb://mongo-primary:27017,"
    "mongo-secondary1:27017,"
    "mongo-secondary2:27017/"
    "?replicaSet=rs0"
)

client = MongoClient(uri, serverSelectionTimeoutMS=10000)

try:
    # Display replica-set configuration and member priorities
    config = client.admin.command("replSetGetConfig")["config"]

    print("Replica Set:", config["_id"])
    print("\nMember Priorities:")

    for member in config["members"]:
        print(
            f'{member["host"]} | '
            f'priority: {member.get("priority", 1)} | '
            f'arbiter: {member.get("arbiterOnly", False)}'
        )

    # Display the current election result
    status = client.admin.command("replSetGetStatus")

    print("\nReplica Set Member States:")

    for member in status["members"]:
        print(
            f'{member["name"]} | '
            f'{member["stateStr"]} | '
            f'health: {member["health"]}'
        )

    print("\nElection experiment verification completed.")

except PyMongoError as error:
    print("MongoDB error:", error)

finally:
    client.close()