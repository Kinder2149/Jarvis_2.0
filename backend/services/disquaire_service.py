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

from backend.database import load_config, get_connection
from backend.services import spotify_service, model_router, lastfm_service

logger = logging.getLogger("uvicorn")

PILE_NAME = "On est parti pour trier"
MEGA_NAME = "megacompil"
_GENRE_RE = re.compile(r"^g\.\s*", re.IGNORECASE)

# Formats : exceptions assumées de Kinder. Ce ne sont pas des styles, et l'IA n'a pas
# l'information pour les juger (un live ou une reprise n'est pas toujours signalé dans le
# titre). On ne les propose donc JAMAIS au classement — Kinder les remplit à la main.
# Ils restent des playlists « G. » normales par ailleurs (rangement manuel, affichage).
FORMATS = {"live", "reprise", "bo film", "disney", "freestyle"}


def _classifiables(labels: dict) -> dict:
    """Genres que l'IA a le droit de proposer (tout sauf les formats)."""
    return {l: pid for l, pid in labels.items() if l.lower() not in FORMATS}

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


async def _find_megacompil() -> dict | None:
    """Retrouve megacompil EN DIRECT dans le compte (jamais depuis la copie locale).

    Sécurité : c'est le coffre-fort. On ne se fie pas à la base locale, qui peut être
    en retard et faire croire à tort qu'un titre n'y est pas (→ doublons en masse).
    """
    for p in await spotify_service.get_all_playlists():
        if (p.get("name") or "").strip().lower() == MEGA_NAME:
            return p
    return None


def _examples_from_local(labels: dict[str, str]) -> dict[str, list[str]]:
    """Artistes représentatifs par genre, lus dans la base locale recensée.

    N'a qu'un rôle d'aide au classement : on ne renvoie QUE des genres présents dans
    `labels` (la liste live des playlists « G. »). Un genre non encore recensé ressort
    avec une liste vide — l'IA se base alors sur le seul nom du genre.
    """
    if not labels:
        return {}
    conn = get_connection()
    cur = conn.cursor()
    examples: dict[str, list[str]] = {}
    for label, pid in labels.items():
        cur.execute(
            """SELECT t.artists FROM disquaire_membership m
               JOIN disquaire_tracks t ON t.uri = m.track_uri
               WHERE m.playlist_id = ?""",
            (pid,),
        )
        seen: list[str] = []
        for r in cur.fetchall():
            for a in (r["artists"] or "").split(", "):
                a = a.strip()
                if a and a not in seen:
                    seen.append(a)
            if len(seen) >= 40:
                break
        examples[label] = seen[:40]
    conn.close()
    return examples


async def build_signatures(force: bool = False) -> dict:
    """Liste des genres AUTORISÉS, lue EN DIRECT depuis les playlists « G. » du compte.

    C'est la seule source de vérité du jeu de genres : jamais figée, jamais mise en
    cache, jamais codée en dur. À chaque tri, on relit les « G. » présentes maintenant
    dans le compte. Les artistes d'exemple (aide au classement) viennent de la base
    locale recensée quand elle est disponible.

    Le paramètre `force` est conservé pour compatibilité d'appel ; la lecture étant
    toujours live, il n'a plus d'effet.
    """
    _, genres = await _find_pile_and_genres()  # lecture live des playlists « G. »
    labels: dict[str, str] = {}
    for g in genres:
        label = _genre_label(g.get("name") or "")
        if label:
            labels[label] = g.get("id")
    examples = _examples_from_local(labels)
    logger.info(f"[DISQUAIRE] Signatures (live « G. ») : {len(labels)} genres.")
    return {"labels": labels, "examples": examples}


async def get_status() -> dict:
    pile, genres = await _find_pile_and_genres()
    return {
        "pile_found": pile is not None,
        "pile_name": PILE_NAME,
        "pile_total": (pile.get("tracks") or {}).get("total", 0) if pile else 0,
        "genre_count": len(genres),
        "ready": pile is not None and len(genres) > 0,
    }


