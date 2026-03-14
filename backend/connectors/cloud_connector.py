from .base_connector import BaseConnector

class CloudConnector(BaseConnector):
    """Mock cloud storage connector"""
    async def delete_all(self, location: dict, user_id: str) -> bool:
        print(f"Deleting all objects for user {user_id} from bucket {location.get('bucket')}")
        return True

    async def delete_field(self, location_path: str, value: str) -> bool:
        print(f"Deleting object containing {value} from cloud location {location_path}")
        return True