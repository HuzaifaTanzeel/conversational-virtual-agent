"""
Tavus CVI client service.
Replaces liveavatar.py — handles Tavus conversation lifecycle.
"""

import json
from typing import Any, Optional

import httpx

from app.config import get_settings

TAVUS_BASE_URL = "https://tavusapi.com"


class TavusError(RuntimeError):
    """Raised when the Tavus API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Tavus API {status_code}: {detail}")


class TavusClient:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        self._api_key = api_key or get_settings().tavus_api_key
        self._timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self._api_key, "Content-Type": "application/json"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.request(
                method, f"{TAVUS_BASE_URL}{path}", headers=self._headers, **kwargs
            )
            if resp.status_code >= 400:
                detail = resp.text
                try:
                    body = resp.json()
                    if isinstance(body, dict):
                        detail = str(body.get("message") or body.get("error") or detail)
                except (json.JSONDecodeError, ValueError):
                    pass
                raise TavusError(resp.status_code, detail)
            if resp.content:
                return resp.json()
            return None

    async def create_conversation(
        self,
        replica_id: str,
        persona_id: str,
        conversation_name: str = "Avatour Sales Call",
        custom_greeting: str = "",
        conversational_context: str = "",
        properties: dict | None = None,
    ) -> dict:
        """Create a Tavus conversation. Returns conversation_id and conversation_url."""
        payload: dict[str, Any] = {
            "replica_id": replica_id,
            "persona_id": persona_id,
            "conversation_name": conversation_name,
        }
        if custom_greeting:
            payload["custom_greeting"] = custom_greeting
        if conversational_context:
            payload["conversational_context"] = conversational_context
        if properties:
            payload["properties"] = properties
        return await self._request("POST", "/v2/conversations", json=payload)

    async def end_conversation(self, conversation_id: str) -> dict:
        await self._request("DELETE", f"/v2/conversations/{conversation_id}")
        return {"status": "ended", "conversation_id": conversation_id}

    async def get_conversation(self, conversation_id: str) -> dict:
        return await self._request("GET", f"/v2/conversations/{conversation_id}")

    async def list_replicas(self, page: int = 1, limit: int = 50) -> dict:
        return await self._request(
            "GET", "/v2/replicas", params={"page": page, "limit": limit}
        )

    async def get_replica(self, replica_id: str) -> dict:
        return await self._request("GET", f"/v2/replicas/{replica_id}")

    async def list_personas(self, page: int = 1, limit: int = 50) -> dict:
        return await self._request(
            "GET", "/v2/personas", params={"page": page, "limit": limit}
        )

    async def get_persona(self, persona_id: str) -> dict:
        return await self._request("GET", f"/v2/personas/{persona_id}")


async def create_conversation(
    replica_id: str,
    persona_id: str,
    conversation_name: str = "Avatour Sales Call",
    custom_greeting: str = "",
    conversational_context: str = "",
    properties: dict | None = None,
) -> dict:
    return await TavusClient().create_conversation(
        replica_id=replica_id,
        persona_id=persona_id,
        conversation_name=conversation_name,
        custom_greeting=custom_greeting,
        conversational_context=conversational_context,
        properties=properties,
    )


async def end_conversation(conversation_id: str) -> dict:
    return await TavusClient().end_conversation(conversation_id)


async def get_conversation(conversation_id: str) -> dict:
    return await TavusClient().get_conversation(conversation_id)