def _build_prompt(signatures: dict, tracks: list[dict], sp_genres: dict | None = None) -> str:
    lines = [
        "Tu es un disquaire expert qui range les titres d'un utilisateur dans SES propres playlists de genre.",
        "",
        "Un GENRE est une IDENTITÉ MUSICALE : un style, une scène, la façon dont la musique",
        "est jouée (ex. rap, house, rock, reggae, jazz…). Ce n'est JAMAIS la langue ou",
        "l'origine (français, anglais, US…), ni l'énergie ou le moment (festif, chill,",
        "soirée, party…), ni l'époque (années 80, vintage…).",
        "",
        "Voici la LISTE EXACTE de ses genres autorisés (chacun est une playlist), avec",
        "des artistes représentatifs quand ils sont connus :",
    ]
    for label, arts in signatures["examples"].items():
        if label.lower() in FORMATS:
            continue  # jamais proposé au classement (voir FORMATS)
        sample = ", ".join(arts[:20]) if arts else "(pas encore d'exemple — fie-toi au nom du genre)"
        lines.append(f"- {label} : {sample}")
    lines += [
        "",
        "TÂCHE : pour CHAQUE titre ci-dessous, liste TOUS les genres de la liste ci-dessus",
        "qui correspondent à son IDENTITÉ MUSICALE.",
        "",
        "RÈGLES IMPÉRATIVES :",
        "- Choisis UNIQUEMENT des genres présents dans la liste ci-dessus, écrits au mot EXACT.",
        "  N'invente AUCUN genre et ne propose JAMAIS un genre absent de la liste.",
        "- Classe seulement sur le STYLE musical. N'utilise JAMAIS la langue/l'origine,",
        "  l'énergie/le moment, ni l'époque pour choisir un genre — même si le titre ou",
        "  l'artiste les évoque. (Un morceau chanté en anglais n'a pas de genre « anglais » ;",
        "  un morceau festif n'a pas de genre « festif ».)",
        "- Un même titre peut appartenir à PLUSIEURS genres de la liste : liste-les tous.",
        "- Appuie-toi sur les artistes d'exemple ET sur le SENS musical du nom du genre.",
        "- Certains titres portent une mention [Spotify classe cet artiste en : …]. C'est une",
        "  donnée factuelle, précieuse quand tu ne connais pas l'artiste : sers-t'en pour situer",
        "  le style plutôt que de renoncer. MAIS elle décrit l'ARTISTE, pas ce morceau précis —",
        "  un artiste étiqueté « pop » peut très bien signer un titre qui sonne tout autrement.",
        "  Fie-toi au morceau quand tu le connais ; l'étiquette Spotify n'est qu'un indice.",
        "- Si AUCUN genre de la liste ne correspond vraiment, OU si tu as un DOUTE sur le",
        "  bon genre, renvoie une liste vide. Mieux vaut laisser le titre à trier que de",
        "  deviner : il sera rangé à la main. Ne force JAMAIS un rangement.",
        "",
        "Titres à classer :",
    ]
    for i, t in enumerate(tracks, start=1):
        artists = ", ".join(t["artists"]) or "artiste inconnu"
        sp = (sp_genres or {}).get(t["uri"])
        indice = f"   [Spotify classe cet artiste en : {', '.join(sp[:5])}]" if sp else ""
        lines.append(f'{i}. "{t["name"]}" — {artists}{indice}')
    lines += [
        "",
        'Réponds UNIQUEMENT en JSON, sans aucun texte autour. Recopie les genres au mot',
        'exact depuis la liste. Format :',
        '[{"i": 1, "genres": ["<un genre EXACT de la liste>", "..."], "reason": "courte raison"},',
        ' {"i": 2, "genres": [], "reason": "aucun genre de la liste ne correspond"}]',
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


async def _call_model_logged(config, model_id, prompt, step_name):
    """Appelle le modèle en enregistrant la consommation (tokens) dans le journal.

    La connexion est ouverte juste pour cet appel puis refermée : elle reste inactive
    pendant l'appel réseau, donc elle ne verrouille pas la base (le verrou n'est pris
    qu'à l'écriture, immédiatement suivie d'un commit).
    """
    conn = get_connection()
    try:
        return await model_router.call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config.get("api_keys", {}),
            session_id=0,
            step_name=step_name,
            model_type="analysis",
            db_conn=conn,
            module_name="disquaire",
        )
    finally:
        conn.close()


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
    sp_genres = await spotify_service.get_artist_genres([t["uri"] for t in pile_tracks])
    raw = await _call_model_logged(
        config, model_id, _build_prompt(signatures, pile_tracks, sp_genres), "disquaire_classify"
    )
    proposals = _parse_proposals(raw, len(pile_tracks))
    label_by_lower = {l.lower(): l for l in _classifiables(signatures["labels"])}
    detailed = get_memberships_detailed([t["uri"] for t in pile_tracks])

    result = []
    for idx, t in enumerate(pile_tracks):
        prop = proposals.get(idx + 1, {"genres": [], "reason": ""})
        d = detailed.get(t["uri"], {"genres": [], "moods": []})
        existing_g = d["genres"]
        matched = []
        for gname in prop.get("genres", []):
            real = label_by_lower.get(str(gname).strip().lower())
            if real and real not in matched and real not in existing_g:
                matched.append(real)  # suggestion NOUVELLE (pas déjà en place)
        result.append({
            "uri": t["uri"],
            "name": t["name"],
            "artists": t["artists"],
            "proposed": matched,             # 🟢 vert : à ajouter
            "existing_genres": existing_g,   # 🔵 bleu : déjà là (retirable)
            "existing_moods": d["moods"],    # 🟣 info : moods déjà là
            "reason": prop.get("reason", ""),
        })
    return {
        "pile_id": pile["id"],
        "genres": list(signatures["labels"].keys()),
        "tracks": result,
    }


def _sync_local_after_apply(labels, add_by_pl, remove_by_pl, filed_uris, to_mega, mega_id, pile_id):
    """Met à jour la base locale pour rester cohérente après un rangement (sans re-recenser)."""
    conn = get_connection()
    cur = conn.cursor()
    for l, uris in add_by_pl.items():
        for u in uris:
            cur.execute("INSERT OR IGNORE INTO disquaire_membership (track_uri, playlist_id) VALUES (?, ?)", (u, labels[l]))
    for l, uris in remove_by_pl.items():
        for u in uris:
            cur.execute("DELETE FROM disquaire_membership WHERE track_uri = ? AND playlist_id = ?", (u, labels[l]))
    if mega_id:
        for u in to_mega:
            cur.execute("INSERT OR IGNORE INTO disquaire_membership (track_uri, playlist_id) VALUES (?, ?)", (u, mega_id))
    for u in filed_uris:
        cur.execute("DELETE FROM disquaire_membership WHERE track_uri = ? AND playlist_id = ?", (u, pile_id))
    conn.commit()
    conn.close()


