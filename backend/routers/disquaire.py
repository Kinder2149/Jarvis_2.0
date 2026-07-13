"""
disquaire.py — Routes de l'agent DISQUAIRE (Mission 2, rangement Genre par lots).

  GET  /disquaire/status  → pile trouvée ? nb de genres ? prêt ?
  POST /disquaire/learn   → (re)apprend les genres depuis les playlists G.
  GET  /disquaire/batch   → propose un genre pour un lot de titres de la pile
  POST /disquaire/apply   → range le lot validé (ajoute dans les G., retire de la pile)
"""
import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import disquaire_service, spotify_service

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/disquaire", tags=["disquaire"])


@router.get("/status")
async def status():
    if not spotify_service.is_connected():
        return {"connected": False, "ready": False}
    try:
        s = await disquaire_service.get_status()
        s["connected"] = True
        return s
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur Spotify : {e}")


@router.post("/learn")
async def learn():
    if not spotify_service.is_connected():
        raise HTTPException(status_code=400, detail="Non connecté à Spotify.")
    try:
        sig = await disquaire_service.build_signatures(force=True)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {
        "genres": [
            {"label": l, "artists": sig["examples"].get(l, [])[:10]}
            for l in sig["labels"]
        ]
    }


@router.get("/batch")
async def batch(size: int = 25):
    if not spotify_service.is_connected():
        raise HTTPException(status_code=400, detail="Non connecté à Spotify.")
    try:
        return await disquaire_service.get_batch(size=size)
    except Exception as e:
        logger.error(f"[DISQUAIRE] batch: {e}")
        raise HTTPException(status_code=502, detail=str(e))


class ApplyItem(BaseModel):
    uri: str
    add: list[str] = []
    remove: list[str] = []
    existing: list[str] = []


class ApplyBody(BaseModel):
    pile_id: str
    assignments: list[ApplyItem]


@router.post("/recenser")
async def recenser():
    if not spotify_service.is_connected():
        raise HTTPException(status_code=400, detail="Non connecté à Spotify.")
    if disquaire_service.get_recenser_state()["running"]:
        return {"already_running": True}
    asyncio.create_task(disquaire_service.run_recenser())
    return {"started": True}


@router.get("/recenser/status")
def recenser_status():
    return disquaire_service.get_recenser_state()


@router.get("/local-stats")
def local_stats():
    return disquaire_service.get_local_stats()


@router.get("/etat")
def etat():
    return disquaire_service.get_etat()


@router.post("/apply")
async def apply(body: ApplyBody):
    if not spotify_service.is_connected():
        raise HTTPException(status_code=400, detail="Non connecté à Spotify.")
    if disquaire_service.get_recenser_state()["running"]:
        raise HTTPException(status_code=409, detail="Recensement en cours — attends qu'il se termine.")
    try:
        return await disquaire_service.apply(
            [a.model_dump() for a in body.assignments], body.pile_id
        )
    except Exception as e:
        logger.error(f"[DISQUAIRE] apply: {e}")
        raise HTTPException(status_code=502, detail=f"Erreur lors du rangement : {e}")
