import re
from datetime import datetime, timezone
from uuid import uuid4

import requests
from pymongo import DESCENDING

from backend.core.config import settings
from backend.services.mongo_store import get_mongo_client
from backend.services.retrieval import retrieve_threats, format_threats, format_listing, detect_filters, best_match
from backend.services.mitigation_service import handle_chat_command


SYSTEM_PROMPT = """
You are ThreatSentry AI, an offline Linux threat-intelligence
and mitigation assistant.

IDENTITY:
- You are a defensive cybersecurity assistant.
- Focus on Linux security, vulnerabilities, threat intelligence,
  package security and system hardening.
- You run locally using Ollama.

DATABASE GROUNDING:
- Use the supplied database records as evidence.
- Never invent scan results, installed packages, CVEs,
  vulnerability assessments or system information.
- Distinguish confirmed affected, not affected and unknown.
- Unknown does not mean vulnerable or safe.
- Distinguish advisory severity from installed-package assessment.
- If evidence is insufficient, state this clearly.

THREAT INTELLIGENCE:
- Explain threats using available threat records.
- Explain CVSS scores and severity when available.
- Identify the affected platform and packages when supported.
- Explain potential impact using reliable supplied information.
- Distinguish anticipated, active, evolving and resolved threats.

MITIGATION:
- Provide defensive remediation recommendations.
- Prefer official package-manager updates and vendor advisories.
- Explain why each recommended action is appropriate.
- Provide commands for the user to review when appropriate.
- Explain potential risks, dependencies and service disruption.
- Include verification steps after remediation.
- If the installed version or vulnerability status is unknown,
  recommend verification before applying a fix.
- Never recommend blindly executing commands.

SAFETY:
- You are READ-ONLY by default.
- Never execute shell commands.
- Never install, remove, update or modify packages.
- Never modify system configuration.
- Never automatically remediate vulnerabilities.
- Never claim to have performed an action.
- All commands are recommendations for user review.
- Actual system changes require explicit user confirmation
  outside this AI response.
- The APPLICATION (not you) proposes fixes when the user types
  'fix <package>' and applies them only after the user types
  'approve <plan id>'. Tell users this when they ask how to fix.
- Answer about the platform the user asks about (Linux, Windows,
  macOS, Android, iOS) using only the supplied threat records.

RESPONSE STYLE:
- Be technically accurate and concise.
- Use clear headings and bullet points.
- Explain technical terms when necessary.
- Avoid unnecessary repetition.
- Clearly identify uncertainty.
- When giving commands, explain what they do.
- Prefer Ubuntu/Debian commands when the detected platform
  is Ubuntu.
"""


def _utc_now():
    return datetime.now(timezone.utc)


def _database_context(db, query=""):
    threats = list(
        db.threats.find(
            {},
            {
                "_id": 0,
                "threat_id": 1,
                "name": 1,
                "platform": 1,
                "severity": 1,
                "status": 1,
                "description": 1,
                "cvss_score": 1,
                "external_id": 1,
            },
        ).sort("updated_at", DESCENDING).limit(5)
    )

    for threat in threats:
        threat["description"] = (
            threat.get("description") or ""
        )[:350]

    if query:
        found, _platform, _status = retrieve_threats(db, query)
        if found:
            threats = format_threats(found)

    scan = db.scan_runs.find_one(
        {},
        {"_id": 0},
        sort=[("started_at", DESCENDING)],
    )

    findings_context = []

    if scan:
        scan_id = scan.get("scan_id")

        if scan_id:
            findings_context = list(
                db.findings.find(
                    {"scan_id": scan_id},
                    {
                        "_id": 0,
                        "package": 1,
                        "installed_version": 1,
                        "threat_id": 1,
                        "external_id": 1,
                        "name": 1,
                        "severity": 1,
                        "cvss_score": 1,
                        "assessment": 1,
                        "ecosystem": 1,
                    },
                ).limit(20)
            )

    return (
        "RELEVANT THREAT RECORDS:\n"
        + str(threats)
        + "\nLATEST SCAN SUMMARY:\n"
        + str(scan or "No scan summary available.")
        + "\nLATEST SCAN INDIVIDUAL FINDINGS:\n"
        + str(findings_context)
        + "\nIMPORTANT: Findings are evidence from the database. "
        "Never infer that unknown means vulnerable or safe."
    )