async def apply(assignments: list[dict], pile_id: str, mode: str = "genre") -> dict:
    """
    assignments : [{"uri", "add": [labels], "remove": [labels], "existing": [labels]}]
    - ajoute les étiquettes validées (anti-doublon), retire celles décochées,
    - garantit la présence dans megacompil,
    - retire de la pile tout titre ayant >= 1 étiquette finale.
    mode="genre" cible les playlists G. ; mode="mood" cible les M. définies (§14).
    """
    if mode == "mood":
        signatures = await build_mood_signatures()
    else:
        signatures = await build_signatures()
    labels = signatures["labels"]  # label -> playlist_id

    # Coffre-fort d'abord : sans megacompil, on n'écrit RIEN et on ne vide pas la pile.
    # (Règle : un titre rangé est toujours dans megacompil.)
    mega = await _find_megacompil()
    if mega is None:
        raise RuntimeError(
            f'Playlist « {MEGA_NAME} » introuvable dans ton compte : rangement annulé '
            "(un titre ne doit jamais quitter la pile sans être dans megacompil)."
        )
    mega_id = mega["id"]

    add_by_pl: dict[str, list[str]] = {}
    remove_by_pl: dict[str, list[str]] = {}
    filed_uris: list[str] = []
    for a in assignments:
        uri = a.get("uri")
        if not uri:
            continue
        add = [l for l in a.get("add", []) if l in labels]
        remove = [l for l in a.get("remove", []) if l in labels]
        existing = [l for l in a.get("existing", []) if l in labels]
        for l in add:
            add_by_pl.setdefault(l, []).append(uri)
        for l in remove:
            remove_by_pl.setdefault(l, []).append(uri)
        final = (set(existing) - set(remove)) | set(add)
        if final:
            filed_uris.append(uri)

    # Ajouts dans les genres (anti-doublon live par playlist cible)
    added = 0
    for l, uris in add_by_pl.items():
        current = {t["uri"] for t in await spotify_service.get_playlist_tracks(labels[l])}
        new = [u for u in uris if u not in current]
        if new:
            await spotify_service.add_items(labels[l], new)
            added += len(new)

    # Retraits de genres (corrections de mauvais tri)
    removed_genres = 0
    for l, uris in remove_by_pl.items():
        if uris:
            await spotify_service.remove_items(labels[l], uris)
            removed_genres += len(uris)

    # Garantir la présence dans megacompil — anti-doublon LIVE (comme pour les genres),
    # jamais depuis la copie locale, qui peut être en retard et créer des doublons.
    mega_uris = {t["uri"] for t in await spotify_service.get_playlist_tracks(mega_id)}
    to_mega = [u for u in filed_uris if u not in mega_uris]
    if to_mega:
        await spotify_service.add_items(mega_id, to_mega)

    # Retrait de la pile
    removed_pile = 0
    if filed_uris:
        await spotify_service.remove_items(pile_id, filed_uris)
        removed_pile = len(filed_uris)

    _sync_local_after_apply(labels, add_by_pl, remove_by_pl, filed_uris, to_mega, mega_id, pile_id)

    logger.info(f"[DISQUAIRE] Apply : +{added} genres, -{removed_genres} genres, {removed_pile} retirés de la pile.")
    return {
        "added": added, "removed_from_genres": removed_genres,
        "filed": len(filed_uris), "removed_from_pile": removed_pile,
    }


# ─── Analyse de la pile COMPLÈTE (pas par lots) ──────────────────────────────

_analyse_state: dict = {
    "running": False, "done": 0, "total": 0, "finished": False,
    "error": None, "pile_id": None, "genres": [], "results": [],
    "mode": "genre", "stopped": False,
}
_analyse_cancel: bool = False


def stop_analyse() -> dict:
    """Demande l'arrêt de l'analyse en cours (effectif à la fin de la tranche en cours).

    Les résultats déjà produits sont conservés et restent validables.
    """
    global _analyse_cancel
    if not _analyse_state["running"]:
        return {"stopped": False, "detail": "Aucune analyse en cours."}
    _analyse_cancel = True
    return {"stopped": True}


def get_analyse_state() -> dict:
    """Progression uniquement (sans la grosse liste de résultats), pour le polling."""
    s = dict(_analyse_state)
    s.pop("results", None)
    return s


def get_analyse_result() -> dict:
    return {
        "pile_id": _analyse_state["pile_id"],
        "genres": _analyse_state["genres"],
        "tracks": _analyse_state["results"],
        "finished": _analyse_state["finished"],
        "error": _analyse_state["error"],
        "mode": _analyse_state.get("mode", "genre"),
        "stopped": _analyse_state.get("stopped", False),
    }


