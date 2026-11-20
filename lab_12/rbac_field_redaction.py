import os
from pymongo import MongoClient


def banner(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    banner("Lab 12.1: Field-Level Redaction via Views")

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Set it in PowerShell before running."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    try:
        db = client["nosql_labs"]

        # Preserve all existing employee data.
        print("\n=== Original Employee Records ===")
        for doc in db.employees.find({}, {"_id": 0}):
            print(doc)

        # Drop only employees_safe if it is already a view.
        existing = list(
            db.list_collections(filter={"name": "employees_safe"})
        )

        if existing:
            if existing[0].get("type") != "view":
                raise RuntimeError(
                    "employees_safe is not a view. "
                    "Stopping to protect existing data."
                )
            db.command("drop", "employees_safe")

        pipeline = [
            {
                "$project": {
                    "_id": 0,
                    "username": 1,
                    "email": 1,
                    "role": 1,
                    "ssn": {
                        "$cond": [
                            {"$eq": [{"$type": "$ssn"}, "string"]},
                            {
                                "$concat": [
                                    "***-**-",
                                    {"$substrBytes": ["$ssn", 7, 4]}
                                ]
                            },
                            "$$REMOVE"
                        ]
                    },
                    "salary": "$$REMOVE"
                }
            }
        ]

        db.command(
            "create",
            "employees_safe",
            viewOn="employees",
            pipeline=pipeline
        )

        print("\n=== Redacted View: employees_safe ===")
        for doc in db.employees_safe.find():
            print(doc)

        original_count = db.employees.count_documents({})
        view_count = db.employees_safe.count_documents({})

        print("\n=== Verification ===")
        print("Original employee count:", original_count)
        print("Redacted view count:", view_count)

        if original_count != view_count:
            raise RuntimeError("Record counts do not match.")

        for doc in db.employees_safe.find():
            if "salary" in doc:
                raise RuntimeError("Salary was not excluded.")
            ssn = doc.get("ssn")
            if ssn is not None and not ssn.startswith("***-**-"):
                raise RuntimeError("An SSN was not masked.")

        print("[PASS] Employee records preserved.")
        print("[PASS] Salary excluded from the view.")
        print("[PASS] SSNs masked in the view.")
        print("[PASS] Lab 12.1 field-redaction check complete.")

    finally:
        client.close()


if __name__ == "__main__":
    main()
    