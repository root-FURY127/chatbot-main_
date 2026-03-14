from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from services.deletion_service import DeletionService
from services.compliance_logger import ComplianceLogger
from app.database import get_db

router = APIRouter()

def get_deletion_service(db=Depends(get_db)):
    return DeletionService(db)

def get_compliance_logger(db=Depends(get_db)):
    return ComplianceLogger(db)

@router.post("/delete-user")
async def delete_user(
    request: dict,
    background_tasks: BackgroundTasks,
    deletion_svc: DeletionService = Depends(get_deletion_service),
    logger: ComplianceLogger = Depends(get_compliance_logger)
):
    """Delete all personal data of a user across all systems"""
    user_id = request.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    # Start background task
    background_tasks.add_task(deletion_svc.delete_all_user_data, user_id, logger)
    return {"status": "processing", "message": f"Deletion of all data for user {user_id} started"}

@router.post("/delete-field")
async def delete_field(
    request: dict,
    background_tasks: BackgroundTasks,
    deletion_svc: DeletionService = Depends(get_deletion_service),
    logger: ComplianceLogger = Depends(get_compliance_logger)
):
    """Delete a specific PII field for a user"""
    user_id = request.get("user_id")
    field = request.get("field")
    value = request.get("value")
    if not user_id or not field:
        raise HTTPException(status_code=400, detail="user_id and field are required")
    background_tasks.add_task(deletion_svc.delete_field, user_id, field, value, logger)
    return {"status": "processing", "message": f"Deletion of {field} for user {user_id} started"}