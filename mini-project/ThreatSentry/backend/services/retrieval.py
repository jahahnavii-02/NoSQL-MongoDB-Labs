"""Platform/status-aware retrieval for the chat: filters on MongoDB fields, then ranks by
embedding similarity (Ollama) with a keyword fallback. Works on plain MongoDB (no Atlas needed)."""
import re
import requests
from backend.core.config import settings

PLATFORMS = {
    "Linux": ["linux", "ubuntu", "debian", "fedora", "kernel"],
    "Windows": ["windows", "win10", "win11"],
    "macOS": ["macos", "mac", "osx"],
    "Android": ["android"],
    "iOS": ["ios", "iphone", "ipad"],
}
STATUSES = {
    "Anticipated": ["anticipated", "upcoming", "emerging", "predicted", "future"],
    "Active": ["active", "ongoing", "exploited", "currently"],
    "Evolving": ["evolving", "evolve", "variant", "variants"],
    "Resolved": ["resolved", "patched", "fixed", "closed"],
}
STOP = {"the", "a", "an", "of", "for", "to", "and", "is", "are", "what", "how", "do", "i", "me", "my", "on", "in", "about", "threats", "threat"}


def detect_filters(text):
    t = text.lower()
    def pick(table):
        for key, words in table.items():
            if any(re.search(rf"\b{re.escape(w)}\b", t) for w in words):
                return key
    return pick(PLATFORMS), pick(STATUSES)


def embed(text):
    r = requests.post(f"{settings.OLLAMA_BASE_URL}/api/embed",
                      json={"model": settings.OLLAMA_EMBED_MODEL, "input": text}, timeout=180)
    r.raise_for_status()
    return r.json()["embeddings"][0]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _keyword_score(query, doc):
    words = {w for w in re.findall(r"[a-z0-9\-]+", query.lower()) if w not in STOP and len(w) > 2}
    hay = " ".join([doc.get("name", ""), doc.get("description", ""), doc.get("threat_id", ""),
                    doc.get("external_id") or ""]).lower()
    return sum(1 for w in words if w in hay)


def retrieve_threats(db, query, k=5, semantic=True):
    """Return (threats, platform, status). Curated multi-platform records only (not raw OSV rows)."""
    platform, status = detect_filters(query)
    q = {"threat_id": {"$not": re.compile("^OSV-")}}
    if platform:
        q["$or"] = [{"platforms": platform}, {"platform": platform}]
    if status:
        q["status"] = status
    docs = list(db.threats.find(q, {"_id": 0}).limit(300))
    if not docs:
        return [], platform, status
    scored = None
    if semantic and any(d.get("embedding") for d in docs):
        try:
            qv = embed(query)
            scored = sorted(docs, key=lambda d: _cosine(qv, d["embedding"]) if d.get("embedding") else -1, reverse=True)
        except Exception:
            scored = None
    if scored is None:
        scored = sorted(docs, key=lambda d: _keyword_score(query, d), reverse=True)
    for d in scored:
        d.pop("embedding", None)
    return scored[:k], platform, status


def format_threats(threats):
    out = []
    for t in threats:
        plats = ", ".join(t.get("platforms") or [t.get("platform", "?")])
        mit = "; ".join(t.get("mitigation") or []) or "not recorded"
        out.append(f"[{t.get('external_id') or t['threat_id']}] {t['name']} | platforms: {plats} | "
                   f"status: {t.get('status')} | severity: {t.get('severity')}\n"
                   f"  {(t.get('description') or '')[:350]}\n  Mitigation: {mit[:450]}")
    return "\n".join(out) or "(no matching curated threat records)"


def format_listing(threats, status, platform):
    label = " ".join(x for x in (status, platform) if x) or "Matching"
    if not threats:
        return f"No **{label}** threat records were found in the database."
    out = [f"## {label} threats ({len(threats)})\n"]
    for t in threats:
        plats = ", ".join(t.get("platforms") or [t.get("platform", "?")])
        steps = "\n".join(f"  {i}. {m}" for i, m in enumerate((t.get("mitigation") or [])[:4], 1)) or "  Not recorded."
        out.append(f"### {t['name']}\n"
                   f"- **ID:** {t.get('external_id') or t['threat_id']} | **Severity:** {t.get('severity')} | "
                   f"**Status:** {t.get('status')} | **Platforms:** {plats}\n"
                   f"- {(t.get('description') or '')[:300]}\n- **Mitigation:**\n{steps}\n")
    return "\n".join(out)


GENERIC = {"how", "what", "does", "about", "mitigate", "mitigation", "protect", "against", "steps",
           "procedure", "explain", "tell", "fix", "threat", "threats", "linux", "windows", "macos",
           "android", "ios", "platform", "from", "with", "this", "that", "can", "you", "please",
           "prevent", "stop", "remove", "show", "list", "which", "active", "resolved", "evolving",
           "anticipated"}


def best_match(db, query):
    """Return the curated threat whose name/CVE the question names (e.g. 'regreSSHion'), else None."""
    toks = {w for w in re.findall(r"[a-z0-9\-]+", query.lower()) if len(w) > 3 and w not in GENERIC}
    if not toks:
        return None
    best, score = None, 0
    for d in db.threats.find({"threat_id": {"$not": re.compile("^OSV-")}}, {"_id": 0, "embedding": 0}):
        hay = " ".join([d.get("name", ""), d.get("external_id") or "", d.get("threat_id", "")]).lower()
        sc = sum(1 for w in toks if w in hay)
        if sc > score:
            best, score = d, sc
    return best if score >= 1 else None
