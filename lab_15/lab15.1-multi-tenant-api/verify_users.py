import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"])
db = client["tasktracker"]

try:
    print("========== USER VERIFICATION ==========")

    for user in db.users.find(
        {},
        {"_id": 0, "username": 1, "tenant_id": 1, "role": 1}
    ).sort("username", 1):
        print(user)

    print("\nTotal users:", db.users.count_documents({}))

finally:
    client.close()
