# services/compliance_logger.py
import datetime
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

class ComplianceLogger:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        """
        Initialize the compliance logger.
        If db is provided, logs will be stored in MongoDB.
        Otherwise, they will be stored in memory (fallback).
        """
        self.db = db
        self.logs: List[Dict] = []  # in‑memory fallback

    async def log_action(self, user_id: str, action: str, field: str = None):
        """Store a compliance log entry."""
        log_entry = {
            "user_id": user_id,
            "action": action,
            "field": field,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        # If MongoDB is available, store there
        if self.db is not None:
            try:
                result = await self.db.compliance_logs.insert_one(log_entry)
                print(f"Compliance log stored in MongoDB with id: {result.inserted_id}")
                return result.inserted_id
            except Exception as e:
                print(f"Failed to store log in MongoDB, falling back to memory: {e}")
                self.logs.append(log_entry)
                return None
        else:
            # Fallback to in‑memory
            self.logs.append(log_entry)
            print(f"Compliance log (in‑memory): {log_entry}")
            return None