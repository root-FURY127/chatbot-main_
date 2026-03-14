# models/consent_model.py
from pydantic import BaseModel
from typing import Optional

class ConsentResponse(BaseModel):
    consent_id: str
    user_id: str
    purpose: str
    status: str  # active, withdrawn
    granted_at: str
    withdrawn_at: Optional[str] = None

class ConsentWithdraw(BaseModel):
    consent_id: str
    user_id: str