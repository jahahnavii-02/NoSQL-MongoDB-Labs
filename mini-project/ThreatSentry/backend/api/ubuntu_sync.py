from fastapi import APIRouter, HTTPException

from ingestion.ubuntu_osv_sync import sync_ubuntu_osv

router = APIRouter(
    prefix="/api/intel/ubuntu",
    tags=["Ubuntu Threat Intelligence"],
)


@router.post("/sync")
def sync_ubuntu_intelligence():
    try:
        return sync_ubuntu_osv()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ubuntu OSV sync failed: {str(exc)[:400]}",
        )
