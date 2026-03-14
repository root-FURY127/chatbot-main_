from .base_connector import BaseConnector

class SQLConnector(BaseConnector):
    """Mock SQL connector for demonstration"""
    async def delete_all(self, location: dict, user_id: str) -> bool:
        # Simulate deletion from SQL
        print(f"Deleting all data for user {user_id} from SQL table {location.get('table')}")
        return True

    async def delete_field(self, location_path: str, value: str) -> bool:
        print(f"Deleting field {location_path} with value {value} from SQL")
        return True