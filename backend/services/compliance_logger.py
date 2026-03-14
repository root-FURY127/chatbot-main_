from typing import Optional, List, Dict, Any
from datetime import datetime

class ComplianceLogger:
    def __init__(self, db):
        self.db = db
        self.collection = db.compliance_logs

    async def log(self, entry: Dict[str, Any]):
        """Insert a log entry with timestamp"""
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        await self.collection.insert_one(entry)

    async def get_logs(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        query = {}
        if user_id:
            query["user_id"] = user_id
        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        logs = await cursor.to_list(length=limit)
        # Convert ObjectId to string
        for log in logs:
            log["log_id"] = str(log["_id"])
            log.pop("_id", None)
        return logs