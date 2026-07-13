"""
disquaire_service.py — Le cerveau de l'agent DISQUAIRE (Mission 2, Genre).

Rôle :
  1. Apprend les genres de Kinder en lisant ses playlists préfixées « G. » (signatures).
  2. Classe un lot de titres de la pile « On est parti pour trier » via l'IA.
  3. Applique le rangement validé : ajoute dans les playlists G. (anti-doublon)
     et retire de la pile les titres effectivement rangés.

Voir docs/CADRAGE_DISQUAIRE.md (§ Cadre Mission 2).
megacompil n'est JAMAIS touchée — la pile est une copie de travail.
"""
import json
import logging
import re

from backend.database import load_config
from backend.services import spotify_service, model_router

logger = logging.getLogger("uvicorn")

PILE_NAME = "On est parti pour trier"
_GENRE_RE = re.compile(r"^g\.\s*", re.IGNORECASE)

# Cache mémoire des signatures de genre (utilisateur unique).
_signatures: dict | None = None


def _is_genre(name: str) -> bool:
    return bool(name and _GENRE_RE.match(name))


def _genre_label(name: str) -> str:
    return _GENRE_RE.sub("", name or "").strip()


async def _find_pile_and_genres() -> tuple[dict | None, list[dict]]:
    playlists = await spotify_service.get_all_playlists()
    pile = None
    genres = []
    for p in playlists:
        name = (p.get("name") or "").strip()
        if name.lower() == PILE_NAME.lower():
            pile = p
        elif _is_genre(name):
            genres.append(p)
    return pile, genres


async def build_signatures(force: bool = False) -> dict:
    """Construit (et met en cache) une signature par genre : label → playlist_id + artistes types."""
    global _signatures
    if _signatures is not None and not force:
        return _signatures
    _, genres = await _find_pile_and_genres()
    labels: dict[str, str] = {}
    examples: dict[str, list[str]] = {}
    for g in genres:
        label = _genre_label(g.get("name") or "")
        if not label:
            continue
        labels[label] = g.get("id")
        tracks = await spotify_service.get_playlist_tracks(g["id"], max_tracks=60)
        seen: list[str] = []
        for t in tracks:
            for a in t["artists"]:
                if a and a not in seen:
                    seen.append(a)
            if len(seen) >= 25:
                break
        examples[label] = seen[:25]
    _signatures = {"labels": labels, "examples": examples}
    logger.info(f"[DISQUAIRE] Signatures construites : {len(labels)} genres.")
    return _signatures


async def get_status() -> dict:
    pile, genres = await _find_pile_and_genres()
    return {
        "pile_found": pile is not None,
        "pile_name": PILE_NAME,
        "pile_total": (pile.get("tracks") or {}).get("total", 0) if pile else 0,
        "genre_count": len(genres),
        "ready": pile is not None and len(genres) > 0,
    }


def _build_prompt(signatures: dict, tracks: list[dict]) -> str:
    lines = ["Voici les GENRES de l'utilisateur (chacun est une playlist), avec des artistes représentatifs :"]
    for label, arts in signatures["examples"].items():
        sample = ", ".join(arts[:15]) if arts else "(playlist vide)"
        lines.append(f"- {label} : {sample}")
    lines += [
        "",
        "Pour CHAQUE titre ci-dessous, indique dans quel(s) genre(s) de la liste ci-dessus il doit être rangé.",
        "Règles : utilise UNIQUEMENT des genres de la liste (mot exact). Un titre peut aller dans plusieurs genres. Si vraiment aucun ne convient, mets une liste vide.",
        "",
        "Titres :",
    ]
    for i, t in enumerate(tracks, start=1):
        artists = ", ".join(t["artists"]) or "artiste inconnu"
        lines.append(f'{i}. "{t["name"]}" — {artists}')
    lines += [
        "",
        'Réponds UNIQUEMENT en JSON, sans aucun texte autour, au format :',
        '[{"i": 1, "genres": ["Rock"], "reason": "courte raison"}, ...]',
    ]
    return "\n".join(lines)


