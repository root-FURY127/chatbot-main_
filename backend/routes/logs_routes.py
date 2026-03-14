from fastapi import APIRouter, Query, Depends
from services.compliance_logger import ComplianceLogger
from app.database import get_db

router = APIRouter()

def get_compliance_logger(db=Depends(get_db)):
    return ComplianceLogger(db)

@router.get("/compliance-logs")
async def get_compliance_logs(
    user_id: str = Query(None, description="Filter by user ID"),
    limit: int = Query(100, description="Max number of logs to return"),
    logger: ComplianceLogger = Depends(get_compliance_logger)
):
    """Retrieve compliance logs, optionally filtered by user"""
    logs = await logger.get_logs(user_id=user_id, limit=limit)
    return logs