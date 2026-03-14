from fastapi import APIRouter, HTTPException, Query, Depends
from services.pii_detection_service import PIIDetectionService
from services.data_mapping_service import DataMappingService
from app.database import get_db

router = APIRouter()

def get_pii_service():
    return PIIDetectionService()

def get_data_mapping_service(db=Depends(get_db)):
    return DataMappingService(db)

@router.get("/pii-detection")
async def detect_pii(
    value: str = Query(..., description="Value to detect PII type"),
    pii_svc: PIIDetectionService = Depends(get_pii_service),
    mapping_svc: DataMappingService = Depends(get_data_mapping_service)
):
    """Detect PII type from a given input value and find where it appears"""
    pii_type = pii_svc.detect_type(value)
    locations = await mapping_svc.find_value_in_locations(value)
    return {
        "input_value": value,
        "type": pii_type,
        "locations_found": locations
    }