async def run_analyse_complete(mode: str = "genre", limit: int | None = None) -> None:
    """Classe TOUS les titres de la pile, par tranches, en tâche de fond.

    mode="genre" : comportement historique (cible les playlists G.).
    mode="mood"  : mode assisté du cadrage §14 (cible les M. définies) — propose des
                   AJOUTS et des RETRAITS de moods, indices Last.fm + genres inclus.
    limit        : galop d'essai — n'analyse que les N premiers titres de la pile
                   (validation à petit coût avant une passe complète).
    """
    global _analyse_state, _analyse_cancel
    if _analyse_state["running"]:
        return
    _analyse_cancel = False
    _analyse_state = {
        "running": True, "done": 0, "total": 0, "finished": False,
        "error": None, "pile_id": None, "genres": [], "results": [],
        "mode": mode, "stopped": False,
    }
    try:
        config = load_config()
        pile, _ = await _find_pile_and_genres()
        if pile is None:
            raise RuntimeError(f'Playlist « {PILE_NAME} » introuvable.')
        if mode == "mood":
            signatures = await build_mood_signatures()
            if not signatures["labels"]:
                raise RuntimeError("Aucun mood triable (playlists « M. » avec définition, cadrage §14).")
            label_by_lower = {l.lower(): l for l in signatures["labels"]}
        else:
            signatures = await build_signatures()
            if not signatures["labels"]:
                raise RuntimeError("Aucune playlist de genre (préfixe « G. »).")
            label_by_lower = {l.lower(): l for l in _classifiables(signatures["labels"])}

        pile_tracks = await spotify_service.get_playlist_tracks(pile["id"])
        if limit:
            pile_tracks = pile_tracks[:limit]
        uris = [t["uri"] for t in pile_tracks]
        _analyse_state["pile_id"] = pile["id"]
        _analyse_state["genres"] = list(signatures["labels"].keys())
        _analyse_state["total"] = len(pile_tracks)

        detailed_all = get_memberships_detailed(uris)
        model_id = config.get("model_preferences", {}).get("analysis") or "anthropic/claude-sonnet-4.5"
        # Genres d'artiste Spotify : comble ce que l'IA ignore (artistes obscurs).
        sp_genres = await spotify_service.get_artist_genres(uris)
        logger.info(f"[DISQUAIRE] Genres d'artiste Spotify récupérés pour {len(sp_genres)}/{len(pile_tracks)} titres.")
        lastfm_key = config.get("api_keys", {}).get("lastfm_key", "") if mode == "mood" else ""

        CHUNK = 40
        results: list[dict] = []
        for i in range(0, len(pile_tracks), CHUNK):
            if _analyse_cancel:
                _analyse_state["stopped"] = True
                logger.info(f"[DISQUAIRE] Analyse ({mode}) STOPPÉE à la demande — {len(results)} titres déjà traités, conservés.")
                break
            chunk = pile_tracks[i:i + CHUNK]
            if mode == "mood":
                lastfm_tags = await lastfm_service.get_tags_for_tracks(lastfm_key, chunk)
                ctx = {}
                for t in chunk:
                    d = detailed_all.get(t["uri"], {"genres": [], "moods": []})
                    # Seuls les moods TRIABLES sont visibles (prompt + écran + comptes) :
                    # les exclus (Pépite, Mix Drop, Passe partout…) appartiennent à Kinder,
                    # l'outil ne doit ni les montrer ni laisser croire qu'il peut les retirer.
                    moods_triables = []
                    for m in d["moods"]:
                        real = label_by_lower.get(_mood_label(m).lower())
                        if real and real not in moods_triables:
                            moods_triables.append(real)
                    ctx[t["uri"]] = {
                        "moods": moods_triables,
                        "genres": d["genres"],
                        "sp": sp_genres.get(t["uri"], []),
                        "lastfm": lastfm_tags.get(t["uri"], []),
                    }
                raw = await _call_model_logged(
                    config, model_id, _build_mood_prompt(signatures, chunk, ctx), "disquaire_mood_full"
                )
                proposals = _parse_mood_proposals(raw)
                for idx, t in enumerate(chunk):
                    prop = proposals.get(idx + 1, {"add": [], "remove": [], "reason": ""})
                    existants = ctx[t["uri"]]["moods"]
                    adds = []
                    for m in prop["add"]:
                        real = label_by_lower.get(str(m).strip().lower())
                        if real and real not in adds and real not in existants:
                            adds.append(real)
                    removes = []
                    for m in prop["remove"]:
                        real = label_by_lower.get(str(m).strip().lower())
                        if real and real in existants and real not in removes:
                            removes.append(real)
                    results.append({
                        "uri": t["uri"], "name": t["name"], "artists": t["artists"],
                        "proposed": adds, "remove_suggested": removes,
                        "existing_moods": existants,
                        "existing_genres": ctx[t["uri"]]["genres"],
                        "reason": prop.get("reason", ""),
                    })
            else:
                raw = await _call_model_logged(
                    config, model_id, _build_prompt(signatures, chunk, sp_genres), "disquaire_analyse_full"
                )
                proposals = _parse_proposals(raw, len(chunk))
                for idx, t in enumerate(chunk):
                    prop = proposals.get(idx + 1, {"genres": [], "reason": ""})
                    d = detailed_all.get(t["uri"], {"genres": [], "moods": []})
                    existing_g = d["genres"]
                    matched = []
                    for gname in prop.get("genres", []):
                        real = label_by_lower.get(str(gname).strip().lower())
                        if real and real not in matched and real not in existing_g:
                            matched.append(real)
                    results.append({
                        "uri": t["uri"], "name": t["name"], "artists": t["artists"],
                        "proposed": matched, "existing_genres": existing_g,
                        "existing_moods": d["moods"], "reason": prop.get("reason", ""),
                    })
            _analyse_state["done"] = len(results)
            _analyse_state["results"] = results

        _analyse_state["finished"] = True
        logger.info(f"[DISQUAIRE] Analyse complète ({mode}) : {len(results)} titres traités.")
    except Exception as e:
        logger.error(f"[DISQUAIRE] analyse complète ({mode}): {e}")
        _analyse_state["error"] = str(e)
        _analyse_state["finished"] = True
    finally:
        _analyse_state["running"] = False


