"""Admin proxy to the Tavus API for replicas and personas."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_admin
from app.models import User
from app.services.tavus import TavusClient, TavusError

router = APIRouter(prefix="/admin/tavus", tags=["admin:tavus"])


def _client() -> TavusClient:
    return TavusClient()


async def _guard(coro):
    try:
        return await coro
    except TavusError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/replicas")
async def list_replicas(
    page: int = 1,
    limit: int = 50,
    _: User = Depends(get_current_admin),
):
    return await _guard(_client().list_replicas(page, limit))


@router.get("/replicas/{replica_id}")
async def get_replica(replica_id: str, _: User = Depends(get_current_admin)):
    return await _guard(_client().get_replica(replica_id))


@router.get("/personas")
async def list_personas(
    page: int = 1,
    limit: int = 50,
    _: User = Depends(get_current_admin),
):
    return await _guard(_client().list_personas(page, limit))


@router.get("/personas/{persona_id}")
async def get_persona(persona_id: str, _: User = Depends(get_current_admin)):
    return await _guard(_client().get_persona(persona_id))
