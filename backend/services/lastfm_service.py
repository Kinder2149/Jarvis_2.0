"""
lastfm_service.py — Connecteur Last.fm minimal (mode Mood assisté, cadrage §14).

Fournit les tags communautaires d'un TITRE (track.getTopTags). Couverture réelle
mesurée le 2026-07-15 : ~8 % de la bibliothèque (surtout les hits anglo-saxons ;
aveugle sur le francophone). C'est donc un INDICE bonus pour le tri des moods,
jamais une source décisive — et une absence de tags est le cas normal.

Règles :
  - Jamais bloquant : toute erreur → liste vide, on continue.
  - Cache mémoire (durée de vie du process) : un titre n'est interrogé qu'une fois.
  - Limite de débit respectée (~4 req/s) uniquement sur les vrais appels réseau.
"""
import asyncio
import logging

import httpx

logger = logging.getLogger("uvicorn")

API_URL = "http://ws.audioscrobbler.com/2.0/"
_POIDS_MINIMUM = 10   # en dessous, le tag est anecdotique (le poids max renvoyé est 100)
_MAX_TAGS = 8

# Cache mémoire : (artiste, titre) normalisés -> [tags]
_cache: dict[tuple[str, str], list[str]] = {}


async def get_track_tags(api_key: str, artist: str, track: str) -> list[str]:
    """Tags Last.fm du titre (max 8, poids >= 10). Liste vide si inconnu ou erreur."""
    if not api_key or not artist or not track:
        return []
    cle = (artist.lower().strip(), track.lower().strip())
    if cle in _cache:
        return _cache[cle]

    tags: list[str] = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(API_URL, params={
                "method": "track.gettoptags",
                "artist": artist, "track": track,
                "api_key": api_key, "format": "json", "autocorrect": 1,
            }, timeout=15.0)
        if resp.status_code == 200:
            brut = (resp.json().get("toptags") or {}).get("tag") or []
            if isinstance(brut, dict):
                brut = [brut]
            tags = [t["name"] for t in brut
                    if int(t.get("count") or 0) >= _POIDS_MINIMUM][:_MAX_TAGS]
    except Exception as e:
        logger.debug(f"[LASTFM] {artist} — {track} : {e}")
    _cache[cle] = tags
    await asyncio.sleep(0.25)  # limite de débit, seulement après un vrai appel réseau
    return tags


async def get_tags_for_tracks(api_key: str, tracks: list[dict]) -> dict[str, list[str]]:
    """{uri: [tags]} pour une liste de titres {uri, name, artists}.

    Ne renvoie que les titres qui ONT des tags (l'absence est le cas normal).
    """
    if not api_key:
        return {}
    out: dict[str, list[str]] = {}
    for t in tracks:
        artiste = (t.get("artists") or [""])[0]
        tags = await get_track_tags(api_key, artiste, t.get("name") or "")
        if tags:
            out[t["uri"]] = tags
    return out