def _parse_proposals(raw: str, n: int) -> dict:
    try:
        start, end = raw.find("["), raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        data = json.loads(raw)
        out = {}
        for item in data:
            i = item.get("i")
            if isinstance(i, int):
                out[i] = {
                    "genres": item.get("genres") or [],
                    "reason": item.get("reason") or "",
                }
        return out
    except Exception as e:
        logger.error(f"[DISQUAIRE] Échec parsing propositions : {e} / brut : {raw[:200]}")
        return {}


async def get_batch(size: int = 25) -> dict:
    size = max(1, min(size, 50))
    config = load_config()
    signatures = await build_signatures()
    pile, _ = await _find_pile_and_genres()
    if pile is None:
        raise RuntimeError(f'Playlist « {PILE_NAME} » introuvable dans ton compte.')
    if not signatures["labels"]:
        raise RuntimeError("Aucune playlist de genre trouvée (préfixe « G. »).")

    pile_tracks = await spotify_service.get_playlist_tracks(pile["id"], max_tracks=size)
    if not pile_tracks:
        return {"pile_id": pile["id"], "genres": list(signatures["labels"].keys()), "tracks": []}

    model_id = config.get("model_preferences", {}).get("analysis") or "anthropic/claude-sonnet-4.5"
    raw = await model_router.call_model(
        model_id=model_id,
        messages=[{"role": "user", "content": _build_prompt(signatures, pile_tracks)}],
        api_keys=config.get("api_keys", {}),
        session_id=0,
        step_name="disquaire_classify",
        model_type="analysis",
        db_conn=None,
        module_name="disquaire",
    )
    proposals = _parse_proposals(raw, len(pile_tracks))
    label_by_lower = {l.lower(): l for l in signatures["labels"]}

    result = []
    for idx, t in enumerate(pile_tracks):
        prop = proposals.get(idx + 1, {"genres": [], "reason": ""})
        matched = []
        for gname in prop.get("genres", []):
            real = label_by_lower.get(str(gname).strip().lower())
            if real and real not in matched:
                matched.append(real)
        result.append({
            "uri": t["uri"],
            "name": t["name"],
            "artists": t["artists"],
            "proposed": matched,
            "reason": prop.get("reason", ""),
        })
    return {
        "pile_id": pile["id"],
        "genres": list(signatures["labels"].keys()),
        "tracks": result,
    }


async def apply(assignments: list[dict], pile_id: str) -> dict:
    """
    assignments : [{"uri": ..., "genre_labels": [...]}]
    Ajoute chaque titre dans les playlists G. correspondantes (anti-doublon),
    puis retire de la pile les titres rangés dans >= 1 genre.
    """
    signatures = await build_signatures()
    labels = signatures["labels"]  # label -> playlist_id

    target_labels = {l for a in assignments for l in a.get("genre_labels", []) if l in labels}

    # Anti-doublon : uris déjà présentes dans chaque playlist cible.
    existing: dict[str, set] = {}
    for l in target_labels:
        tracks = await spotify_service.get_playlist_tracks(labels[l])
        existing[l] = {t["uri"] for t in tracks}

    to_add: dict[str, list[str]] = {l: [] for l in target_labels}
    filed_uris: list[str] = []
    for a in assignments:
        uri = a.get("uri")
        glabels = [l for l in a.get("genre_labels", []) if l in labels]
        if not uri or not glabels:
            continue
        filed = False
        for l in glabels:
            if uri in existing[l]:
                filed = True  # déjà rangé
            elif uri not in to_add[l]:
                to_add[l].append(uri)
                filed = True
        if filed:
            filed_uris.append(uri)

    added = 0
    for l, uris in to_add.items():
        if uris:
            await spotify_service.add_items(labels[l], uris)
            added += len(uris)

    removed = 0
    if filed_uris:
        await spotify_service.remove_items(pile_id, filed_uris)
        removed = len(filed_uris)

    logger.info(f"[DISQUAIRE] Rangement : {added} ajouts, {removed} retirés de la pile.")
    return {"added": added, "filed": len(filed_uris), "removed_from_pile": removed}
