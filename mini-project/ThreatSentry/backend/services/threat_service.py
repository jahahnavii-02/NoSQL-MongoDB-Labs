from datetime import datetime, timezone
from typing import Optional

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from backend.services.mongo_store import get_mongo_client
from backend.core.config import settings


VALID_STATUSES = {
    "Anticipated",
    "Active",
    "Evolving",
    "Resolved",
}

VALID_SEVERITIES = {
    "Critical",
    "High",
    "Medium",
    "Low",
    "Informational",
}


class ThreatValidationError(ValueError):
    pass


def create_threat(
    threat_id: str,
    name: str,
    description: str,
    platform: str,
    severity: str,
    status: str = "Anticipated",
    source: Optional[str] = None,
):
    threat_id = threat_id.strip()
    name = name.strip()

    if not threat_id or not name:
        raise ThreatValidationError("Threat ID and name are required.")

    if status not in VALID_STATUSES:
        raise ThreatValidationError("Invalid threat status.")

    if severity not in VALID_SEVERITIES:
        raise ThreatValidationError("Invalid severity.")

    now = datetime.now(timezone.utc)

    document = {
        "threat_id": threat_id,
        "name": name,
        "description": description.strip(),
        "platform": platform.strip(),
        "severity": severity,
        "status": status,
        "source": source,
        "created_at": now,
        "updated_at": now,
    }

    client = get_mongo_client()
    try:
        db = client[settings.MONGO_DATABASE]
        db.threats.insert_one(document)
        document.pop("_id", None)
        return document
    except DuplicateKeyError:
        raise ThreatValidationError("This threat ID already exists.")
    finally:
        client.close()


def get_threat(threat_id: str):
    client = get_mongo_client()
    try:
        db = client[settings.MONGO_DATABASE]
        document = db.threats.find_one(
            {"threat_id": threat_id},
            {"_id": 0, "embedding": 0},
        )
        return document
    finally:
        client.close()


def list_threats(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 100,
):
    if status and status not in VALID_STATUSES:
        raise ThreatValidationError("Invalid threat status.")

    limit = max(1, min(limit, 500))
    query = {}

    if status:
        query["status"] = status

    if platform:
        query["$or"] = [{"platform": platform}, {"platforms": platform}]

    client = get_mongo_client()
    try:
        db = client[settings.MONGO_DATABASE]
        cursor = (
            db.threats.find(query, {"_id": 0, "embedding": 0})
            .sort("updated_at", -1)
            .limit(limit)
        )
        return list(cursor)
    finally:
        client.close()


def update_threat_status(threat_id: str, status: str):
    if status not in VALID_STATUSES:
        raise ThreatValidationError("Invalid threat status.")

    client = get_mongo_client()
    try:
        db = client[settings.MONGO_DATABASE]
        result = db.threats.update_one(
            {"threat_id": threat_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.modified_count == 1 or (
            result.matched_count == 1
        )
    finally:
        client.close()
