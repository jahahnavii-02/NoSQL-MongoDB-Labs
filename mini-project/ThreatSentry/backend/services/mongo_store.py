from datetime import datetime, timezone

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from backend.core.config import settings


COLLECTIONS = [
    "threats",
    "threat_evidence",
    "conversations",
    "messages",
    "scan_runs",
    "findings",
    "mitigation_plans",
    "audit_events",
    "intel_sources",
    "document_chunks",
]


def get_mongo_client():
    return MongoClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
    )


def get_database(client=None):
    client = client or get_mongo_client()
    return client[settings.MONGO_DATABASE]


def ensure_schema():
    client = get_mongo_client()

    try:
        client.admin.command("ping")
        db = client[settings.MONGO_DATABASE]

        existing = set(db.list_collection_names())

        for name in COLLECTIONS:
            if name not in existing:
                db.create_collection(name)

        # Threat intelligence indexes
        db.threats.create_index(
            [("threat_id", ASCENDING)],
            unique=True,
            sparse=True,
        )
        db.threats.create_index(
            [("status", ASCENDING), ("updated_at", DESCENDING)]
        )
        db.threats.create_index(
            [("platform", ASCENDING), ("severity", ASCENDING)]
        )

        # Evidence lookup
        db.threat_evidence.create_index(
            [("threat_id", ASCENDING), ("created_at", DESCENDING)]
        )

        # Chat history
        db.conversations.create_index(
            [("user_id", ASCENDING), ("updated_at", DESCENDING)]
        )
        db.messages.create_index(
            [("conversation_id", ASCENDING), ("created_at", ASCENDING)]
        )

        # Linux scanner
        db.scan_runs.create_index(
            [("host_id", ASCENDING), ("started_at", DESCENDING)]
        )
        db.findings.create_index(
            [("scan_id", ASCENDING), ("severity", ASCENDING)]
        )
        db.findings.create_index(
            [("cve_id", ASCENDING), ("status", ASCENDING)]
        )

        # Mitigation and audit
        db.mitigation_plans.create_index(
            [("finding_id", ASCENDING), ("status", ASCENDING)]
        )
        db.audit_events.create_index(
            [("created_at", DESCENDING)]
        )

        # RAG metadata
        db.document_chunks.create_index(
            [("document_id", ASCENDING), ("chunk_index", ASCENDING)]
        )
        db.intel_sources.create_index(
            [("source_id", ASCENDING)],
            unique=True,
            sparse=True,
        )

        return {
            "status": "success",
            "database": settings.MONGO_DATABASE,
            "collections": sorted(db.list_collection_names()),
            "collection_count": len(db.list_collection_names()),
        }

    except PyMongoError:
        raise

    finally:
        client.close()


if __name__ == "__main__":
    result = ensure_schema()
    print("ThreatSentry MongoDB schema initialized.")
    print("Database:", result["database"])
    print("Collections:", result["collection_count"])
    for name in result["collections"]:
        print("-", name)