def _is_scan_question(message):
    keywords = (
        "scan",
        "scanned",
        "scanner",
        "package",
        "packages",
        "affected",
        "not affected",
        "unknown",
        "vulnerability results",
        "vulnerability result",
        "scan results",
        "scan summary",
        "latest results",
        "latest scan",
    )

    text = message.lower()
    return any(word in text for word in keywords)


def _latest_scan_answer(db):
    scan = db.scan_runs.find_one(
        {},
        {"_id": 0},
        sort=[("started_at", DESCENDING)],
    )

    if not scan:
        return "No Linux vulnerability scan is available."

    scan_id = scan.get("scan_id")

    package_count = scan.get("package_count", 0)
    advisory_count = scan.get("advisory_count", 0)
    matches = scan.get("advisory_matches", 0)
    affected = scan.get("affected_count", 0)
    unknown = scan.get("unknown_count", 0)
    not_affected = scan.get("not_affected_count", 0)

    findings = list(
        db.findings.find(
            {"scan_id": scan_id},
            {
                "_id": 0,
                "package": 1,
                "installed_version": 1,
                "external_id": 1,
                "threat_id": 1,
                "name": 1,
                "severity": 1,
                "cvss_score": 1,
                "assessment": 1,
            },
        ).limit(1000)
    )

    started = scan.get("started_at")

    started_text = (
        started.strftime("%d %b %Y, %H:%M UTC")
        if hasattr(started, "strftime")
        else str(started or "Not recorded")
    )

    affected_findings = [
        f for f in findings
        if f.get("assessment") == "affected"
    ]

    unknown_findings = [
        f for f in findings
        if f.get("assessment") == "version_unknown"
    ]

    safe_findings = [
        f for f in findings
        if f.get("assessment") == "not_affected"
    ]

    def format_finding(f):
        package = f.get("package", "Unknown package")
        version = f.get("installed_version", "Unknown version")
        vulnerability = (
            f.get("external_id")
            or f.get("threat_id")
            or "Unknown advisory"
        )
        severity = f.get("severity", "Unknown")

        return (
            f"- **{package}** ({version}) — "
            f"{vulnerability} — Severity: {severity}"
        )

    def format_group(items, limit=15):
        if not items:
            return "None."

        lines = [
            format_finding(item)
            for item in items[:limit]
        ]

        if len(items) > limit:
            lines.append(
                f"- ...and {len(items) - limit} more records."
            )

        return "\n".join(lines)

    return (
        "## Latest Linux Vulnerability Scan\n\n"
        f"**Platform:** {scan.get('platform', 'Unknown')}\n\n"
        f"**Environment:** {scan.get('environment', 'Unknown')}\n\n"
        f"**Scan date:** {started_text}\n\n"
        f"**Status:** {scan.get('status', 'Unknown')}\n\n"
        f"**Mode:** {scan.get('scanner_mode', 'Unknown')}\n\n"
        "### Statistics\n\n"
        f"- Packages examined: **{package_count}**\n"
        f"- OSV advisories checked: **{advisory_count}**\n"
        f"- Package-advisory matches: **{matches}**\n"
        f"- Individual findings stored: **{len(findings)}**\n\n"
        "### Assessment\n\n"
        f"- Confirmed affected: **{affected}**\n"
        f"- Unknown: **{unknown}**\n"
        f"- Not affected: **{not_affected}**\n\n"
        "### Confirmed affected findings\n\n"
        f"{format_group(affected_findings)}\n\n"
        "### Unknown assessments\n\n"
        f"{format_group(unknown_findings)}\n\n"
        "### Not affected\n\n"
        f"{format_group(safe_findings)}\n\n"
        "### Interpretation\n\n"
        "Unknown assessments mean the scanner could not "
        "establish the installed package version's vulnerability "
        "status using the available advisory metadata. They are "
        "not confirmed vulnerabilities and are not confirmed safe.\n\n"
        "This scan was read-only. No system modifications "
        "or automatic remediation were performed."
    )


def _save_assistant_message(db, conversation_id, answer):
    db.messages.insert_one({
        "message_id": str(uuid4()),
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": answer,
        "created_at": _utc_now(),
    })

    db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {"updated_at": _utc_now()}},
    )


