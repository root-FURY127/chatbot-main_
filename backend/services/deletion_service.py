from typing import Optional
from connectors.mongodb_connector import MongoDBConnector
from connectors.sql_connector import SQLConnector
from connectors.file_scanner import FileScanner
from connectors.cloud_connector import CloudConnector
from services.data_mapping_service import DataMappingService
from services.compliance_logger import ComplianceLogger
from services.pii_detection_service import PIIDetectionService

class DeletionService:
    def __init__(self, db):
        self.db = db
        self.data_svc = DataMappingService(db)
        self.pii_svc = PIIDetectionService()
        # Initialize connectors (mock implementations)
        self.connectors = {
            "MongoDB": MongoDBConnector(db),
            "PostgreSQL": SQLConnector(),
            "AWS S3": CloudConnector(),
            "file": FileScanner()
        }

    async def delete_all_user_data(self, user_id: str, logger: ComplianceLogger):
        """Delete all data for a user across all systems"""
        # Get user data map
        user_map = await self.data_svc.get_user_data_map(user_id)
        if not user_map:
            # Log error
            await logger.log({
                "user_id": user_id,
                "action": "delete_all",
                "status": "failed",
                "error": "User data map not found"
            })
            return

        systems_cleaned = 0
        locations_affected = []
        for loc in user_map.get("locations", []):
            system = loc.get("system")
            connector = self.connectors.get(system)
            if connector:
                success = await connector.delete_all(loc, user_id)
                if success:
                    systems_cleaned += 1
                    locations_affected.append(f"{system}.{loc.get('collection', loc.get('bucket', ''))}")
        
        # After deletion, update data map (remove all locations for user)
        await self.db.data_locations.delete_one({"user_id": user_id})
        
        # Log compliance
        await logger.log({
            "user_id": user_id,
            "action": "delete_all",
            "systems_cleaned": systems_cleaned,
            "status": "completed",
            "details": {"locations_affected": locations_affected}
        })

    async def delete_field(self, user_id: str, field: str, value: Optional[str], logger: ComplianceLogger):
        """Delete a specific field/value for a user"""
        # Get user data to find value if not provided
        user = await self.data_svc.get_user_by_id(user_id)
        if not user:
            await logger.log({
                "user_id": user_id,
                "action": "delete_field",
                "field": field,
                "status": "failed",
                "error": "User not found"
            })
            return

        if not value:
            value = user.get(field)
            if not value:
                await logger.log({
                    "user_id": user_id,
                    "action": "delete_field",
                    "field": field,
                    "status": "failed",
                    "error": f"Field {field} not found for user"
                })
                return

        # Detect PII type (optional, for logging)
        pii_type = self.pii_svc.detect_type(value)

        # Find all locations where this value appears
        locations = await self.data_svc.find_value_in_locations(value)
        
        systems_cleaned = 0
        for loc_path in locations:
            # Parse loc_path (e.g., "MongoDB.users.aadhaar")
            parts = loc_path.split('.')
            system = parts[0]
            connector = self.connectors.get(system)
            if connector:
                # For simplicity, we pass the full location info; connector needs to know how to delete.
                # In a real system, we'd have a more structured location object.
                success = await connector.delete_field(loc_path, value)
                if success:
                    systems_cleaned += 1

        # Update data map: remove entries with this value
        await self.data_svc.remove_location_entries(user_id, value)

        # Optionally, update the user document in MongoDB to remove the field
        await self.db.users.update_one({"_id": user["_id"]}, {"$unset": {field: ""}})

        # Log compliance
        await logger.log({
            "user_id": user_id,
            "action": "delete_field",
            "field": field,
            "pii_type": pii_type,
            "systems_cleaned": systems_cleaned,
            "status": "completed",
            "details": {
                "input": value,
                "locations_affected": locations
            }
        })

    async def get_pending_count(self) -> int:
        """Count pending deletion requests (simplified)"""
        # If we had a deletion_requests collection, count pending.
        # For hackathon, return 0 or mock.
        return 0

    async def get_pending_requests(self) -> list:
        """Return list of pending requests"""
        return []