# ─── Mode MOOD assisté (cadrage §14) ──────────────────────────────────────────

_MOOD_RE = re.compile(r"^m\.\s*", re.IGNORECASE)

# Référentiel des moods — DÉFINITIONS DE KINDER, copiées du CADRAGE_DISQUAIRE.md §14
# (source de vérité : le cadrage ; si Kinder amende une définition, répercuter ici).
# RÈGLE : un mood sans définition dans ce dict est HORS TRI — c'est ce qui exclut
# volontairement Pépite Auditive, Mix Drop et Passe partout. La LISTE des moods,
# elle, reste lue EN DIRECT dans les playlists « M. » du compte.
# Format : nom (sans préfixe M.) -> (axe, définition).
MOOD_DEFS: dict[str, tuple[str, str]] = {
    # Axe 1 — Ça bouge comment ? (danse)
    "Party": ("danse", "Électro dancefloor, let's go — la danse électro club."),
    "Son de teuf": ("danse", "Gros boom boom de teufeur — plus dur que Party : la teuf, pas le club."),
    "Calor": ("danse", "Rythme espagnol, tango, déhanché — la danse latine."),
    "DANCING": ("danse", "Besoin de bouger, danser — tout le reste qui fait danser (funk, rock'n'roll, disco), ni électro ni latin."),
    # Axe 2 — Ça m'énergise ? (boost)
    "Patate d'enfer": ("boost", "Coup de punch, go go go — le boost générique."),
    "Lets' get ready": ("boost", "Séance de salle, motivation sport — le boost d'effort."),
    "Sombre Dynamique": ("boost", "Rap sombre, méchant et boostant — le boost agressif."),
    # Axe 3 — Ça m'apaise ? (calme)
    "Douceur": ("calme", "Tout doux, PRESQUE PAS DE TEXTE — quasi instrumental (c'est le critère qui la sépare de Chill relax)."),
    "Chill relax": ("calme", "Tranquille, détendu — posé AVEC voix/texte."),
    "Wake up chill": ("calme", "Dimanche matin, réveil avec un bon café — le calme du matin."),
    # Axe 4 — Ça me fait quoi ? (émotion)
    "Mélancolie": ("émotion", "Triste, rupture, ça va pas."),
    "24K - Sunshine": ("émotion", "Joyeux, soleil, ça donne envie."),
    "Espoir Héroïque": ("émotion", "Donne espoir, on se sent plus fort, c'est héroïque."),
    "You're crazy of course": ("émotion", "Zinzin, un peu débile, mais ça fait du bien."),
    "Une étoile au milieu de la nuit": ("émotion", "Tête dans les étoiles, la mélodie m'emporte — rêverie, pas tristesse."),
    "Voyage": ("émotion", "Donne envie de partir — inspiration internationale."),
    "Mignon": ("émotion", "Toutes les chansons d'amour — mode loveur."),
    # Axe 5 — Je l'écoute quand/comment ? (usage)
    "Casque Session": ("usage", "Au casque : puissance mélodique monstrueuse, variations, vraie touche musicale."),
    "Au bistrot": ("usage", "Accordéon, chorale, chanson à boire."),
    "Électro de fond": ("usage", "Électro d'arrière-plan."),
    # Axe 6 — Je le connais ? (mémoire & notoriété)
    "Memories": ("mémoire", "Titres 2000-2018, époque collège/lycée, écoutés en boucle."),
    "Multi connu": ("mémoire", "Les titres que tout le monde connaît — notoriété universelle."),
    "Besoin de chanter ?🎤": ("mémoire", "Connu par cœur, à chanter à tue-tête."),
    # Rap à texte (transverse)
    "Flow Kiffant": ("rap", "La FORME du rap : flow musical, beat sympa et entraînant."),
    "Parole consciente": ("rap", "Le FOND du rap : paroles fortes, remise en question, philosophie."),
}


def _mood_label(name: str) -> str:
    return _MOOD_RE.sub("", name or "").strip()


async def build_mood_signatures() -> dict:
    """Moods TRIABLES, lus EN DIRECT : playlists « M. » du compte ∩ définitions du §14.

    Même principe que les genres (liste jamais figée), plus la règle du cadrage :
    un mood sans définition écrite est laissé de côté (renvoyé dans « exclus »).
    """
    playlists = await spotify_service.get_all_playlists()
    defs_low = {k.lower(): (k, v) for k, v in MOOD_DEFS.items()}
    labels: dict[str, str] = {}
    defs: dict[str, tuple[str, str]] = {}
    exclus: list[str] = []
    for p in playlists:
        nom = (p.get("name") or "").strip()
        if not _MOOD_RE.match(nom):
            continue
        label = _mood_label(nom)
        hit = defs_low.get(label.lower())
        if hit:
            labels[label] = p.get("id")
            defs[label] = hit[1]
        else:
            exclus.append(label)
    examples = _examples_from_local(labels)
    logger.info(f"[DISQUAIRE] Moods triables : {len(labels)} — exclus (sans définition) : {exclus}")
    return {"labels": labels, "defs": defs, "examples": examples, "exclus": exclus}


