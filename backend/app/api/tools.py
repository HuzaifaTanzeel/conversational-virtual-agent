"""
Tavus API-delivery tool endpoints
==================================
These endpoints are called directly by Tavus when an API-delivery tool fires.
They are NOT called by the frontend. Authentication uses a shared secret
(TAVUS_TOOL_SECRET env var) passed as a Bearer token by Tavus.
"""

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import AsyncSessionLocal
from app.models import CallSession, MeetingInvite
from app.services.email import send_details_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])

_BROCHURE_URLS = {
    "planet_trekkers": "https://issuu.com/icmmg/docs/icm_planet-trekkers-brochure_final?fr=sN2ZlMjUzNDY5NDg",
}


def _verify_tool_secret(request: Request) -> None:
    """Verify the bearer token matches our internal tool secret."""
    settings = get_settings()
    expected = settings.tavus_tool_secret
    if not expected:
        raise HTTPException(status_code=503, detail="Tool secret not configured")
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != expected:
        raise HTTPException(status_code=401, detail="Invalid tool authorization")


async def _lookup_guest_email(conversation_id: str) -> tuple[str, str]:
    """Resolve conversation_id -> (prospect_email, prospect_name)."""
    async with AsyncSessionLocal() as db:
        session = await db.scalar(
            select(CallSession).where(
                CallSession.tavus_conversation_id == conversation_id
            )
        )
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        invite = await db.scalar(
            select(MeetingInvite).where(
                MeetingInvite.demo_user_id == session.demo_user_id,
                MeetingInvite.call_session_id == session.id,
            )
        )
        if invite and invite.prospect_email:
            return invite.prospect_email, invite.prospect_name

        invite_fallback = await db.scalar(
            select(MeetingInvite).where(
                MeetingInvite.demo_user_id == session.demo_user_id,
            ).order_by(MeetingInvite.created_at.desc())
        )
        if invite_fallback and invite_fallback.prospect_email:
            return invite_fallback.prospect_email, invite_fallback.prospect_name

        raise HTTPException(
            status_code=404, detail="Guest email not found for this session"
        )


@router.post("/send-email")
async def handle_send_email(request: Request):
    """Tavus API-delivery endpoint for the send_details_email tool.

    Tavus POSTs here directly with tool call parameters.
    Returns a result that Tavus uses to generate a spoken response.
    """
    _verify_tool_secret(request)

    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    conversation_id = body.get("conversation_id", "")
    parameters = body.get("parameters") or body.get("properties", {})
    if isinstance(parameters, str):
        parameters = json.loads(parameters)

    detail_type = parameters.get("detail_type", "planet_trekkers")
    logger.info(
        "send_details_email tool called: conversation=%s detail_type=%s",
        conversation_id,
        detail_type,
    )

    try:
        email, name = await _lookup_guest_email(conversation_id)
    except HTTPException:
        return {
            "output": "I'm sorry, I wasn't able to find an email address for this session. Could you provide your email?",
            "status": "error",
        }

    brochure_url = _BROCHURE_URLS.get(detail_type, _BROCHURE_URLS["planet_trekkers"])

    try:
        await send_details_email(
            to_email=email,
            prospect_name=name,
            detail_type=detail_type,
            brochure_url=brochure_url,
        )
    except Exception as exc:
        logger.exception("Failed to send details email to %s", email)
        return {
            "output": f"I'm sorry, there was a problem sending the email. Please try again later.",
            "status": "error",
        }

    return {
        "output": f"Email with {detail_type.replace('_', ' ').title()} details sent successfully to {name}.",
        "status": "success",
    }
