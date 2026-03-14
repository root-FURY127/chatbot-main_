# models/logs_model.py
from pydantic import BaseModel
from typing import Optional, Any, Dict

class ComplianceLogResponse(BaseModel):
    log_id: str
    user_id: str
    action: str
    field: Optional[str] = None
    systems_cleaned: Optional[int] = None
    status: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None