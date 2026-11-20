from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.threat_service import (
    create_threat,
    get_threat,
    list_threats,
    update_threat_status,
    ThreatValidationError,
)

router = APIRouter(prefix="/api/threats", tags=["Threat Intelligence"])


class ThreatCreate(BaseModel):
    threat_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    platform: str = Field(min_length=1, max_length=100)
    severity: str
    status: str = "Anticipated"
    source: Optional[str] = None


class ThreatStatusUpdate(BaseModel):
    status: str


@router.post("/")
def add_threat(threat: ThreatCreate):
    try:
        return {
            "message": "Threat created successfully.",
            "threat": create_threat(**threat.dict()),
        }
    except ThreatValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/")
def get_threats(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 100,
):
    try:
        return {
            "threats": list_threats(status, platform, limit)
        }
    except ThreatValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{threat_id}")
def get_threat_by_id(threat_id: str):
    threat = get_threat(threat_id)

    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found.")

    return threat


@router.patch("/{threat_id}/status")
def change_threat_status(
    threat_id: str,
    update: ThreatStatusUpdate,
):
    try:
        updated = update_threat_status(threat_id, update.status)

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Threat not found.",
            )

        return {
            "message": "Threat status updated.",
            "threat": get_threat(threat_id),
        }
    except ThreatValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

