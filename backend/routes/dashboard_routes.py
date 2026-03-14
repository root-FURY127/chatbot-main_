from fastapi import APIRouter, Depends
from services.data_mapping_service import DataMappingService
from services.consent_service import ConsentService
from services.deletion_service import DeletionService

router = APIRouter()

@router.get("/stats")
async def get_stats(
    data_svc: DataMappingService = Depends(),
    consent_svc: ConsentService = Depends(),
    deletion_svc: DeletionService = Depends()
):
    total_users = await data_svc.get_total_users()
    total_locations = await data_svc.get_total_locations()
    pending = await deletion_svc.get_pending_count()
    active_consents = await consent_svc.get_active_count()
    return {
        "total_users": total_users,
        "total_data_locations": total_locations,
        "pending_deletion_requests": pending,
        "active_consents": active_consents
    }