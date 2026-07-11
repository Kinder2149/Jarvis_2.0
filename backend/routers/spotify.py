"""
spotify.py — Routes de la connexion Spotify (agent DISQUAIRE, Mission 1).

Flux :
  1. POST /spotify/credentials  → Kinder enregistre Client ID + Client Secret
  2. GET  /spotify/login        → redirige vers l'écran d'autorisation Spotify
  3. GET  /spotify/callback     → Spotify renvoie ici, on stocke le jeton
  4. GET  /spotify/status       → état de la connexion
  5. GET  /spotify/playlists    → liste des playlists du compte
  6. POST /spotify/disconnect   → oublie le jeton
"""
import logging
import secrets

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.services import spotify_service

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/spotify", tags=["spotify"])


class CredentialsBody(BaseModel):
    client_id: str
    client_secret: str


@router.post("/credentials")
def save_credentials(body: CredentialsBody):
    if not body.client_id.strip() or not body.client_secret.strip():
        raise HTTPException(status_code=400, detail="Client ID et Client Secret requis.")
    spotify_service.save_credentials(body.client_id, body.client_secret)
    return {"ok": True}


@router.get("/status")
async def status():
    if not spotify_service.is_configured():
        return {"configured": False, "connected": False}
    if not spotify_service.is_connected():
        return {"configured": True, "connected": False}
    try:
        me = await spotify_service.get_me()
        return {
            "configured": True,
            "connected": True,
            "display_name": me.get("display_name") or me.get("id"),
            "product": me.get("product"),
        }
    except Exception as e:
        logger.warning(f"[SPOTIFY] status: jeton présent mais /me a échoué: {e}")
        return {"configured": True, "connected": True, "display_name": None}


@router.get("/login")
def login():
    if not spotify_service.is_configured():
        raise HTTPException(status_code=400, detail="Identifiants Spotify non enregistrés.")
    state = secrets.token_urlsafe(16)
    return RedirectResponse(spotify_service.build_authorize_url(state))


@router.get("/callback")
async def callback(code: str = "", error: str = "", state: str = ""):
    if error:
        return RedirectResponse(f"/app/spotify.html?error={error}")
    if not code:
        return RedirectResponse("/app/spotify.html?error=code_manquant")
    try:
        await spotify_service.exchange_code(code)
    except Exception as e:
        logger.error(f"[SPOTIFY] callback: {e}")
        return RedirectResponse("/app/spotify.html?error=echange")
    return RedirectResponse("/app/spotify.html?connected=1")


@router.get("/playlists")
async def playlists():
    if not spotify_service.is_connected():
        raise HTTPException(status_code=400, detail="Non connecté à Spotify.")
    try:
        raw = await spotify_service.get_all_playlists()
    except Exception as e:
        logger.error(f"[SPOTIFY] playlists: {e}")
        raise HTTPException(status_code=502, detail=f"Erreur Spotify : {e}")
    playlists = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "tracks_total": (p.get("tracks") or {}).get("total", 0),
            "owner": (p.get("owner") or {}).get("display_name"),
            "public": p.get("public"),
        }
        for p in raw
    ]
    return {"count": len(playlists), "playlists": playlists}


@router.post("/disconnect")
def disconnect():
    spotify_service.disconnect()
    return {"ok": True}
