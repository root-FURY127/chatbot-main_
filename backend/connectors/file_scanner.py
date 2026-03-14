# connectors/file_scanner.py
from .base_connector import BaseConnector

class FileScanner(BaseConnector):
    """Mock file scanner for demonstration"""
    async def delete_all(self, location: dict, user_id: str) -> bool:
        print(f"Deleting all files for user {user_id} from {location.get('file_path')}")
        return True

    async def delete_field(self, location_path: str, value: str) -> bool:
        print(f"Removing value {value} from file {location_path}")
        return True