_AXES_TITRES = {
    "danse": "Ça bouge comment ? (danse)",
    "boost": "Ça m'énergise ? (boost)",
    "calme": "Ça m'apaise ? (calme)",
    "émotion": "Ça me fait quoi ? (émotion)",
    "usage": "Je l'écoute quand/comment ? (usage)",
    "mémoire": "Je le connais ? (mémoire & notoriété)",
    "rap": "Rap à texte (transverse : forme / fond)",
}


def _build_mood_prompt(sig: dict, tracks: list[dict], ctx: dict) -> str:
    """Prompt du mode Mood assisté (cadrage §14) — définitions de Kinder mot pour mot.

    ctx[uri] = {"moods": [déjà en place], "genres": [du titre], "sp": [genres artiste
    Spotify], "lastfm": [tags]} — les indices qui compensent le fait que l'IA n'entend
    pas la musique.
    """
    lines = [
        "Tu aides un utilisateur (Kinder) à ranger ses titres dans SES playlists de MOOD.",
        "Un MOOD décrit l'ÉNERGIE, l'ÉMOTION ou le MOMENT d'écoute d'un morceau — pas son style.",
        "",
        "SES MOODS, organisés en axes, définis PAR LUI (fais confiance à ces définitions) :",
    ]
    for axe in ("danse", "boost", "calme", "émotion", "usage", "mémoire", "rap"):
        moods_axe = [l for l in sig["labels"] if sig["defs"][l][0] == axe]
        if not moods_axe:
            continue
        lines.append(f"— Axe « {_AXES_TITRES[axe]} » :")
        for l in moods_axe:
            arts = sig["examples"].get(l) or []
            ex = f" (déjà dedans : {', '.join(arts[:8])})" if arts else ""
            lines.append(f"  - {l} : {sig['defs'][l][1]}{ex}")
    lines += [
        "",
        "TÂCHE — pour CHAQUE titre ci-dessous :",
        '  "add"    : les moods de la liste qui correspondent VRAIMENT à ce morceau (0 à n) ;',
        '  "remove" : parmi les moods où le titre est DÉJÀ (champ « déjà dans »), ceux où il',
        "             n'a VRAIMENT rien à faire au vu de la définition (sinon liste vide).",
        "",
        "RÈGLES IMPÉRATIVES :",
        "- Uniquement des moods de la liste ci-dessus, au mot EXACT.",
        "- Multi-mood bienvenu, MAIS deux moods du MÊME axe sur un titre = exception rare, à justifier.",
        "- Tu n'entends pas la musique. Appuie-toi sur ta connaissance du MORCEAU précis, son",
        "  genre (fourni), les genres Spotify de l'artiste et les tags Last.fm éventuels.",
        "- Si tu ne connais pas le morceau et que les indices ne suffisent pas : add = [].",
        "  Dans le doute on n'ajoute RIEN — l'utilisateur triera à la main, c'est voulu.",
        "- Ne propose un retrait que si l'incohérence est FLAGRANTE, jamais par confort.",
        "",
        "Titres :",
    ]
    for i, t in enumerate(tracks, start=1):
        c = ctx.get(t["uri"], {})
        infos = []
        if c.get("moods"):
            infos.append("déjà dans : " + ", ".join(c["moods"]))
        if c.get("genres"):
            infos.append("genre : " + ", ".join(c["genres"][:3]))
        if c.get("sp"):
            infos.append("artiste Spotify : " + ", ".join(c["sp"][:4]))
        if c.get("lastfm"):
            infos.append("tags Last.fm : " + ", ".join(c["lastfm"][:6]))
        artists = ", ".join(t["artists"]) or "artiste inconnu"
        suffixe = f"   [{' | '.join(infos)}]" if infos else ""
        lines.append(f'{i}. "{t["name"]}" — {artists}{suffixe}')
    lines += [
        "",
        'Réponds UNIQUEMENT en JSON, rien autour. Recopie les moods au mot exact. Format :',
        '[{"i":1,"add":["<mood exact>"],"remove":[],"reason":"courte raison"},',
        ' {"i":2,"add":[],"remove":[],"reason":"morceau inconnu, indices insuffisants"}]',
    ]
    return "\n".join(lines)


def _parse_mood_proposals(raw: str) -> dict:
    """{i: {"add": [...], "remove": [...], "reason": str}} depuis la réponse JSON de l'IA."""
    try:
        start, end = raw.find("["), raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        out = {}
        for item in json.loads(raw):
            i = item.get("i")
            if isinstance(i, int):
                out[i] = {
                    "add": item.get("add") or [],
                    "remove": item.get("remove") or [],
                    "reason": item.get("reason") or "",
                }
        return out
    except Exception as e:
        logger.error(f"[DISQUAIRE] Échec parsing propositions mood : {e} / brut : {raw[:200]}")
        return {}


