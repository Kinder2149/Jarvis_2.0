"""
spotify_service.py — Connecteur Spotify pour l'agent DISQUAIRE (Mission 1).

Gère l'autorisation OAuth (Authorization Code) sur le compte personnel de Kinder,
le stockage du jeton renouvelable dans app_config, et la lecture des playlists.

Identifiants et jeton stockés dans la table app_config (catégorie 'spotify') :
  - spotify_client_id       : identifiant public de la fiche app Spotify
  - spotify_client_secret   : secret de la fiche app (ne quitte jamais le backend)
  - spotify_refresh_token   : jeton renouvelable obtenu après autorisation

Contraintes figées (voir docs/CADRAGE_DISQUAIRE.md) :
  - Redirect URI = http://127.0.0.1:8000/api/spotify/callback (identique côté fiche Spotify)
  - Loopback 127.0.0.1 obligatoire (Spotify refuse « localhost »)
"""
import base64
import logging
import urllib.parse

import httpx

from backend.database import get_connection

logger = logging.getLogger("uvicorn")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

REDIRECT_URI = "http://127.0.0.1:8000/api/spotify/callback"

# Droits demandés : lire les playlists + ranger des titres dans les playlists du compte.
SCOPES = (
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-private "
    "playlist-modify-public "
    "user-read-private"
)


# --- Stockage app_config -----------------------------------------------------

def _get(key: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row and row["value"] else ""


def _set(key: str, value: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO app_config (key, value, category, updated_at)
        VALUES (?, ?, 'spotify', datetime('now'))
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')
        """,
        (key, value),
    )
    conn.commit()
    conn.close()


def get_credentials() -> tuple[str, str]:
    return _get("spotify_client_id"), _get("spotify_client_secret")


def save_credentials(client_id: str, client_secret: str) -> None:
    _set("spotify_client_id", client_id.strip())
    _set("spotify_client_secret", client_secret.strip())


def is_configured() -> bool:
    client_id, client_secret = get_credentials()
    return bool(client_id and client_secret)


def is_connected() -> bool:
    return bool(_get("spotify_refresh_token"))


def disconnect() -> None:
    _set("spotify_refresh_token", "")


# --- OAuth -------------------------------------------------------------------

def build_authorize_url(state: str) -> str:
    client_id, _ = get_credentials()
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "show_dialog": "false",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def _basic_auth_header() -> str:
    client_id, client_secret = get_credentials()
    token = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return f"Basic {token}"


async def exchange_code(code: str) -> None:
    """Échange le code d'autorisation contre un jeton renouvelable et le stocke."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            headers={
                "Authorization": _basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            timeout=30.0,
        )
    if resp.status_code != 200:
        logger.error(f"[SPOTIFY] Échange code échoué {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Échec de l'autorisation Spotify ({resp.status_code})")
    data = resp.json()
    refresh = data.get("refresh_token")
    if not refresh:
        raise RuntimeError("Spotify n'a pas renvoyé de jeton renouvelable.")
    _set("spotify_refresh_token", refresh)
    logger.info("[SPOTIFY] Connexion réussie — jeton renouvelable stocké.")


async def _get_access_token() -> str:
    """Obtient un jeton d'accès frais à partir du jeton renouvelable stocké."""
    refresh = _get("spotify_refresh_token")
    if not refresh:
        raise RuntimeError("Spotify non connecté.")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            headers={
                "Authorization": _basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "refresh_token", "refresh_token": refresh},
            timeout=30.0,
        )
    if resp.status_code != 200:
        logger.error(f"[SPOTIFY] Rafraîchissement jeton échoué {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Session Spotify expirée ({resp.status_code}) — reconnecte-toi.")
    data = resp.json()
    # Spotify peut renvoyer un nouveau refresh_token : le conserver le cas échéant.
    if data.get("refresh_token"):
        _set("spotify_refresh_token", data["refresh_token"])
    return data["access_token"]


# --- Appels API --------------------------------------------------------------

async def _api_get(path: str, params: dict | None = None) -> dict:
    token = await _get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30.0,
        )
    resp.raise_for_status()
    return resp.json()


async def get_me() -> dict:
    return await _api_get("/me")


async def get_all_playlists() -> list[dict]:
    """Récupère toutes les playlists du compte (pagination 50 par 50)."""
    items: list[dict] = []
    while True:
        data = await _api_get("/me/playlists", {"limit": 50, "offset": len(items)})
        batch = data.get("items", [])
        items.extend(batch)
        if not data.get("next") or not batch:
            break
    return items
