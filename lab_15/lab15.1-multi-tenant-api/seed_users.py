import os
import secrets
import hashlib
from getpass import getpass

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"])
db = client["tasktracker"]
users = db["users"]


def hash_password(password):
    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        310000
    ).hex()

    return salt, hashed


accounts = [
    ("admin1", "tenant_001", "admin"),
    ("user1", "tenant_001", "user"),
    ("user2", "tenant_002", "user")
]

try:
    for username, tenant_id, role in accounts:

        existing = users.find_one({
            "tenant_id": tenant_id,
            "username": username
        })

        if existing:
            print(f"{username} already exists. Skipping.")
            continue

        password = getpass(f"Set password for {username}: ")

        if len(password) < 8:
            print("Password must contain at least 8 characters.")
            continue

        salt, password_hash = hash_password(password)

        users.insert_one({
            "user_id": f"user_{secrets.token_hex(6)}",
            "tenant_id": tenant_id,
            "username": username,
            "role": role,
            "password_salt": salt,
            "password_hash": password_hash
        })

        print(f"Created {username} ({role}, {tenant_id})")

    print("\nUser seeding completed.")

finally:
    client.close()