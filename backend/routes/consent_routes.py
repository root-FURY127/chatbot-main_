from fastapi import APIRouter, HTTPException, Query, Depends
from services.consent_service import ConsentService
from app.database import get_db

router = APIRouter()

def get_consent_service(db=Depends(get_db)):
    return ConsentService(db)

@router.get("/consents")
async def get_consents(
    user_id: str = Query(..., description="User ID"),
    consent_svc: ConsentService = Depends(get_consent_service)
):
    """Get all consents for a user"""
    consents = await consent_svc.get_user_consents(user_id)
    return consents

@router.post("/withdraw-consent")
async def withdraw_consent(
    request: dict,
    consent_svc: ConsentService = Depends(get_consent_service)
):
    """Withdraw a specific consent"""
    consent_id = request.get("consent_id")
    user_id = request.get("user_id")
    if not consent_id or not user_id:
        raise HTTPException(status_code=400, detail="consent_id and user_id are required")
    result = await consent_svc.withdraw_consent(consent_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Consent not found or already withdrawn")
    return result