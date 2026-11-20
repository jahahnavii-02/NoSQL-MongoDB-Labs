from fastapi import APIRouter, HTTPException
from requests import RequestException

from ingestion.osv_ingest import ingest_osv_vulnerability

router = APIRouter(
    prefix="/api/intel",
    tags=["Threat Intelligence Ingestion"],
)


@router.post("/osv/{vulnerability_id}")
def import_osv_record(vulnerability_id: str):
    try:
        return {
            "message": "OSV intelligence processed successfully.",
            "record": ingest_osv_vulnerability(vulnerability_id),
        }

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except RequestException:
        raise HTTPException(
            status_code=502,
            detail="OSV could not be reached. Check internet connectivity.",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="OSV ingestion failed. Check the backend logs.",
        )
