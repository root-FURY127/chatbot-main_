# routes/user_routes.py
from fastapi import APIRouter, HTTPException, Query, Depends
from services.data_mapping_service import DataMappingService
from models.user_model import UserResponse, UserUpdate
from app.database import get_db

router = APIRouter()

def get_data_mapping_service(db=Depends(get_db)):
    return DataMappingService(db)

@router.get("/user-data", response_model=UserResponse)
async def get_user_data(
    user_id: str = Query(..., description="User ID"),
    data_svc: DataMappingService = Depends(get_data_mapping_service)
):
    """Retrieve all personal data for a user"""
    user = await data_svc.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Convert _id to str if present
    if "_id" in user:
        user["user_id"] = str(user["_id"])
    return user

@router.put("/update-user", response_model=UserResponse)
async def update_user(
    update: UserUpdate,
    data_svc: DataMappingService = Depends(get_data_mapping_service)
):
    """Update user's personal information"""
    updated = await data_svc.update_user(update.user_id, update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return updated

@router.get("/data-map")
async def get_data_map(
    user_id: str = Query(..., description="User ID"),
    data_svc: DataMappingService = Depends(get_data_mapping_service)
):
    """Get data map for a specific user (where their data resides)"""
    mapping = await data_svc.get_user_data_map(user_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="User data map not found")
    # Format response as per frontend contract
    user_email = mapping.get("email", "unknown")
    locations = [f"{loc['system']} {loc.get('collection', loc.get('bucket', ''))}" for loc in mapping.get("locations", [])]
    return {
        "user": user_email,
        "locations": locations
    }