"""Load curated multi-platform threats (Linux, Windows, macOS, Android, iOS) with all four
lifecycle statuses, then embed them with Ollama for semantic retrieval.
Run:  python -m ingestion.seed_curated            (add --no-embed to skip embeddings)"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from backend.services.mongo_store import get_mongo_client, ensure_schema
from backend.services.retrieval import embed
from backend.core.config import settings

DATA = Path(__file__).with_name("curated_threats.json")


def main(do_embed=True):
    ensure_schema()
    records = json.loads(DATA.read_text(encoding="utf-8"))
    client = get_mongo_client()
    try:
        db = client[settings.MONGO_DATABASE]
        now = datetime.now(timezone.utc)
        ok_embed = 0
        for r in records:
            r["updated_at"] = now
            if do_embed:
                try:
                    r["embedding"] = embed(f"{r['name']}. {r['description']} Platforms: {', '.join(r['platforms'])}. "
                                           f"Status: {r['status']}. Mitigation: {'; '.join(r['mitigation'])}")
                    ok_embed += 1
                except Exception as exc:
                    print("embedding skipped (is Ollama up with", settings.OLLAMA_EMBED_MODEL, "?):", type(exc).__name__)
                    do_embed = False
            db.threats.update_one({"threat_id": r["threat_id"]}, {"$set": r, "$setOnInsert": {"created_at": now}}, upsert=True)
        print(f"Seeded {len(records)} curated threats; embedded {ok_embed}.")
    finally:
        client.close()


if __name__ == "__main__":
    main("--no-embed" not in sys.argv)