def send_message(message, conversation_id=None, user_id="local-user"):
    message = message.strip()

    if not message:
        raise ValueError("Message cannot be empty.")

    if len(message) > 6000:
        raise ValueError("Message exceeds the 6000-character limit.")

    client = get_mongo_client()

    try:
        db = client[settings.MONGO_DATABASE]
        now = _utc_now()

        if conversation_id:
            conversation = db.conversations.find_one({
                "conversation_id": conversation_id,
                "user_id": user_id,
            })

            if not conversation:
                raise ValueError("Conversation not found.")

        else:
            conversation_id = str(uuid4())

            conversation = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "title": message[:70],
                "created_at": now,
                "updated_at": now,
            }

            db.conversations.insert_one(conversation)

        db.messages.insert_one({
            "message_id": str(uuid4()),
            "conversation_id": conversation_id,
            "role": "user",
            "content": message,
            "created_at": now,
        })

        # Confirmation-based mitigation: 'fix <pkg>', 'approve <id>', 'reject <id>'.
        mitigation_reply = handle_chat_command(db, message)
        if mitigation_reply is not None:
            _save_assistant_message(db, conversation_id, mitigation_reply)
            return {
                "conversation_id": conversation_id,
                "reply": mitigation_reply,
            }

        # Scan questions use verified MongoDB data directly.
        # They do not wait for Ollama.
        if _is_scan_question(message):
            answer = _latest_scan_answer(db)
            _save_assistant_message(db, conversation_id, answer)

            return {
                "conversation_id": conversation_id,
                "reply": answer,
            }

        # Platform/status list questions are answered directly from MongoDB (instant, no model).
        plat, stat = detect_filters(message)
        if (
            (plat or stat)
            and re.search(r"\b(threats?|list|show|which|what)\b", message, re.I)
            and not re.search(r"\b(how|fix|mitigate|steps|procedure|explain)\b", message, re.I)
        ):
            found, _p, _s = retrieve_threats(db, message, k=10)
            answer = format_listing(found, stat, plat)
            _save_assistant_message(db, conversation_id, answer)
            return {"conversation_id": conversation_id, "reply": answer}

        # A question that names a known threat is answered directly from its record.
        hit = best_match(db, message)
        if hit:
            answer = format_listing([hit], None, None).replace("## Matching threats (1)", "## Threat record")
            _save_assistant_message(db, conversation_id, answer)
            return {"conversation_id": conversation_id, "reply": answer}

        # General cybersecurity questions use the local model.
        history = list(
            db.messages.find(
                {"conversation_id": conversation_id},
                {"_id": 0, "role": 1, "content": 1},
            ).sort("created_at", DESCENDING).limit(6)
        )

        history.reverse()

        for item in history:
            item["content"] = item["content"][:1200]

        context = _database_context(db, message)

        ollama_messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + "\n\n" + context,
            }
        ]

        ollama_messages.extend(history)

        retrieved, _p, _s = retrieve_threats(db, message)
        if ollama_messages[-1]["role"] == "user":
            ollama_messages[-1]["content"] = (
                "Answer ONLY from these threat records and cite their IDs. "
                "If they do not cover the question, say so.\n\n"
                + format_threats(retrieved)
                + "\n\nQuestion: " + message
            )

        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_CHAT_MODEL,
                "messages": ollama_messages,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                    "num_predict": settings.OLLAMA_NUM_PREDICT,
                    "temperature": 0.2,
                },
            },
            timeout=(10, 600),
        )

        response.raise_for_status()

        answer = (
            response.json()
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not answer:
            raise RuntimeError(
                "The local model returned an empty response."
            )

        _save_assistant_message(db, conversation_id, answer)

        return {
            "conversation_id": conversation_id,
            "reply": answer,
        }

    finally:
        client.close()


def list_conversations(user_id="local-user"):
    client = get_mongo_client()

    try:
        db = client[settings.MONGO_DATABASE]

        return list(
            db.conversations.find(
                {"user_id": user_id},
                {"_id": 0},
            ).sort("updated_at", DESCENDING).limit(50)
        )

    finally:
        client.close()


def get_messages(conversation_id, user_id="local-user"):
    client = get_mongo_client()

    try:
        db = client[settings.MONGO_DATABASE]

        exists = db.conversations.find_one({
            "conversation_id": conversation_id,
            "user_id": user_id,
        })

        if not exists:
            raise ValueError("Conversation not found.")

        return list(
            db.messages.find(
                {"conversation_id": conversation_id},
                {
                    "_id": 0,
                    "message_id": 1,
                    "role": 1,
                    "content": 1,
                    "created_at": 1,
                },
            ).sort("created_at", 1)
        )

    finally:
        client.close()