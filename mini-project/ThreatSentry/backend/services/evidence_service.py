from datetime import datetime, timezone
from urllib.parse import urlparse

from backend.services.mongo_store import get_mongo_client
from backend.core.config import settings


def add_threat_evidence(
    threat_id: str,
    source_name: str,
    source_url: str,
    summary: str,
    published_at=None,
):
    if not threat_id.strip():
        raise ValueError("Threat ID is required.")

    if not source_name.strip():
        raise ValueError("Source name is required.")

    parsed = urlparse(source_url)

    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Evidence URL must be a valid HTTPS URL.")

    if not summary.strip():
        raise ValueError("Evidence summary is required.")

    client = get_mongo_client()

    try:
        db = client[settings.MONGO_DATABASE]

        threat = db.threats.find_one(
            {"threat_id": threat_id},
            {"_id": 1},
        )

        if not threat:
            raise ValueError("Referenced threat does not exist.")

        evidence = {
            "threat_id": threat_id,
            "source_name": source_name.strip(),
            "source_url": source_url,
            "summary": summary.strip(),
            "published_at": published_at,
            "retrieved_at": datetime.now(timezone.utc),
            "verification_status": "source_recorded",
        }

        result = db.threat_evidence.insert_one(evidence)
        evidence["evidence_id"] = str(result.inserted_id)

        return evidence

    finally:
        client.close()


def list_threat_evidence(threat_id: str):
    client = get_mongo_client()

    try:
        db = client[settings.MONGO_DATABASE]
        records = db.threat_evidence.find(
            {"threat_id": threat_id}
        ).sort("retrieved_at", -1)

        evidence_list = []

        for item in records:
            item["evidence_id"] = str(item.pop("_id"))
            evidence_list.append(item)

        return evidence_list

    finally:
        client.close()
