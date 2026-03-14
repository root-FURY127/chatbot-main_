from .base_connector import BaseConnector

class MongoDBConnector(BaseConnector):
    def __init__(self, db):
        self.db = db  # This is our main app db, but in real scenario might connect to external MongoDB

    async def delete_all(self, location: dict, user_id: str) -> bool:
        """Delete user document from MongoDB collection"""
        # location example: {"system": "MongoDB", "collection": "users", ...}
        collection_name = location.get("collection")
        if not collection_name:
            return False
        collection = self.db[collection_name]
        # Delete based on user_id field
        result = await collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    async def delete_field(self, location_path: str, value: str) -> bool:
        """Delete field from MongoDB document"""
        # location_path like "MongoDB.users.aadhaar"
        parts = location_path.split('.')
        if len(parts) < 3:
            return False
        collection_name = parts[1]
        field = parts[2]
        collection = self.db[collection_name]
        # We need to know which document contains this value. For simplicity, assume we can find by value.
        # In real scenario, we'd have more context.
        result = await collection.update_one(
            {field: value},
            {"$unset": {field: ""}}
        )
        return result.modified_count > 0