# ─── Phase « Recenser » : base locale de la bibliothèque ─────────────────────

_recenser_state: dict = {
    "running": False, "phase": "", "playlists_done": 0, "playlists_total": 0,
    "tracks_seen": 0, "finished": False, "error": None, "summary": None,
}


def get_recenser_state() -> dict:
    return dict(_recenser_state)


def _classify_kind(name: str) -> str:
    n = (name or "").strip()
    if n.lower() == "megacompil":
        return "megacompil"
    if n.lower() == PILE_NAME.lower():
        return "pile"
    if _GENRE_RE.match(n):
        return "genre"
    if _MOOD_RE.match(n):
        return "mood"
    return "other"


async def run_recenser() -> None:
    """Aspire la bibliothèque (megacompil + genres + moods + pile) dans la base locale.

    Incrémental : une playlist dont le snapshot_id est inchangé n'est pas relue.
    L'état de progression est exposé via get_recenser_state().
    """
    global _recenser_state
    if _recenser_state["running"]:
        return
    _recenser_state = {
        "running": True, "phase": "Lecture de tes playlists…", "playlists_done": 0,
        "playlists_total": 0, "tracks_seen": 0, "finished": False, "error": None, "summary": None,
    }
    try:
        all_playlists = await spotify_service.get_all_playlists()
        relevant = [
            (p, _classify_kind(p.get("name")))
            for p in all_playlists
        ]
        relevant = [(p, k) for (p, k) in relevant if k in ("megacompil", "genre", "mood", "pile")]
        _recenser_state["playlists_total"] = len(relevant)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, snapshot_id FROM disquaire_playlists")
        known_snap = {r["id"]: r["snapshot_id"] for r in cur.fetchall()}
        counts = {"megacompil": 0, "genre": 0, "mood": 0, "pile": 0}

        for p, kind in relevant:
            pid, name, snap = p.get("id"), p.get("name"), p.get("snapshot_id")
            counts[kind] += 1
            _recenser_state["phase"] = f"Recensement : {name}"
            cur.execute(
                """INSERT INTO disquaire_playlists (id, name, kind, tracks_total, snapshot_id, last_synced)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(id) DO UPDATE SET name=excluded.name, kind=excluded.kind,
                       tracks_total=excluded.tracks_total, snapshot_id=excluded.snapshot_id,
                       last_synced=datetime('now')""",
                (pid, name, kind, (p.get("tracks") or {}).get("total", 0), snap),
            )
            conn.commit()  # libère le verrou d'écriture AVANT l'appel réseau qui suit
            # Incrémental : snapshot inchangé → on ne relit pas les titres.
            if snap and known_snap.get(pid) == snap:
                _recenser_state["playlists_done"] += 1
                continue

            tracks = await spotify_service.get_playlist_tracks(pid)
            cur.execute("DELETE FROM disquaire_membership WHERE playlist_id = ?", (pid,))
            for t in tracks:
                cur.execute(
                    "INSERT OR IGNORE INTO disquaire_tracks (uri, name, artists) VALUES (?, ?, ?)",
                    (t["uri"], t["name"], ", ".join(t["artists"])),
                )
                cur.execute(
                    "INSERT OR IGNORE INTO disquaire_membership (track_uri, playlist_id) VALUES (?, ?)",
                    (t["uri"], pid),
                )
            _recenser_state["tracks_seen"] += len(tracks)
            _recenser_state["playlists_done"] += 1
            conn.commit()

        # Ménage : réaligner la copie locale sur la vraie liste Spotify qu'on vient
        # de lire. On retire les playlists qui n'y sont plus (supprimées dans Spotify)
        # ou qui ont quitté les catégories suivies (renommées hors G./M./megacompil/pile).
        # Uniquement sur la base locale — aucune écriture Spotify.
        current_ids = [p.get("id") for p, _ in relevant]
        ph = ",".join("?" * len(current_ids)) if current_ids else "NULL"
        cur.execute(f"DELETE FROM disquaire_membership WHERE playlist_id NOT IN ({ph})", current_ids)
        cur.execute(f"DELETE FROM disquaire_playlists WHERE id NOT IN ({ph})", current_ids)
        removed_pl = cur.rowcount
        # Purge de l'annuaire : titres qui n'appartiennent plus à aucune playlist
        # (restes de playlists supprimées). Inertes, mais retirés pour garder la base saine.
        cur.execute(
            "DELETE FROM disquaire_tracks WHERE uri NOT IN (SELECT track_uri FROM disquaire_membership)"
        )
        removed_tracks = cur.rowcount

        conn.commit()
        cur.execute("SELECT COUNT(*) AS c FROM disquaire_tracks")
        total_tracks = cur.fetchone()["c"]
        conn.close()

        _recenser_state["summary"] = {"tracks_total": total_tracks, **counts}
        _recenser_state["phase"] = "Terminé"
        logger.info(f"[DISQUAIRE] Recensement terminé : {total_tracks} titres, {counts}, {removed_pl} playlists périmées retirées, {removed_tracks} titres orphelins purgés.")
    except Exception as e:
        logger.error(f"[DISQUAIRE] recenser: {e}")
        _recenser_state["error"] = str(e)
    finally:
        _recenser_state["running"] = False
        _recenser_state["finished"] = True


