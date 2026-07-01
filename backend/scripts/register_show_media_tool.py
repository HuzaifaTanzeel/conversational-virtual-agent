"""Register show_media tool on the Tavus persona (required for images + silent tool calls)."""

import asyncio
import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings  # noqa: E402

TAVUS_BASE = "https://tavusapi.com"

SHOW_MEDIA_TOOL = {
    "type": "function",
    "function": {
        "name": "show_media",
        "description": (
            "Display a photo, video, or 360 tour on the guest's screen. "
            "Call this when the guest asks to SEE a villa, restaurant, spa, activity, or resort area. "
            "Do not describe the tool or function name — only provide natural speech in the speech parameter."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_type": {
                    "type": "string",
                    "enum": ["photo", "video", "tour_360", "floor_plan", "matterport"],
                    "description": "Type of media to display",
                },
                "room_name": {
                    "type": "string",
                    "enum": [
                        "overwater_pool_villa",
                        "sunset_overwater_pool_villa",
                        "one_bedroom_lagoon_pool_villa",
                        "one_bedroom_sunset_lagoon_pool_villa",
                        "one_bedroom_sunset_beach_pool_villa",
                        "beach_pool_villa",
                        "family_beach_pool_villa",
                        "two_bedroom_family_lagoon_pool_villa",
                        "two_bedroom_family_beach_pool_villa",
                        "two_bedroom_overwater_pool_residence",
                        "two_bedroom_beachfront_pool_residence",
                        "three_bedroom_overwater_pool_residence",
                        "three_bedroom_lagoon_pool_residence",
                        "three_bedroom_royal_beachfront_pool_residence",
                        "the_lighthouse",
                        "fish_market",
                        "cafe_umi",
                        "the_collective",
                        "the_retreat",
                        "pool_bar",
                        "sunset_bar",
                        "wine_cellar",
                        "avi_spa",
                        "fitness_centre",
                        "water_sports",
                        "planet_trekkers",
                        "teen_escapades",
                        "resort_aerial",
                        "resort_overview",
                    ],
                    "description": "Canonical area identifier for the media asset",
                },
                "speech": {
                    "type": "string",
                    "description": (
                        "Natural conversational sentence for the guest while the image appears. "
                        "Never mention tools, functions, or underscores."
                    ),
                },
            },
            "required": ["asset_type", "room_name", "speech"],
        },
    },
}


async def main() -> None:
    settings = get_settings()
    if not settings.tavus_api_key:
        print("TAVUS_API_KEY not set in .env")
        sys.exit(1)
    persona_id = settings.tavus_persona_id
    if not persona_id:
        print("TAVUS_PERSONA_ID not set in .env")
        sys.exit(1)

    headers = {"x-api-key": settings.tavus_api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        get_resp = await client.get(
            f"{TAVUS_BASE}/v2/personas/{persona_id}", headers=headers
        )
        get_resp.raise_for_status()
        persona = get_resp.json()
        existing = persona.get("layers", {}).get("llm", {}).get("tools") or []
        print(f"Persona: {persona.get('persona_name', persona_id)}")
        print(f"Existing tools: {[t.get('function', {}).get('name') for t in existing]}")

        patch_resp = await client.patch(
            f"{TAVUS_BASE}/v2/personas/{persona_id}",
            headers=headers,
            json=[
                {
                    "op": "replace",
                    "path": "/layers/llm/tools",
                    "value": [SHOW_MEDIA_TOOL],
                }
            ],
        )
        if patch_resp.status_code == 304:
            print(f"show_media already registered on persona {persona_id}")
        else:
            patch_resp.raise_for_status()
            print(f"Registered show_media on persona {persona_id}")
        print(json.dumps([SHOW_MEDIA_TOOL], indent=2)[:500] + "...")


if __name__ == "__main__":
    asyncio.run(main())
