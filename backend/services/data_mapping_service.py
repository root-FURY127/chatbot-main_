from typing import List, Dict, Any, Optional
from bson import ObjectId

class DataMappingService:
    def __init__(self, db):
        self.db = db
        self.users_collection = db.users
        self.locations_collection = db.data_locations

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by user_id (string)"""
        # Try to convert to ObjectId if it's a valid 24-char hex
        try:
            obj_id = ObjectId(user_id)
            user = await self.users_collection.find_one({"_id": obj_id})
        except:
            # If not a valid ObjectId, treat as string field 'user_id'
            user = await self.users_collection.find_one({"user_id": user_id})
        return user

    async def update_user(self, user_id: str, update_data: dict) -> Optional[Dict[str, Any]]:
        """Update user fields"""
        # Determine query
        try:
            obj_id = ObjectId(user_id)
            query = {"_id": obj_id}
        except:
            query = {"user_id": user_id}
        result = await self.users_collection.update_one(query, {"$set": update_data})
        if result.modified_count == 1:
            return await self.get_user_by_id(user_id)
        return None

    async def get_user_data_map(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get data locations for user"""
        # First get user to have email
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        # Get locations document
        loc_doc = await self.locations_collection.find_one({"user_id": user_id})
        if not loc_doc:
            # Return empty locations
            return {"user_id": user_id, "email": user.get("email"), "locations": []}
        loc_doc["email"] = user.get("email")
        return loc_doc

    async def find_value_in_locations(self, value: str) -> List[str]:
        """Search across all location records for a specific value"""
        cursor = self.locations_collection.find({"locations.value": value})
        results = []
        async for doc in cursor:
            for loc in doc.get("locations", []):
                if loc.get("value") == value:
                    system = loc.get("system", "unknown")
                    container = loc.get("collection") or loc.get("bucket") or loc.get("table") or ""
                    field = loc.get("field", "")
                    results.append(f"{system}.{container}.{field}".rstrip('.'))
        return results

    async def remove_location_entries(self, user_id: str, value: str):
        """Remove location entries that contain a specific value"""
        await self.locations_collection.update_one(
            {"user_id": user_id},
            {"$pull": {"locations": {"value": value}}}
        )

    async def get_total_users(self) -> int:
        return await self.users_collection.count_documents({})

    async def get_total_locations(self) -> int:
        pipeline = [{"$unwind": "$locations"}, {"$count": "total"}]
        result = await self.locations_collection.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0

    async def get_all_locations_summary(self) -> List[Dict]:
        """Return summary of all data sources (for dashboard)"""
        # Simplified: group by system
        pipeline = [
            {"$unwind": "$locations"},
            {"$group": {
                "_id": "$locations.system",
                "details": {"$addToSet": {
                    "database": "$locations.database",
                    "collection": "$locations.collection",
                    "bucket": "$locations.bucket"
                }}
            }}
        ]
        cursor = self.locations_collection.aggregate(pipeline)
        result = []
        async for doc in cursor:
            system = doc["_id"]
            # Flatten details
            containers = set()
            for d in doc["details"]:
                if d.get("collection"):
                    containers.add(d["collection"])
                if d.get("bucket"):
                    containers.add(d["bucket"])
            result.append({
                "system": system,
                "containers": list(containers)
            })
        return result