def get_local_stats() -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM disquaire_tracks")
    tracks = cur.fetchone()["c"]
    cur.execute("SELECT kind, COUNT(*) AS c FROM disquaire_playlists GROUP BY kind")
    by_kind = {r["kind"]: r["c"] for r in cur.fetchall()}
    cur.execute("SELECT MAX(last_synced) AS m FROM disquaire_playlists")
    last = cur.fetchone()["m"]
    conn.close()
    return {"tracks": tracks, "playlists_by_kind": by_kind, "last_synced": last}


def get_track_memberships(uri: str) -> list[str]:
    """Playlists genre/mood contenant ce titre (pour l'affichage « déjà dans »)."""
    return get_memberships_for([uri]).get(uri, [])


def get_etat() -> dict:
    """État complet du rangement, calculé sur la base locale recensée.

    Permet de COMPRENDRE l'organisation : combien de titres, combien déjà rangés
    en genre, combien d'orphelins (dans megacompil sans genre), répartitions, etc.
    """
    conn = get_connection()
    cur = conn.cursor()
    mega_id = _get_playlist_id_by_kind(cur, "megacompil")
    pile_id = _get_playlist_id_by_kind(cur, "pile")

    mega_uris: set[str] = set()
    if mega_id:
        cur.execute("SELECT track_uri FROM disquaire_membership WHERE playlist_id = ?", (mega_id,))
        mega_uris = {r["track_uri"] for r in cur.fetchall()}

    # Nombre de genres par titre
    cur.execute(
        """SELECT m.track_uri AS uri, COUNT(DISTINCT m.playlist_id) AS c
           FROM disquaire_membership m JOIN disquaire_playlists p ON p.id = m.playlist_id
           WHERE p.kind = 'genre' GROUP BY m.track_uri"""
    )
    genre_count = {r["uri"]: r["c"] for r in cur.fetchall()}
    genre_tracks = set(genre_count)

    def _per_kind(kind):
        cur.execute(
            """SELECT p.name AS name, COUNT(*) AS c
               FROM disquaire_membership m JOIN disquaire_playlists p ON p.id = m.playlist_id
               WHERE p.kind = ? GROUP BY p.id ORDER BY c DESC""",
            (kind,),
        )
        return [{"name": r["name"], "count": r["c"]} for r in cur.fetchall()]

    per_genre = _per_kind("genre")
    per_mood = _per_kind("mood")

    pile_count = 0
    if pile_id:
        cur.execute("SELECT COUNT(*) AS c FROM disquaire_membership WHERE playlist_id = ?", (pile_id,))
        pile_count = cur.fetchone()["c"]
    conn.close()

    total = len(mega_uris)
    in_genre = len(mega_uris & genre_tracks)
    return {
        "total": total,
        "in_genre": in_genre,
        "orphans": total - in_genre,
        "multi_genre": sum(1 for u in mega_uris if genre_count.get(u, 0) >= 2),
        "anomalies": len(genre_tracks - mega_uris),  # dans un genre mais pas dans megacompil
        "pile": pile_count,
        "genre_playlists": len(per_genre),
        "mood_playlists": len(per_mood),
        "per_genre": per_genre,
        "per_mood": per_mood,
    }


def _get_playlist_id_by_kind(cur, kind: str) -> str | None:
    cur.execute("SELECT id FROM disquaire_playlists WHERE kind = ? LIMIT 1", (kind,))
    row = cur.fetchone()
    return row["id"] if row else None


def get_memberships_detailed(uris: list[str]) -> dict[str, dict]:
    """Pour une liste d'uris : {uri: {"genres": [labels], "moods": [noms]}} (base locale)."""
    if not uris:
        return {}
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ",".join("?" * len(uris))
    cur.execute(
        f"""SELECT m.track_uri, p.name, p.kind FROM disquaire_membership m
            JOIN disquaire_playlists p ON p.id = m.playlist_id
            WHERE m.track_uri IN ({placeholders}) AND p.kind IN ('genre', 'mood')""",
        uris,
    )
    out: dict[str, dict] = {}
    for r in cur.fetchall():
        d = out.setdefault(r["track_uri"], {"genres": [], "moods": []})
        if r["kind"] == "genre":
            lbl = _genre_label(r["name"])
            if lbl not in d["genres"]:
                d["genres"].append(lbl)
        else:
            if r["name"] not in d["moods"]:
                d["moods"].append(r["name"])
    conn.close()
    return out


def get_memberships_for(uris: list[str]) -> dict[str, list[str]]:
    """Pour une liste d'uris, retourne {uri: [noms de playlists genre/mood]}.

    Exclut megacompil et la pile (chaque titre y est, sans intérêt à l'affichage).
    """
    if not uris:
        return {}
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ",".join("?" * len(uris))
    cur.execute(
        f"""SELECT m.track_uri, p.name FROM disquaire_membership m
            JOIN disquaire_playlists p ON p.id = m.playlist_id
            WHERE m.track_uri IN ({placeholders}) AND p.kind IN ('genre', 'mood')
            ORDER BY p.kind, p.name""",
        uris,
    )
    out: dict[str, list[str]] = {}
    for r in cur.fetchall():
        out.setdefault(r["track_uri"], []).append(r["name"])
    conn.close()
    return out
