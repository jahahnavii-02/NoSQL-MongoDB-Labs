from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.evidence_service import (
    add_threat_evidence,
    list_threat_evidence,
)

router = APIRouter(
    prefix="/api/threats/{threat_id}/evidence",
    tags=["Threat Evidence"],
)


class EvidenceCreate(BaseModel):
    source_name: str = Field(min_length=1, max_length=150)
    source_url: str = Field(min_length=1, max_length=2000)
    summary: str = Field(min_length=1, max_length=5000)
    published_at: Optional[datetime] = None


@router.post("/")
def create_evidence(threat_id: str, evidence: EvidenceCreate):
    try:
        saved = add_threat_evidence(
            threat_id=threat_id,
            source_name=evidence.source_name,
            source_url=evidence.source_url,
            summary=evidence.summary,
            published_at=evidence.published_at,
        )
        return {
            "message": "Threat evidence recorded successfully.",
            "evidence": saved,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/")
def get_evidence(threat_id: str):
    return {
        "threat_id": threat_id,
        "evidence": list_threat_evidence(threat_id),
    }
