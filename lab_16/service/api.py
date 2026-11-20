from fastapi import FastAPI, HTTPException, Query
from .db import DatabaseHub
from .hybrid import HybridFraudService

app = FastAPI(title="Lab 16 Hybrid NoSQL Fraud Detection API", version="1.0.0")
hub = None
service = None


@app.on_event("startup")
def startup():
    global hub, service
    hub = DatabaseHub()
    service = HybridFraudService(hub)


@app.on_event("shutdown")
def shutdown():
    if hub:
        hub.close()


@app.get("/health")
def health():
    return {"status": "running", "service": "lab16-hybrid"}


@app.get("/transaction/{txn_id}")
def transaction(txn_id: str):
    try:
        result = service.get_transaction(txn_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable")


@app.get("/user/{user_id}")
def user_profile(user_id: str):
    try:
        return service.get_user_profile(user_id)
    except Exception:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable")


@app.get("/fraud-rings/{user_id}")
def fraud_rings(user_id: str, max_hops: int = Query(default=3, ge=1, le=5)):
    try:
        return service.detect_fraud_rings(user_id, max_hops)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable")
