# connectors/base_connector.py
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    @abstractmethod
    async def delete_all(self, location: dict, user_id: str) -> bool:
        """Delete all data for user from this system"""
        pass

    @abstractmethod
    async def delete_field(self, location_path: str, value: str) -> bool:
        """Delete a specific field/value from this system"""
        pass