from typing import List, Dict, Any, Optional
from datetime import datetime

class ConsentService:
    def __init__(self, db):
        self.db = db
        self.collection = db.consents

    async def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id})
        consents = await cursor.to_list(length=100)
        # Convert ObjectId to string
        for c in consents:
            c["consent_id"] = str(c["_id"])
            c.pop("_id", None)
        return consents

    async def get_active_count(self) -> int:
        return await self.collection.count_documents({"status": "active"})

    async def withdraw_consent(self, consent_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        result = await self.collection.update_one(
            {"_id": ObjectId(consent_id), "user_id": user_id, "status": "active"},
            {"$set": {"status": "withdrawn", "withdrawn_at": datetime.utcnow().isoformat() + "Z"}}
        )
        if result.modified_count == 1:
            consent = await self.collection.find_one({"_id": ObjectId(consent_id)})
            consent["consent_id"] = str(consent["_id"])
            consent.pop("_id")
            return consent
        return None