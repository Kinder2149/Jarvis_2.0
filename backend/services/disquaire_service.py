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


def _build_signatures_local() -> dict:
    """Signatures depuis la base locale recensée (contenu COMPLET des playlists G.)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM disquaire_playlists WHERE kind = 'genre'")
    genres = cur.fetchall()
    labels: dict[str, str] = {}
    examples: dict[str, list[str]] = {}
    for g in genres:
        label = _genre_label(g["name"])
        if not label:
            continue
        labels[label] = g["id"]
        cur.execute(
            """SELECT t.artists FROM disquaire_membership m
               JOIN disquaire_tracks t ON t.uri = m.track_uri
               WHERE m.playlist_id = ?""",
            (g["id"],),
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
    return {"labels": labels, "examples": examples}


async def build_signatures(force: bool = False) -> dict:
    """Construit (et met en cache) une signature par genre : label → playlist_id + artistes types.

    Priorité à la base locale recensée (contenu complet). Repli sur la lecture live
    Spotify (60-100 titres/genre) si la bibliothèque n'a pas encore été recensée.
    """
    global _signatures
    if _signatures is not None and not force:
        return _signatures

    local = _build_signatures_local()
    if local["labels"]:
        _signatures = local
        logger.info(f"[DISQUAIRE] Signatures (base locale) : {len(local['labels'])} genres.")
        return _signatures

    _, genres = await _find_pile_and_genres()
    labels: dict[str, str] = {}
    examples: dict[str, list[str]] = {}
    for g in genres:
        label = _genre_label(g.get("name") or "")
        if not label:
            continue
        labels[label] = g.get("id")
        tracks = await spotify_service.get_playlist_tracks(g["id"], max_tracks=100)
        seen: list[str] = []
        for t in tracks:
            for a in t["artists"]:
                if a and a not in seen:
                    seen.append(a)
            if len(seen) >= 30:
                break
        examples[label] = seen[:30]
    _signatures = {"labels": labels, "examples": examples}
    logger.info(f"[DISQUAIRE] Signatures (live Spotify) : {len(labels)} genres.")
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
    lines = [
        "Tu es un disquaire expert qui range les titres d'un utilisateur dans SES propres playlists de genre.",
        "",
        "Voici ses GENRES (chacun est une playlist), avec des artistes représentatifs :",
    ]
    for label, arts in signatures["examples"].items():
        sample = ", ".join(arts[:20]) if arts else "(playlist vide)"
        lines.append(f"- {label} : {sample}")
    lines += [
        "",
        "TÂCHE : pour CHAQUE titre ci-dessous, liste TOUS les genres de la liste ci-dessus qui lui correspondent.",
        "",
        "RÈGLES IMPORTANTES :",
        "- Un même titre appartient TRÈS SOUVENT à PLUSIEURS genres à la fois. Exemple : un tube festif anglophone est à la fois « Party » ET « Pop anglaise ». Sois généreux : liste TOUS les genres pertinents, pas seulement le plus évident (vise en général 2 à 3 genres quand ça se justifie).",
        "- Appuie-toi À LA FOIS sur les artistes d'exemple ET sur le SENS du nom du genre.",
        "- N'utilise QUE des genres présents dans la liste ci-dessus, au mot exact.",
        "- Si vraiment aucun genre ne convient, mets une liste vide.",
        "",
        "Titres à classer :",
    ]
    for i, t in enumerate(tracks, start=1):
        artists = ", ".join(t["artists"]) or "artiste inconnu"
        lines.append(f'{i}. "{t["name"]}" — {artists}')
    lines += [
        "",
        'Réponds UNIQUEMENT en JSON, sans aucun texte autour, au format :',
        '[{"i": 1, "genres": ["Party", "Pop anglaise"], "reason": "courte raison"}, ...]',
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


async def apply(assignments: list[dict], pile_id: str) -> dict:
    """
    assignments : [{"uri", "add": [labels], "remove": [labels], "existing": [labels]}]
    - ajoute les genres verts (anti-doublon), retire les genres bleus décochés,
    - garantit la présence dans megacompil,
    - retire de la pile tout titre ayant >= 1 genre final.
    """
    signatures = await build_signatures()
    labels = signatures["labels"]  # label -> playlist_id

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

    # Garantir la présence dans megacompil
    conn = get_connection()
    cur = conn.cursor()
    mega_id = _get_playlist_id_by_kind(cur, "megacompil")
    mega_uris = set()
    if mega_id:
        cur.execute("SELECT track_uri FROM disquaire_membership WHERE playlist_id = ?", (mega_id,))
        mega_uris = {r["track_uri"] for r in cur.fetchall()}
    conn.close()
    to_mega = [u for u in filed_uris if u not in mega_uris]
    if mega_id and to_mega:
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
}


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
    }


async def run_analyse_complete() -> None:
    """Classe TOUS les titres de la pile, par tranches, en tâche de fond."""
    global _analyse_state
    if _analyse_state["running"]:
        return
    _analyse_state = {
        "running": True, "done": 0, "total": 0, "finished": False,
        "error": None, "pile_id": None, "genres": [], "results": [],
    }
    try:
        config = load_config()
        signatures = await build_signatures()
        pile, _ = await _find_pile_and_genres()
        if pile is None:
            raise RuntimeError(f'Playlist « {PILE_NAME} » introuvable.')
        if not signatures["labels"]:
            raise RuntimeError("Aucune playlist de genre (préfixe « G. »).")

        pile_tracks = await spotify_service.get_playlist_tracks(pile["id"])
        _analyse_state["pile_id"] = pile["id"]
        _analyse_state["genres"] = list(signatures["labels"].keys())
        _analyse_state["total"] = len(pile_tracks)

        label_by_lower = {l.lower(): l for l in signatures["labels"]}
        detailed_all = get_memberships_detailed([t["uri"] for t in pile_tracks])
        model_id = config.get("model_preferences", {}).get("analysis") or "anthropic/claude-sonnet-4.5"

        CHUNK = 40
        results: list[dict] = []
        for i in range(0, len(pile_tracks), CHUNK):
            chunk = pile_tracks[i:i + CHUNK]
            raw = await model_router.call_model(
                model_id=model_id,
                messages=[{"role": "user", "content": _build_prompt(signatures, chunk)}],
                api_keys=config.get("api_keys", {}),
                session_id=0, step_name="disquaire_analyse_full",
                model_type="analysis", db_conn=None, module_name="disquaire",
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
        logger.info(f"[DISQUAIRE] Analyse complète : {len(results)} titres classés.")
    except Exception as e:
        logger.error(f"[DISQUAIRE] analyse complète: {e}")
        _analyse_state["error"] = str(e)
        _analyse_state["finished"] = True
    finally:
        _analyse_state["running"] = False


# ─── Phase « Recenser » : base locale de la bibliothèque ─────────────────────

_MOOD_RE = re.compile(r"^m\.\s*", re.IGNORECASE)

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

        conn.commit()
        cur.execute("SELECT COUNT(*) AS c FROM disquaire_tracks")
        total_tracks = cur.fetchone()["c"]
        conn.close()

        _recenser_state["summary"] = {"tracks_total": total_tracks, **counts}
        _recenser_state["phase"] = "Terminé"
        logger.info(f"[DISQUAIRE] Recensement terminé : {total_tracks} titres, {counts}")
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
