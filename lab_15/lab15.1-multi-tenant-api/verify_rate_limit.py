import os
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING

load_dotenv()
client = MongoClient(os.environ["MONGO_URI"])
db = client["tasktracker"]

try:
    print("========== MONGODB RATE LIMIT RECORD ==========")

    records = db.rate_limits.find(
        {},
        {"_id": 0}
    ).sort("window_start", DESCENDING).limit(5)

    for record in records:
        print(record)

finally:
    client.close()
