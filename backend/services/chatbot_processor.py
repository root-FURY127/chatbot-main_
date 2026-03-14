from services.deletion_service import DeletionService
from services.compliance_logger import ComplianceLogger

class ChatbotProcessor:
    def __init__(self, db):
        self.db = db
        self.deletion_svc = DeletionService(db)
        self.logger = ComplianceLogger(db)

    async def parse_and_execute(self, user_id: str, message: str) -> dict:
        """Parse message and trigger appropriate action"""
        msg_lower = message.lower()
        # Simple keyword matching
        if "delete all my data" in msg_lower or "delete all data" in msg_lower:
            # Trigger full deletion (background task would be better, but for API response we can just start)
            # In a real system, we might return a job ID.
            await self.deletion_svc.delete_all_user_data(user_id, self.logger)
            return {"action": "delete_all", "status": "completed", "message": "All data deletion initiated"}
        elif "delete my aadhaar" in msg_lower or "remove aadhaar" in msg_lower:
            await self.deletion_svc.delete_field(user_id, "aadhaar", None, self.logger)
            return {"action": "delete_field", "field": "aadhaar", "status": "completed"}
        elif "delete my pan" in msg_lower or "remove pan" in msg_lower:
            await self.deletion_svc.delete_field(user_id, "pan", None, self.logger)
            return {"action": "delete_field", "field": "pan", "status": "completed"}
        elif "delete my phone" in msg_lower or "remove phone" in msg_lower:
            await self.deletion_svc.delete_field(user_id, "phone", None, self.logger)
            return {"action": "delete_field", "field": "phone", "status": "completed"}
        elif "delete my email" in msg_lower or "remove email" in msg_lower:
            await self.deletion_svc.delete_field(user_id, "email", None, self.logger)
            return {"action": "delete_field", "field": "email", "status": "completed"}
        else:
            return {"action": "unknown", "message": "Command not recognized"}