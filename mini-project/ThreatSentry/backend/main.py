from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.services.connectivity import check_all_services
from backend.api.threats import router as threats_router
from backend.api.evidence import router as evidence_router
from backend.api.intelligence import router as intelligence_router
from backend.api.scans import router as scans_router
from backend.api.ubuntu_sync import router as ubuntu_sync_router
from backend.api.chat import router as chat_router
from backend.api.mitigations import router as mitigations_router

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Offline threat intelligence, Linux vulnerability analysis "
        "and confirmation-based mitigation assistant."
    ),
    version="0.7.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(threats_router)
app.include_router(evidence_router)
app.include_router(intelligence_router)
app.include_router(scans_router)
app.include_router(ubuntu_sync_router)
app.include_router(chat_router)
app.include_router(mitigations_router)


@app.get("/")
def root():
    return {
        "application": settings.APP_NAME,
        "status": "running",
        "message": "ThreatSentry API is ready.",
    }


@app.get("/api/health")
def health():
    services = check_all_services()
    connected = sum(
        1 for item in services.values()
        if item.get("status") == "connected"
    )

    return {
        "status": "ok" if all(
            services.get(name, {}).get("status") == "connected"
            for name in ("mongodb", "ollama")
        ) else "degraded",
        "note": "MongoDB and Ollama are required; Cassandra and Neo4j are optional (Labs 16/18).",
        "application": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "connected_services": connected,
        "total_services": len(services),
        "services": services,
    }
