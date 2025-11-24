import httpx
import os
import base64
from typing import Optional, Dict, Any, List

class LeverClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("LEVER_API_KEY")
        if not self.api_key:
            raise ValueError("LEVER_API_KEY environment variable is not set")
        
        self.base_url = os.environ.get("LEVER_API_BASE_URL", "https://api.lever.co/v1")
        # Lever uses Basic Auth with the API key as the username and an empty password
        auth_string = f"{self.api_key}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }

    async def get_candidates(self, limit: int = 10, offset: Optional[str] = None) -> Dict[str, Any]:
        params = {"limit": limit}
        if offset:
            params["offset"] = offset
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/candidates",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/candidates/{candidate_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def create_requisition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/requisitions",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
