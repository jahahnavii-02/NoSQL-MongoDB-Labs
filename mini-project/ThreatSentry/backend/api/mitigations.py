from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.core.config import settings
from backend.services.mongo_store import get_mongo_client
from backend.services import mitigation_service as ms

router = APIRouter(prefix="/api/mitigations", tags=["Confirmation-based Mitigation"])


class ProposeRequest(BaseModel):
    target: str = Field(min_length=1, max_length=200, description="package name, advisory id, or 'all affected'")


def _with_db(fn):
    client = get_mongo_client()
    try:
        return fn(client[settings.MONGO_DATABASE])
    finally:
        client.close()


@router.get("/")
def plans():
    return {"dry_run": settings.MITIGATION_DRY_RUN, "plans": _with_db(ms.list_plans)}


@router.post("/propose")
def propose(body: ProposeRequest):
    return {"plans": _with_db(lambda db: ms.propose(db, body.target))}


@router.post("/{code}/approve")
def approve(code: str):
    return {"result": _with_db(lambda db: ms.decide(db, code, True))}


@router.post("/{code}/reject")
def reject(code: str):
    return {"result": _with_db(lambda db: ms.decide(db, code, False))}
