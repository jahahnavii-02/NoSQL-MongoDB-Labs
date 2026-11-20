import math
import re
from datetime import datetime, timezone

import requests

from backend.core.config import settings
from backend.services.mongo_store import get_mongo_client


OSV_API = "https://api.osv.dev/v1/vulns/"


def calculate_cvss31(vector: str):
    """Calculate a CVSS v3.1 base score from its metric vector."""

    metrics = {}

    for part in vector.split("/"):
        if ":" in part:
            key, value = part.split(":", 1)
            metrics[key] = value

    required = {"AV", "AC", "PR", "UI", "S", "C", "I", "A"}

    if not required.issubset(metrics):
        return None

    weights = {
        "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20},
        "AC": {"L": 0.77, "H": 0.44},
        "PR_U": {"N": 0.85, "L": 0.62, "H": 0.27},
        "PR_C": {"N": 0.85, "L": 0.68, "H": 0.50},
        "UI": {"N": 0.85, "R": 0.62},
        "CIA": {"H": 0.56, "L": 0.22, "N": 0.0},
    }

    try:
        scope_changed = metrics["S"] == "C"

        av = weights["AV"][metrics["AV"]]
        ac = weights["AC"][metrics["AC"]]

        pr_group = "PR_C" if scope_changed else "PR_U"
        pr = weights[pr_group][metrics["PR"]]

        ui = weights["UI"][metrics["UI"]]

        c = weights["CIA"][metrics["C"]]
        i = weights["CIA"][metrics["I"]]
        a = weights["CIA"][metrics["A"]]

    except KeyError:
        return None

    impact_sub = 1 - ((1 - c) * (1 - i) * (1 - a))

    if scope_changed:
        impact = 7.52 * (impact_sub - 0.029)
        impact -= 3.25 * ((impact_sub - 0.02) ** 15)
    else:
        impact = 6.42 * impact_sub

    if impact <= 0:
        return 0.0

    exploitability = 8.22 * av * ac * pr * ui

    if scope_changed:
        base_score = min(
            1.08 * (impact + exploitability),
            10
        )
    else:
        base_score = min(
            impact + exploitability,
            10
        )

    # CVSS Roundup rule
    return math.ceil((base_score - 1e-10) * 10) / 10


def _severity_from_osv(record):
    """
    Extract CVSS severity and vendor severity separately.
    Never infer a numeric score from descriptive wording.
    """

    cvss_score = None
    cvss_version = None

    for item in record.get("severity", []):
        vector = item.get("score", "")
        vector_type = item.get("type", "").upper()

        if not isinstance(vector, str):
            continue

        if vector_type in ("CVSS_V3", "CVSS_V3.1"):
            if vector.startswith("CVSS:3.1/"):
                cvss_score = calculate_cvss31(vector)
                cvss_version = "3.1"
                break

            if vector.startswith("CVSS:3.0/"):
                cvss_score = calculate_cvss31(vector)
                cvss_version = "3.0"
                break

    description = " ".join([
        record.get("summary") or "",
        record.get("details") or "",
    ])

    vendor_match = re.search(
        r"(?:security\s+)?severity\s*:\s*"
        r"(critical|high|medium|moderate|low)",
        description,
        re.IGNORECASE,
    )

    vendor_severity = None

    if vendor_match:
        vendor_severity = vendor_match.group(1).capitalize()

        if vendor_severity == "Moderate":
            vendor_severity = "Medium"

    if cvss_score is None:
        severity = "Unknown"
    elif cvss_score == 0:
        severity = "Informational"
    elif cvss_score <= 3.9:
        severity = "Low"
    elif cvss_score <= 6.9:
        severity = "Medium"
    elif cvss_score <= 8.9:
        severity = "High"
    else:
        severity = "Critical"

    return {
        "severity": severity,
        "cvss_score": cvss_score,
        "cvss_version": cvss_version,
        "vendor_severity": vendor_severity,
    }


def ingest_osv_vulnerability(vulnerability_id: str):
    """Retrieve an OSV advisory and store it in ThreatSentry."""

    vulnerability_id = vulnerability_id.strip()

    if not vulnerability_id:
        raise ValueError("OSV vulnerability ID is required.")

    response = requests.get(
        f"{OSV_API}{vulnerability_id}",
        headers={"Accept": "application/json"},
        timeout=20,
    )

    if response.status_code == 404:
        raise ValueError(
            "Vulnerability ID was not found in OSV."
        )

    response.raise_for_status()

    record = response.json()

    actual_id = record.get("id")

    if not actual_id:
        raise ValueError(
            "OSV returned an invalid vulnerability record."
        )

    now = datetime.now(timezone.utc)

    threat_id = f"OSV-{actual_id}"

    affected = record.get("affected", [])

    ecosystems = sorted({
        item.get("package", {}).get("ecosystem", "")
        for item in affected
        if item.get("package", {}).get("ecosystem")
    })

    ubuntu_related = any(
        ecosystem.lower().startswith("ubuntu")
        for ecosystem in ecosystems
    )

    platform = (
        "Ubuntu Linux"
        if ubuntu_related
        else ", ".join(ecosystems[:5]) or "Multiple platforms"
    )

    description = (
        record.get("details")
        or record.get("summary")
        or "No detailed description supplied by OSV."
    )

    source_url = (
        f"https://osv.dev/vulnerability/{actual_id}"
    )

    severity_data = _severity_from_osv(record)

    threat_document = {
        "threat_id": threat_id,
        "name": record.get("summary") or actual_id,
        "description": description,
        "platform": platform,

        "severity": severity_data["severity"],
        "cvss_score": severity_data["cvss_score"],
        "cvss_version": severity_data["cvss_version"],
        "vendor_severity": severity_data["vendor_severity"],

        "status": "Anticipated",
        "source": "OSV",
        "external_id": actual_id,

        "aliases": record.get("aliases", []),
        "affected": affected,
        "ecosystems": ecosystems,

        "published_at": record.get("published"),
        "modified_at": record.get("modified"),

        "intelligence_state": "published_advisory",
        "exposure_assessment": "not_assessed",

        "updated_at": now,
    }

    client = get_mongo_client()

    try:
        db = client[settings.MONGO_DATABASE]

        existing = db.threats.find_one(
            {"threat_id": threat_id},
            {"_id": 1},
        )

        if existing:
            db.threats.update_one(
                {"threat_id": threat_id},
                {"$set": threat_document},
            )
            action = "updated"

        else:
            threat_document["created_at"] = now

            db.threats.insert_one(threat_document)
            action = "inserted"

        evidence_summary = (
            record.get("summary")
            or description[:1000]
        )

        db.threat_evidence.update_one(
            {
                "threat_id": threat_id,
                "source_url": source_url,
            },
            {
                "$set": {
                    "source_name": (
                        "Open Source Vulnerabilities (OSV)"
                    ),
                    "source_url": source_url,
                    "summary": evidence_summary,
                    "published_at": record.get("published"),
                    "retrieved_at": now,
                    "verification_status": "source_recorded",
                },
                "$setOnInsert": {
                    "threat_id": threat_id,
                },
            },
            upsert=True,
        )

        return {
            "result": action,
            "threat_id": threat_id,
            "external_id": actual_id,
            "source": "OSV",

            "severity": severity_data["severity"],
            "cvss_score": severity_data["cvss_score"],
            "cvss_version": severity_data["cvss_version"],
            "vendor_severity": severity_data["vendor_severity"],

            "status": "Anticipated",
            "exposure_assessment": "not_assessed",
            "affected_entries": len(affected),
            "evidence_url": source_url,
        }

    finally:
        client.close()