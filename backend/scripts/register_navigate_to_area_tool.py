"""Register all tools on the Tavus persona: navigate_* + show_brochure (inline)
and send_details_email (API delivery via /v2/tools registry)."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
FRONTEND_ROOT = REPO_ROOT / "frontend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings  # noqa: E402

TAVUS_BASE = "https://tavusapi.com"


def _ok_response(resp: httpx.Response) -> None:
    """Accept 2xx and 304 (Tavus may return NOT MODIFIED when unchanged)."""
    if resp.status_code == 304 or resp.is_success:
        return
    resp.raise_for_status()

SHOW_BROCHURE_TOOL = {
    "type": "function",
    "function": {
        "name": "show_brochure",
        "description": (
            "Show the Planet Trekkers kids club brochure on the guest's screen in full detail. "
            "Use when the guest specifically asks to SEE the Planet Trekkers details, schedule, "
            "or brochure in full. "
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "brochure_id": {
                    "type": "string",
                    "enum": ["planet_trekkers"],
                    "description": "Which brochure to display",
                },
                "speech": {
                    "type": "string",
                    "description": (
                        "What to say to the guest while showing the brochure. "
                        "Two to three short sentences: tell them what they are seeing, "
                        "invite them to scroll through, and offer to answer questions or "
                        "navigate back to the tour when ready."
                    ),
                },
            },
            "required": ["brochure_id", "speech"],
        },
    },
}

SEND_EMAIL_TOOL_DEF = {
    "name": "send_details_email",
    "description": (
        "Send resort details (e.g. the Planet Trekkers kids club brochure) "
        "to the guest's email address. Use when the guest asks to receive "
        "information or details by email. The guest's email is already known "
        "from their booking — do not ask for it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "detail_type": {
                "type": "string",
                "enum": ["planet_trekkers"],
                "description": "Which details to send",
            },
        },
        "required": ["detail_type"],
    },
    "origin": "llm",
    "delivery": {
        "app_message": False,
        "api": {
            "url": "",  # filled at runtime from BACKEND_PUBLIC_URL
            "method": "POST",
            "timeout": 30,
            "auth": {"type": "bearer", "token": ""},  # filled from TAVUS_TOOL_SECRET
        },
    },
    "on_call": "generate_filler",
    "on_resolve": "generate_response",
}


def load_tool_definitions() -> list[dict]:
    """
    Call buildToolDefinitions() in sceneRegistry.js via Node and return the
    full array of OpenAI-format tool objects (10 navigate_* tools).
    """
    cmd = [
        "node",
        "--input-type=module",
        "-e",
        "import { buildToolDefinitions } from './src/lib/sceneRegistry.js'; "
        "console.log(JSON.stringify(buildToolDefinitions()));",
    ]
    result = subprocess.run(
        cmd,
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout.strip())


async def _register_inline_tools(
    client: httpx.AsyncClient, headers: dict, persona_id: str, tools: list[dict]
) -> None:
    """Patch inline tools (navigate_* + show_brochure) on the persona."""
    patch_resp = await client.patch(
        f"{TAVUS_BASE}/v2/personas/{persona_id}",
        headers=headers,
        json=[
            {
                "op": "replace",
                "path": "/layers/llm/tools",
                "value": tools,
            }
        ],
    )
    _ok_response(patch_resp)
    tool_names = [t["function"]["name"] for t in tools]
    if patch_resp.status_code == 304:
        print(f"  Inline tools unchanged (304) — already registered ({len(tools)}): {tool_names}")
    else:
        print(f"  Inline tools registered ({len(tools)}): {tool_names}")


async def _register_api_tool(
    client: httpx.AsyncClient, headers: dict, persona_id: str, settings
) -> None:
    """Register send_details_email via /v2/tools registry + attach to persona."""
    backend_url = settings.backend_public_url.rstrip("/")
    tool_def = {**SEND_EMAIL_TOOL_DEF}
    tool_def["delivery"] = {
        "app_message": False,
        "api": {
            "url": f"{backend_url}/tools/send-email",
            "method": "POST",
            "timeout": 30,
            "auth": {
                "type": "bearer",
                "token": settings.tavus_tool_secret,
            },
        },
    }

    # Check if tool already exists
    list_resp = await client.get(
        f"{TAVUS_BASE}/v2/tools", headers=headers, params={"limit": 100}
    )
    list_resp.raise_for_status()
    existing_tools = list_resp.json().get("data", [])
    existing = next(
        (t for t in existing_tools if t.get("name") == "send_details_email"), None
    )

    if existing:
        tool_id = existing["tool_id"]
        # Update it
        update_resp = await client.patch(
            f"{TAVUS_BASE}/v2/tools/{tool_id}",
            headers=headers,
            json=tool_def,
        )
        _ok_response(update_resp)
        print(f"  Updated existing send_details_email tool (id={tool_id})")
    else:
        # Create it
        create_resp = await client.post(
            f"{TAVUS_BASE}/v2/tools", headers=headers, json=tool_def
        )
        _ok_response(create_resp)
        tool_id = create_resp.json().get("tool_id")
        print(f"  Created send_details_email tool (id={tool_id})")

    # Attach to persona/PAL
    attach_resp = await client.post(
        f"{TAVUS_BASE}/v2/pals/{persona_id}/tools",
        headers=headers,
        json={"tool_ids": [tool_id]},
    )
    if attach_resp.status_code < 400:
        print(f"  Attached send_details_email to persona {persona_id}")
    else:
        print(
            f"  Warning: attach returned {attach_resp.status_code}: {attach_resp.text}"
        )


async def main() -> None:
    settings = get_settings()
    if not settings.tavus_api_key:
        print("TAVUS_API_KEY not set in .env")
        sys.exit(1)
    persona_id = settings.tavus_persona_id
    if not persona_id:
        print("TAVUS_PERSONA_ID not set in .env")
        sys.exit(1)

    # Load navigate tools from frontend scene registry
    nav_tools = load_tool_definitions()
    # Add show_brochure as inline tool alongside navigate tools
    inline_tools = nav_tools + [SHOW_BROCHURE_TOOL]

    nav_tool_names = [t["function"]["name"] for t in nav_tools]
    total_enums = sum(
        len(t["function"]["parameters"]["properties"]["area"]["enum"])
        for t in nav_tools
    )

    headers = {"x-api-key": settings.tavus_api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        get_resp = await client.get(
            f"{TAVUS_BASE}/v2/personas/{persona_id}", headers=headers
        )
        get_resp.raise_for_status()
        persona = get_resp.json()
        existing = persona.get("layers", {}).get("llm", {}).get("tools") or []
        print(f"Persona: {persona.get('persona_name', persona_id)}")
        print(f"Existing inline tools: {[t.get('function', {}).get('name') for t in existing]}")
        print(f"\nRegistering {len(nav_tools)} navigate tools ({total_enums} enum values) + show_brochure")
        for name in nav_tool_names:
            print(f"  - {name}")
        print(f"  - show_brochure")

        # 1. Register inline tools (navigate + show_brochure)
        await _register_inline_tools(client, headers, persona_id, inline_tools)

        # 2. Register send_details_email via API tool registry
        if settings.tavus_tool_secret:
            print(f"\nRegistering send_details_email (API delivery -> {settings.backend_public_url}/tools/send-email)")
            await _register_api_tool(client, headers, persona_id, settings)
        else:
            print(
                "\nSkipping send_details_email: TAVUS_TOOL_SECRET not set in .env. "
                "Set it and re-run to enable the email tool."
            )

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
