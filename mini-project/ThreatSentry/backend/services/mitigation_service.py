"""Confirmation-based mitigation. Flow: propose -> user approves in chat/UI -> execute -> audit.
Safety: commands are built HERE from a validated package name (never taken from the model or
the request); only 'apt-get install --only-upgrade'; dry-run by default; every step is audited."""
import re
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

from backend.core.config import settings
from backend.services.mongo_store import get_mongo_client

PKG_RE = re.compile(r"^[a-z0-9][a-z0-9+.\-]{0,99}$")
FIXABLE = {"affected"}


def _now():
    return datetime.now(timezone.utc)


def _audit(db, event, plan_id, detail=""):
    db.audit_events.insert_one({"event": event, "plan_id": plan_id, "detail": detail[:500], "created_at": _now()})


def build_command(package):
    if not PKG_RE.match(package or ""):
        raise ValueError("Unsafe or invalid package name.")
    return ["apt-get", "install", "--only-upgrade", "-y", package]


def _run(cmd):
    """Run a command on the monitored Ubuntu system (WSL from Windows, or locally in Linux/Docker)."""
    if settings.SCANNER_MODE == "wsl":
        full = ["wsl.exe", "-d", settings.WSL_DISTRIBUTION, "-u", "root", "--"] + cmd
    else:
        full = cmd
    p = subprocess.run(full, capture_output=True, text=True, timeout=900)
    return p.returncode, (p.stdout + p.stderr).strip()


def propose(db, text):
    """Create proposed plans for affected findings in the latest scan matching `text`
    (a package name, CVE/advisory id, or 'all'). Returns list of plan dicts."""
    scan = db.scan_runs.find_one({}, {"_id": 0, "scan_id": 1}, sort=[("started_at", -1)])
    if not scan:
        return []
    t = text.lower()
    out, seen = [], set()
    for f in db.findings.find({"scan_id": scan["scan_id"], "assessment": {"$in": list(FIXABLE)}}, {"_id": 0}):
        pkg = (f.get("package") or "").split(":")[0]
        ids = " ".join(str(f.get(k) or "") for k in ("external_id", "threat_id", "name")).lower()
        wanted = "all affected" in t or "everything" in t or re.search(rf"\b{re.escape(pkg.lower())}\b", t) or (
            ids.strip() and any(tok in t for tok in ids.split() if len(tok) > 6))
        if not wanted or pkg in seen or not PKG_RE.match(pkg):
            continue
        seen.add(pkg)
        existing = db.mitigation_plans.find_one({"package": pkg, "status": "proposed"}, {"_id": 0})
        if existing:
            out.append(existing); continue
        plan = {"plan_id": str(uuid4()), "finding_id": f.get("finding_id"), "package": pkg,
                "installed_version": f.get("installed_version"), "advisory": f.get("external_id") or f.get("threat_id"),
                "severity": f.get("severity"), "command": " ".join(build_command(pkg)),
                "verify": f"dpkg-query -W {pkg}", "status": "proposed", "dry_run": settings.MITIGATION_DRY_RUN,
                "created_at": _now()}
        db.mitigation_plans.insert_one(dict(plan))
        _audit(db, "proposed", plan["plan_id"], plan["command"])
        out.append(plan)
    return out


def _find_plan(db, code):
    return db.mitigation_plans.find_one({"plan_id": {"$regex": f"^{re.escape(code.lower())}"}}, {"_id": 0})


def decide(db, code, approve):
    plan = _find_plan(db, code)
    if not plan:
        return f"No mitigation plan starts with `{code}`."
    pid = plan["plan_id"]
    if plan["status"] != "proposed":
        return f"Plan `{pid[:8]}` is already **{plan['status']}**."
    if not approve:
        db.mitigation_plans.update_one({"plan_id": pid}, {"$set": {"status": "rejected", "decided_at": _now()}})
        _audit(db, "rejected", pid)
        return f"Plan `{pid[:8]}` rejected. Nothing was changed."
    db.mitigation_plans.update_one({"plan_id": pid}, {"$set": {"status": "approved", "decided_at": _now()}})
    _audit(db, "approved", pid, "user confirmed in chat/UI")
    cmd = build_command(plan["package"])  # rebuilt, never read back from the DB
    if settings.MITIGATION_DRY_RUN:
        db.mitigation_plans.update_one({"plan_id": pid}, {"$set": {"status": "dry_run", "result": "DRY RUN: " + " ".join(cmd)}})
        _audit(db, "dry_run", pid, " ".join(cmd))
        return (f"Plan `{pid[:8]}` approved - **dry run only** (MITIGATION_DRY_RUN=true).\n\n"
                f"Would run: `{' '.join(cmd)}`\n\nSet MITIGATION_DRY_RUN=false to apply it for real.")
    try:
        rc, out = _run(cmd)
    except Exception as exc:
        rc, out = 1, str(exc)
    status = "executed" if rc == 0 else "failed"
    db.mitigation_plans.update_one({"plan_id": pid}, {"$set": {"status": status, "result": out[-800:], "executed_at": _now()}})
    _audit(db, status, pid, out[-300:])
    return (f"Plan `{pid[:8]}` **{status}**.\n\nVerify with: `{plan['verify']}` and re-run the scan.\n\n```\n{out[-600:]}\n```")


def format_plans(plans):
    if not plans:
        return ("No fixable findings matched. Run a Linux scan first, and name a package that is "
                "**confirmed affected** (unknown or not-affected findings are never auto-fixed).")
    lines = ["## Proposed mitigation plans (nothing has been changed)\n"]
    for p in plans:
        lines.append(f"- `{p['plan_id'][:8]}` **{p['package']}** {p.get('installed_version','')} - {p.get('advisory')} "
                     f"({p.get('severity')})\n  Command: `{p['command']}`")
    lines.append("\nReply **approve <id>** to apply or **reject <id>** to discard. "
                 "Back up important data first; upgrades can restart services.")
    return "\n".join(lines)


COMMAND_RE = re.compile(r"^\s*/?(approve|reject)\s+([0-9a-f]{6,36})\b", re.I)
FIX_RE = re.compile(r"^\s*(please\s+|can you\s+|could you\s+)?(fix|remediate|mitigate|patch|upgrade)\b", re.I)


def handle_chat_command(db, message):
    """Return a reply string if the message is a mitigation command, else None."""
    m = COMMAND_RE.match(message)
    if m:
        return decide(db, m.group(2), m.group(1).lower() == "approve")
    if FIX_RE.search(message):
        return format_plans(propose(db, message))
    return None


def list_plans(db, limit=50):
    return list(db.mitigation_plans.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))
