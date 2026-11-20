from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "cti_platform"

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]


def test_connection():
    client.admin.command("ping")
    print("MongoDB connection successful")
    print(f"Database: {DATABASE_NAME}")


if __name__ == "__main__":
    test_connection()