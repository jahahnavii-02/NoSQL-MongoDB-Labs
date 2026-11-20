from fastapi import APIRouter, HTTPException

from backend.services.linux_scanner import run_linux_scan

router = APIRouter(prefix="/api/scans", tags=["Linux Security Scanning"])


@router.post("/linux")
def scan_linux():
    try:
        return run_linux_scan()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Linux scan failed: {str(exc)[:300]}",
        )
