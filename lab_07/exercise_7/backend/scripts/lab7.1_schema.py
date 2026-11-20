from pymongo import MongoClient
from datetime import datetime


# -----------------------------
# MongoDB Connection
# -----------------------------

client = MongoClient("mongodb://localhost:27017/")
db = client["cti_platform"]


# -----------------------------
# Collections
# -----------------------------

threats = db["threats"]
sources = db["sources"]
indicators = db["indicators"]


# -----------------------------
# Clear previous Lab 7.1 data
# -----------------------------

threats.delete_many({})
sources.delete_many({})
indicators.delete_many({})


# -----------------------------
# SOURCE DATA
# -----------------------------

sources_data = [
    {
        "_id": "SRC001",
        "name": "CTI Digest",
        "organization": "Cyber Threat Intelligence Digest",
        "url": "https://ctidigest.com/",
        "type": "Threat Intelligence"
    },
    {
        "_id": "SRC002",
        "name": "Security Research Source",
        "organization": "Security Research Group",
        "url": "https://example.com/",
        "type": "Security Research"
    },
    {
        "_id": "SRC003",
        "name": "Threat Intelligence Report",
        "organization": "Cyber Security Organization",
        "url": "https://example.org/",
        "type": "Annual Report"
    }
]

sources.insert_many(sources_data)


# -----------------------------
# INDICATOR DATA
# These are REFERENCED
# -----------------------------

indicators_data = [
    {
        "_id": "IOC001",
        "type": "IP",
        "value": "192.0.2.10",
        "confidence": 90,
        "status": "Malicious"
    },
    {
        "_id": "IOC002",
        "type": "DOMAIN",
        "value": "malicious-example.test",
        "confidence": 85,
        "status": "Malicious"
    },
    {
        "_id": "IOC003",
        "type": "HASH",
        "value": "5d41402abc4b2a76b9719d911017c592",
        "confidence": 95,
        "status": "Malicious"
    },
    {
        "_id": "IOC004",
        "type": "URL",
        "value": "https://example.test/payload",
        "confidence": 88,
        "status": "Suspicious"
    }
]

indicators.insert_many(indicators_data)


# -----------------------------
# THREAT DATA
# -----------------------------

threats_data = [
    {
        "_id": "THR001",

        "title": "Ransomware Campaign",

        "description":
            "A ransomware campaign targeting enterprise systems "
            "using malicious payloads and credential theft.",

        "category": "Ransomware",

        "severity": "Critical",

        "publishedDate": datetime(2026, 9, 20),

        # EMBEDDED
        "source": {
            "id": "SRC001",
            "name": "CTI Digest",
            "type": "Threat Intelligence"
        },

        # EMBEDDED
        "tags": [
            "ransomware",
            "malware",
            "enterprise"
        ],

        # EMBEDDED
        "classification": {
            "type": "Malware",
            "confidence": 0.94
        },

        # REFERENCED
        "indicatorIds": [
            "IOC001",
            "IOC003"
        ]
    },

    {
        "_id": "THR002",

        "title": "Phishing Infrastructure",

        "description":
            "A phishing campaign using malicious domains "
            "to collect user credentials.",

        "category": "Phishing",

        "severity": "High",

        "publishedDate": datetime(2026, 9, 22),

        # EMBEDDED
        "source": {
            "id": "SRC001",
            "name": "CTI Digest",
            "type": "Threat Intelligence"
        },

        # EMBEDDED
        "tags": [
            "phishing",
            "credential-theft",
            "social-engineering"
        ],

        # EMBEDDED
        "classification": {
            "type": "Phishing",
            "confidence": 0.91
        },

        # REFERENCED
        "indicatorIds": [
            "IOC002",
            "IOC004"
        ]
    },

    {
        "_id": "THR003",

        "title": "Malware Distribution Activity",

        "description":
            "Malware distribution infrastructure was observed "
            "delivering malicious files to targeted systems.",

        "category": "Malware",

        "severity": "High",

        "publishedDate": datetime(2026, 9, 25),

        # EMBEDDED
        "source": {
            "id": "SRC002",
            "name": "Security Research Source",
            "type": "Security Research"
        },

        # EMBEDDED
        "tags": [
            "malware",
            "payload",
            "distribution"
        ],

        # EMBEDDED
        "classification": {
            "type": "Malware",
            "confidence": 0.89
        },

        # REFERENCED
        "indicatorIds": [
            "IOC003",
            "IOC004"
        ]
    }
]

threats.insert_many(threats_data)


# -----------------------------
# Verification
# -----------------------------

print("\n================================")
print("LAB 7.1 DATABASE CREATED")
print("================================")

print("Database:", db.name)

print(
    "Threat documents:",
    threats.count_documents({})
)

print(
    "Source documents:",
    sources.count_documents({})
)

print(
    "Indicator documents:",
    indicators.count_documents({})
)

print("\nCollections:")

for collection in db.list_collection_names():
    print("-", collection)

print("\nLab 7.1 schema setup completed successfully.")