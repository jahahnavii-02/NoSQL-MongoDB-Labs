"""Streaming chat. Routing:  commands -> scan -> platform/status lists -> named threat -> LLM (streamed).
The LLM path uses retrieved records first, then clearly-labelled general security knowledge."""
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

import requests
from pymongo import DESCENDING

from backend.core.config import settings
from backend.services import chat_service as cs
from backend.services.mongo_store import get_mongo_client
from backend.services.mitigation_service import handle_chat_command
from backend.services.retrieval import (
    retrieve_threats, format_threats, format_listing, detect_filters, best_match,
)

GENERAL_SYSTEM = """You are ThreatSentry AI, a defensive cybersecurity assistant. Use the THREAT RECORDS first and cite their IDs. If they do not cover the question, answer from well-established security knowledge, starting that part with 'General guidance (not from the database):'. Never invent CVE IDs or scan results. You cannot run commands. Be concise: finish in under 120 words, ending with a complete sentence. Defensive help only."""

SCAN_RE = re.compile(r"\b(scan|scanned|scan results?|latest results?|my (system|packages|machine|computer)|installed packages)\b", re.I)
LIST_RE = re.compile(r"\b(threats?|list|show|which|what)\b", re.I)
NOT_LIST_RE = re.compile(r"\b(how|fix|mitigate|steps|procedure|explain|why)\b", re.I)


def _line(**kw):
    return json.dumps(kw) + "\n"


def direct_answer(db, message):
    """Answer straight from MongoDB (instant, no model) or return None."""
    reply = handle_chat_command(db, message)
    if reply is not None:
        return reply
    if SCAN_RE.search(message):
        return cs._latest_scan_answer(db)
    plat, stat = detect_filters(message)
    if (plat or stat) and LIST_RE.search(message) and not NOT_LIST_RE.search(message):
        found, _p, _s = retrieve_threats(db, message, k=10)
        return format_listing(found, stat, plat)
    hit = best_match(db, message)
    if hit:
        return format_listing([hit], None, None).replace("## Matching threats (1)", "## Threat record")
    return None


def _scan_line(db):
    scan = db.scan_runs.find_one({}, {"_id": 0}, sort=[("started_at", DESCENDING)])
    if not scan:
        return "No Linux scan has been run yet."
    return (f"Latest Linux scan: {scan.get('package_count', 0)} packages, confirmed affected "
            f"{scan.get('affected_count', 0)}, unknown {scan.get('unknown_count', 0)}, "
            f"not affected {scan.get('not_affected_count', 0)}.")


def _compact(threats):
    out = []
    for t in threats:
        steps = "; ".join((t.get("mitigation") or [])[:2])
        out.append(f"[{t.get('external_id') or t['threat_id']}] {t['name'][:80]} ({t.get('status')}, {t.get('severity')}). Fix: {steps[:200]}")
    return "\n".join(out) or "(none)"


def _llm_tokens(db, message, conversation_id):
    history = list(db.messages.find(
        {"conversation_id": conversation_id}, {"_id": 0, "role": 1, "content": 1}
    ).sort("created_at", DESCENDING).limit(3))
    history.reverse()
    history = [{"role": h["role"], "content": h["content"][:400]} for h in history[:-1]]  # last one is this question

    records = _compact(retrieve_threats(db, message, k=2, semantic=False)[0])
    user = (f"THREAT RECORDS (may be empty):\n{records}\n\nSCAN SUMMARY: {_scan_line(db)}\n\nQUESTION: {message}")
    messages = [{"role": "system", "content": GENERAL_SYSTEM}, *history, {"role": "user", "content": user}]

    with requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat", stream=True, timeout=(10, 600),
        json={"model": settings.OLLAMA_CHAT_MODEL, "messages": messages, "stream": True, "keep_alive": "30m",
              "options": {"num_ctx": 2048, "num_thread": max(1, (__import__("os").cpu_count() or 4) - 2), "num_predict": 300,
                          "temperature": 0.3}},
    ) as resp:
        resp.raise_for_status()
        for raw in resp.iter_lines():
            if not raw:
                continue
            data = json.loads(raw.decode("utf-8"))
            token = data.get("message", {}).get("content", "")
            if token:
                yield token
            if data.get("done"):
                break


def stream_message(message, conversation_id=None, user_id="local-user"):
    message = (message or "").strip()
    if not message:
        yield _line(error="Message cannot be empty.")
        return
    client = get_mongo_client()
    try:
        db = client[settings.MONGO_DATABASE]
        now = datetime.now(timezone.utc)
        if conversation_id:
            if not db.conversations.find_one({"conversation_id": conversation_id, "user_id": user_id}):
                yield _line(error="Conversation not found.")
                return
        else:
            conversation_id = str(uuid4())
            db.conversations.insert_one({"conversation_id": conversation_id, "user_id": user_id,
                                         "title": message[:70], "created_at": now, "updated_at": now})
        yield _line(conversation_id=conversation_id)
        db.messages.insert_one({"message_id": str(uuid4()), "conversation_id": conversation_id,
                                "role": "user", "content": message, "created_at": now})

        direct = direct_answer(db, message)
        if direct is not None:
            cs._save_assistant_message(db, conversation_id, direct)
            yield _line(token=direct)
            yield _line(done=True)
            return

        parts = []
        for token in _llm_tokens(db, message, conversation_id):
            parts.append(token)
            yield _line(token=token)
        answer = "".join(parts).strip()
        if not answer:
            yield _line(error="The local model returned an empty response.")
            return
        cs._save_assistant_message(db, conversation_id, answer)
        yield _line(done=True)
    except Exception as exc:
        yield _line(error=f"{type(exc).__name__}: {str(exc)[:200]}")
    finally:
        client.close()
