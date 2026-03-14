import httpx
from typing import Any, Optional

class DeletionService:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)

    async def delete_field(self, user_id: str, field: str, value: Any, logger) -> bool:
        """Delete a specific field via POST with JSON body."""
        url = f"{self.base_url}/api/delete-field"
        payload = {
            "user_id": user_id,
            "field": field
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            await logger.log_action(user_id, f"delete_field:{field}", field)
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error deleting field: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            print(f"Unexpected error deleting field: {e}")
            return False

    async def delete_all_user_data(self, user_id: str, logger) -> bool:
        """Delete all data via POST with JSON body."""
        url = f"{self.base_url}/api/delete-all"
        payload = {"user_id": user_id}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            await logger.log_action(user_id, "delete_all", None)
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error deleting all data: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            print(f"Unexpected error deleting all data: {e}")
            return False

    async def get_user_data(self, user_id: str) -> Optional[dict]:
        """Fetch user data via GET with query parameter (if needed)."""
        url = f"{self.base_url}/api/get-data"
        params = {"user_id": user_id}
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching user data: {e}")
            return None

    async def close(self):
        await self.client.aclose()