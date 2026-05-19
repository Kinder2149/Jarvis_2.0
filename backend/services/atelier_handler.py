import asyncio
import json
import logging
import re
from urllib.parse import urlparse
from backend.database import get_connection

logger = logging.getLogger("jarvis")

_ABORT_SIGNALS = [
    "annule", "annuler", "stop", "laisse tomber", "oublie",
    "autre chose", "finalement", "pas ça", "mauvais",
    "j'ai fait une erreur", "je veux pas", "je ne veux pas",
    "ignore", "recommence", "abort", "erreur"
]

_NO_SITE_SIGNALS = [
    "pas de site", "sans site", "pas d'url", "pas d'adresse",
    "aucun site", "aucune url", "pas encore de site",
]

_CONFIRM_SIGNALS = [
    "oui", "ok", "go", "vas-y", "lance", "yes", "valide", "validé",
    "parfait", "super", "c'est bon", "allez", "yep", "ouais", "bien sûr",
    "affirmatif", "absolument", "carrément"
]


def _is_abort_signal(message: str) -> bool:
    msg_lower = message.lower().strip()
    if msg_lower.startswith("non"):
        return True
    return any(sig in msg_lower for sig in _ABORT_SIGNALS)


def _is_no_site_signal(message: str) -> bool:
    msg_lower = message.lower().strip()
    if msg_lower in ("-", ".", "rien", "skip", "passe", "non", "néant"):
        return True
    return any(sig in msg_lower for sig in _NO_SITE_SIGNALS)


def _is_confirm_signal(message: str) -> bool:
    msg_lower = message.lower().strip()
    if msg_lower.startswith("oui") or msg_lower in ("go", "ok", "yes"):
        return True
    return any(sig in msg_lower for sig in _CONFIRM_SIGNALS)


# ─── Point d'entrée ──────────────────────────────────────────────────────────

async def handle(conversation_id: int, message: str,
                 current_instance_ref: dict | None, db, config: dict) -> tuple:
    """
    Flow ATELIER depuis JARVIS — 4 étapes :
      1. URL reçue → scrape + extraction LLM → résumé + demande confirmation
      2. Confirmation → bypass step 0 + lancement pipeline phase 1 (bg)
      3. Phase 1 terminée (bg injecte message checkpoint) → user valide proposition
      4. Validation checkpoint → phase 2 (bg) → démo prête, JARVIS notifie
    """
    # État : collecte en cours (nom → URL → note)
    if current_instance_ref and current_instance_ref.get("type") == "atelier_collecting":
        return await _handle_collecting(conversation_id, message, current_instance_ref, db, config)

    # État : checkpoint en attente (phase 1 terminée, attente validation proposition)
    if current_instance_ref and current_instance_ref.get("type") == "atelier_checkpoint":
        return await _handle_checkpoint_confirm(conversation_id, message, current_instance_ref, db, config)

    # État : confirmation en attente (URL analysée, attente lancement)
    if current_instance_ref and current_instance_ref.get("type") == "atelier_confirm":
        return await _handle_confirm(conversation_id, message, current_instance_ref, db, config)

    # État pipeline en cours — l'utilisateur veut peut-être un statut
    if current_instance_ref and current_instance_ref.get("type") in ("atelier_pipeline", "atelier_done"):
        prospect_id = current_instance_ref.get("prospect_id")
        nom = current_instance_ref.get("nom", "le prospect")
        session_id = current_instance_ref.get("session_id")
        if session_id:
            db2 = get_connection()
            try:
                cursor = db2.cursor()
                cursor.execute("SELECT status FROM sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                status = row["status"] if row else "UNKNOWN"
            finally:
                db2.close()
            labels = {
                "RUNNING": "en cours ⚙️",
                "WAITING_VALIDATION": "en attente de validation 👀",
                "COMPLETED": "terminé ✅",
                "FAILED": "échoué ❌",
                "ABORTED": "interrompu ⛔",
            }
            label = labels.get(status, status)
            content = (
                f"[ATELIER] Pipeline **{nom}** — statut : {label}\n\n"
                f"[→ Voir dans l'Atelier](atelier.html?prospect_id={prospect_id})"
            )
            return content, "ATELIER", current_instance_ref, False, None

    # Abandon (avec ou sans état actif)
    if _is_abort_signal(message):
        if current_instance_ref:
            return ("Flow annulé, aucun prospect créé. Comment puis-je t'aider ?",
                    "ATELIER", None, False, None)
        return ("Rien à annuler en cours. Comment puis-je t'aider ?",
                "ATELIER", None, False, None)

    # URL détectée → nouveau prospect (flow direct)
    url_match = re.search(r'https?://\S+', message)
    if url_match:
        url = url_match.group(0).rstrip('/.,;)')
        return await _handle_new_prospect(url, message, db, config)

    # Pas d'URL → démarrer la collecte en 3 étapes
    state = {"type": "atelier_collecting", "step": "nom"}
    return (
        "Pour créer un prospect, j'ai besoin de quelques infos.\n\n"
        "Quel est le **nom de l'établissement** ?",
        "ATELIER", state, False, None
    )


# ─── Collecte 3 étapes (nom → URL → note) ────────────────────────────────────

async def _handle_collecting(conversation_id: int, message: str,
                              state: dict, db, config: dict) -> tuple:
    """Flow de collecte progressif : nom → URL → note → création prospect."""
    step = state.get("step", "nom")

    if _is_abort_signal(message):
        return ("Flow annulé, aucun prospect créé. Comment puis-je t'aider ?",
                "ATELIER", None, False, None)

    if step == "nom":
        nom = message.strip()
        new_state = {"type": "atelier_collecting", "step": "url", "nom": nom}
        return (
            f"Parfait, **{nom}** !\n\n"
            f"Quel est l'**URL du site web** ? "
            f"*(tape « pas de site » si aucun site web)*",
            "ATELIER", new_state, False, None
        )

    elif step == "url":
        nom = state.get("nom", "")
        url_match = re.search(r'https?://\S+', message)
        if url_match:
            url = url_match.group(0).rstrip('/.,;)')
        elif _is_no_site_signal(message):
            url = None
        else:
            stripped = message.strip().rstrip('/.,;)')
            url = f"https://{stripped}" if stripped and '.' in stripped else None

        new_state = {"type": "atelier_collecting", "step": "note", "nom": nom, "url": url}
        return (
            "Noté ✅\n\n"
            "Une **note contextuelle** à ajouter ? "
            "*(optionnel — tape « - » pour passer)*",
            "ATELIER", new_state, False, None
        )

    elif step == "note":
        nom = state.get("nom", "")
        url = state.get("url")
        _skip = {"-", ".", "rien", "non", "skip", "passe", "pas de note", "aucune note"}
        note = message.strip() if message.strip().lower() not in _skip else None

        prospect_id = _create_prospect(nom, url, note, db)

        if url:
            return await _finalize_collecting_with_url(
                prospect_id, nom, url, conversation_id, db, config
            )
        content = (
            f"✅ **Prospect {nom} créé !**\n\n"
            f"Aucun site à analyser — tu peux compléter les infos depuis l'Atelier.\n\n"
            f"[→ Ouvrir dans l'Atelier](atelier.html?prospect_id={prospect_id})"
        )
        return content, "ATELIER", None, False, None

    return ("Erreur interne ATELIER — état de collecte inconnu.", "ATELIER", None, False, None)


async def _finalize_collecting_with_url(prospect_id: int, nom: str, url: str,
                                         conversation_id: int, db, config: dict) -> tuple:
    """Scrape le site, met à jour le prospect, lance le pipeline."""
    from backend.services.atelier_service import fetch_url

    site_data = await fetch_url(url)
    fetch_ok = site_data.get("text") and not site_data["text"].startswith("[Erreur")

    form_data = await _extract_form_data(url, site_data, config, db) if fetch_ok else _fallback_form_data(url)
    form_data["nom_restaurant"] = nom
    _update_prospect(prospect_id, nom, json.dumps(form_data, ensure_ascii=False), db)

    try:
        session_id = await _launch_pipeline(prospect_id, conversation_id, nom, db, config)
        content = (
            f"✅ **Prospect {nom} créé !**\n\n"
            f"L'analyse et la génération de la proposition démarrent en arrière-plan. "
            f"Je te notifie quand c'est prêt.\n\n"
            f"[→ Suivre dans l'Atelier](atelier.html?prospect_id={prospect_id})"
        )
        return content, "ATELIER", {
            "type": "atelier_pipeline", "prospect_id": prospect_id,
            "session_id": session_id, "nom": nom
        }, False, None
    except Exception as e:
        logger.error(f"[ATELIER] Erreur lancement après collecte: {e}")
        content = (
            f"✅ **Prospect {nom} créé !**\n\n"
            f"Le pipeline n'a pas pu démarrer — lance-le manuellement depuis l'Atelier.\n\n"
            f"[→ Ouvrir dans l'Atelier](atelier.html?prospect_id={prospect_id})"
        )
        return content, "ATELIER", None, False, None


# ─── Nouveau prospect ─────────────────────────────────────────────────────────

async def _handle_new_prospect(url: str, message: str, db, config: dict) -> tuple:
    """Crée le prospect, scrape le site, extrait les données, demande confirmation."""
    from backend.services.atelier_service import fetch_url

    nom_temp = _extract_name_hint(message, url)
    prospect_id = _create_prospect(nom_temp, url, None, db)

    site_data = await fetch_url(url)
    fetch_ok = site_data.get("text") and not site_data["text"].startswith("[Erreur")

    if fetch_ok:
        form_data = await _extract_form_data(url, site_data, config, db)
    else:
        logger.warning(f"[ATELIER] Scraping échoué pour {url} — fallback domaine")
        form_data = _fallback_form_data(url)

    nom = form_data.get("nom_restaurant") or nom_temp
    _update_prospect(prospect_id, nom, json.dumps(form_data, ensure_ascii=False), db)

    summary = _build_summary(form_data)
    state = {"type": "atelier_confirm", "prospect_id": prospect_id, "nom": nom}
    content = (
        f"✅ J'ai analysé **{url}**\n\n"
        f"{summary}\n\n"
        f"**Je lance la génération de la démo ?** *(oui pour démarrer · non pour annuler)*"
    )
    return content, "ATELIER", state, False, None


# ─── Confirmation lancement pipeline ─────────────────────────────────────────

async def _handle_confirm(conversation_id: int, message: str,
                          state: dict, db, config: dict) -> tuple:
    """Gère la réponse oui/non à la demande de lancement du pipeline."""
    prospect_id = state["prospect_id"]
    nom = state.get("nom", "ce prospect")

    if _is_confirm_signal(message):
        try:
            session_id = await _launch_pipeline(prospect_id, conversation_id, nom, db, config)
            instance_ref = {
                "type": "atelier_pipeline",
                "prospect_id": prospect_id,
                "session_id": session_id,
                "nom": nom
            }
            content = (
                f"🚀 **Pipeline lancé pour {nom} !**\n\n"
                f"J'analyse le site, qualifie le prospect et génère la proposition "
                f"automatiquement. Je te présente la proposition pour validation dès "
                f"que l'analyse est terminée — aucune action requise de ta part pour l'instant.\n\n"
                f"[→ Suivre dans l'Atelier](atelier.html?prospect_id={prospect_id})"
            )
            return content, "ATELIER", instance_ref, False, None
        except Exception as e:
            logger.error(f"[ATELIER] Erreur lancement pipeline: {e}")
            return (
                f"⚠️ Erreur au lancement : {e}\n\n"
                f"[→ Ouvrir manuellement dans l'Atelier](atelier.html?prospect_id={prospect_id})",
                "ATELIER", None, False, None
            )
    else:
        return (
            f"D'accord, pipeline annulé. **{nom}** est enregistré dans l'Atelier, "
            f"tu pourras le relancer quand tu veux.\n\n"
            f"[→ Ouvrir dans l'Atelier](atelier.html?prospect_id={prospect_id})",
            "ATELIER", None, False, None
        )


# ─── Checkpoint — validation de la proposition ───────────────────────────────

async def _handle_checkpoint_confirm(conversation_id: int, message: str,
                                      state: dict, db, config: dict) -> tuple:
    """Gère la réponse oui/non au checkpoint (validation proposition → lancement démo)."""
    session_id = state["session_id"]
    prospect_id = state["prospect_id"]
    nom = state.get("nom", "ce prospect")

    if _is_confirm_signal(message):
        try:
            cursor = db.cursor()
            # Marquer step 4 (checkpoint) comme COMPLETED
            cursor.execute("""
                UPDATE pipeline_steps
                SET status = 'COMPLETED', validated_at = datetime('now')
                WHERE session_id = ? AND step_index = 4
            """, (session_id,))
            cursor.execute(
                "UPDATE sessions SET current_step_index = 5, status = 'RUNNING', "
                "updated_at = datetime('now') WHERE id = ?",
                (session_id,)
            )
            db.commit()

            # Lancer la phase 2 en arrière-plan
            asyncio.create_task(_run_phase2_bg(session_id, conversation_id, prospect_id, nom, config))

            instance_ref = {
                "type": "atelier_pipeline",
                "session_id": session_id,
                "prospect_id": prospect_id,
                "nom": nom
            }
            content = (
                f"🚀 **Génération de la démo lancée pour {nom} !**\n\n"
                f"Je génère maintenant tous les fichiers (CSS, HTML, JS, admin). "
                f"Je te notifie dès que c'est prêt.\n\n"
                f"[→ Suivre dans l'Atelier](atelier.html?prospect_id={prospect_id})"
            )
            return content, "ATELIER", instance_ref, False, None

        except Exception as e:
            logger.error(f"[ATELIER] Erreur lancement phase 2: {e}")
            return (
                f"⚠️ Erreur au lancement de la génération : {e}\n\n"
                f"[→ Ouvrir dans l'Atelier](atelier.html?prospect_id={prospect_id})",
                "ATELIER", None, False, None
            )

    elif _is_abort_signal(message):
        cursor = db.cursor()
        cursor.execute(
            "UPDATE prospects SET statut = 'en_attente', updated_at = datetime('now') WHERE id = ?",
            (prospect_id,)
        )
        db.commit()
        return (
            f"D'accord, génération annulée. **{nom}** reste dans l'Atelier avec sa proposition, "
            f"tu pourras relancer la démo quand tu veux.\n\n"
            f"[→ Ouvrir dans l'Atelier](atelier.html?prospect_id={prospect_id})",
            "ATELIER", None, False, None
        )

    else:
        # Signal ambigu — re-présenter le choix sans perdre l'état
        return (
            f"Je n'ai pas compris. Pour la démo de **{nom}** :\n"
            f"- Réponds **oui** pour lancer la génération\n"
            f"- Réponds **non** pour annuler",
            "ATELIER", state, False, None
        )


# ─── Lancement pipeline (fire-and-forget phase 1) ────────────────────────────

async def _launch_pipeline(prospect_id: int, conversation_id: int,
                            nom: str, db, config: dict) -> int:
    """
    Crée la session, bypasse step 0 (saisie déjà remplie par JARVIS),
    puis lance la phase 1 en tâche asyncio de fond.
    Retourne immédiatement le session_id.
    """
    from backend.services.pipeline_engine import create_session

    cursor = db.cursor()

    cursor.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,))
    prospect_row = cursor.fetchone()
    if not prospect_row:
        raise ValueError(f"Prospect {prospect_id} introuvable")
    form_data_json = prospect_row["form_data"] or "{}"

    # Récupérer ou créer le projet système Atelier
    cursor.execute("SELECT id FROM projects WHERE path = ?", ("__atelier__",))
    project_row = cursor.fetchone()
    if not project_row:
        cursor.execute(
            "INSERT INTO projects (name, path, module_type) VALUES (?, ?, ?)",
            ("Atelier Connecté", "__atelier__", "code")
        )
        db.commit()
        project_id = cursor.lastrowid
    else:
        project_id = project_row["id"]

    # Créer la session
    session = create_session(project_id, "atelier_restauration", form_data_json, db)
    session_id = session["id"]

    # Lier la session au prospect
    cursor.execute(
        "UPDATE prospects SET session_id = ?, statut = ?, updated_at = datetime('now') WHERE id = ?",
        (session_id, "en_analyse", prospect_id)
    )

    # ── BYPASS step 0 ────────────────────────────────────────────────────────
    # form_data est déjà rempli par JARVIS → marquer step 0 COMPLETED directement
    cursor.execute("""
        UPDATE pipeline_steps
        SET status = 'COMPLETED', output_data = ?, validated_at = datetime('now')
        WHERE session_id = ? AND step_index = 0
    """, (form_data_json, session_id))
    cursor.execute(
        "UPDATE sessions SET current_step_index = 1 WHERE id = ?",
        (session_id,)
    )
    db.commit()

    # Lancer la phase 1 en arrière-plan (sans bloquer la réponse JARVIS)
    asyncio.create_task(
        _run_phase1_bg(session_id, conversation_id, prospect_id, nom, config)
    )

    return session_id


# ─── Phase 1 background : analyse → qualification → proposition ───────────────

async def _run_phase1_bg(session_id: int, conversation_id: int,
                          prospect_id: int, nom: str, config: dict) -> None:
    """
    Exécute les steps 1-3 (analyse_site, qualification, proposition) en arrière-plan.
    À la fin, injecte un message JARVIS avec la proposition et demande la validation.
    """
    db = get_connection()
    try:
        from backend.services.pipeline_engine import execute_step

        result = await execute_step(session_id, 1, "__atelier__", db, config)
        count = 0
        MAX_AUTO = 10
        while result.get("status") == "auto_completed" and count < MAX_AUTO:
            count += 1
            next_step = result["next_step"]
            if next_step >= 4:
                # Arrêt avant le step 4 (checkpoint) — géré séparément
                break
            result = await execute_step(session_id, next_step, "__atelier__", db, config)

        # Extraire la proposition (step 3)
        cursor = db.cursor()
        cursor.execute("""
            SELECT output_data FROM pipeline_steps
            WHERE session_id = ? AND step_index = 3
        """, (session_id,))
        row = cursor.fetchone()
        proposition = (row["output_data"] or "").strip()[:1200] if row else ""

        # Construire le message checkpoint
        state = {
            "type": "atelier_checkpoint",
            "session_id": session_id,
            "prospect_id": prospect_id,
            "nom": nom
        }

        if proposition:
            content = (
                f"📊 **Analyse complète pour {nom}**\n\n"
                f"**Proposition générée :**\n\n{proposition}\n\n"
                f"---\n"
                f"✅ **Je génère la démo ?** "
                f"*(oui pour lancer la génération complète · non pour annuler)*"
            )
        else:
            content = (
                f"📊 **Analyse complète pour {nom}**\n\n"
                f"Le prospect est qualifié et la proposition est prête.\n\n"
                f"✅ **Je génère la démo ?** "
                f"*(oui pour lancer la génération complète · non pour annuler)*"
            )

        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'ATELIER', ?, datetime('now'))
        """, (
            conversation_id,
            content,
            json.dumps(state, ensure_ascii=False)
        ))
        # Mettre à jour la conversation updated_at pour que le frontend détecte le nouveau message
        cursor.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        db.commit()
        logger.info(f"[ATELIER] Phase 1 terminée — checkpoint injecté conv={conversation_id}")

    except Exception as e:
        logger.error(f"[ATELIER] Erreur phase 1 bg (session={session_id}): {e}")
        try:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
                VALUES (?, 'assistant', ?, 'ATELIER', NULL, datetime('now'))
            """, (conversation_id, f"⚠️ Erreur lors de l'analyse du prospect : {e}"))
            cursor.execute(
                "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
                (conversation_id,)
            )
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ─── Phase 2 background : génération démo ─────────────────────────────────────

async def _run_phase2_bg(session_id: int, conversation_id: int,
                          prospect_id: int, nom: str, config: dict) -> None:
    """
    Exécute les steps 5-12 (brief_technique → export) en arrière-plan.
    À la fin, injecte un message JARVIS "Démo prête".
    """
    db = get_connection()
    try:
        from backend.services.pipeline_engine import execute_step

        result = await execute_step(session_id, 5, "__atelier__", db, config)
        count = 0
        MAX_AUTO = 15
        while result.get("status") == "auto_completed" and count < MAX_AUTO:
            count += 1
            result = await execute_step(session_id, result["next_step"], "__atelier__", db, config)

        # Vérifier le statut final de la session
        cursor = db.cursor()
        cursor.execute("SELECT status FROM sessions WHERE id = ?", (session_id,))
        session_row = cursor.fetchone()
        session_status = session_row["status"] if session_row else "UNKNOWN"

        # Récupérer demo_url/demo_path du prospect
        cursor.execute("SELECT demo_url, demo_path FROM prospects WHERE id = ?", (prospect_id,))
        prospect_row = cursor.fetchone()
        demo_url = prospect_row["demo_url"] if prospect_row else None

        if session_status == "COMPLETED":
            # Mettre à jour le statut du prospect
            cursor.execute(
                "UPDATE prospects SET statut = 'demo_prete', updated_at = datetime('now') WHERE id = ?",
                (prospect_id,)
            )
            content = f"🎉 **Démo prête pour {nom} !**\n\n"
            if demo_url:
                content += f"[→ Voir la démo]({demo_url})\n"
            content += f"[→ Ouvrir dans l'Atelier](atelier.html?prospect_id={prospect_id})"
            state = {
                "type": "atelier_done",
                "session_id": session_id,
                "prospect_id": prospect_id,
                "nom": nom
            }
        else:
            content = (
                f"⚠️ La génération pour **{nom}** s'est arrêtée (statut : {session_status}).\n\n"
                f"[→ Voir dans l'Atelier](atelier.html?prospect_id={prospect_id})"
            )
            state = None

        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'ATELIER', ?, datetime('now'))
        """, (
            conversation_id,
            content,
            json.dumps(state, ensure_ascii=False) if state else None
        ))
        cursor.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        db.commit()
        logger.info(f"[ATELIER] Phase 2 terminée — statut={session_status} conv={conversation_id}")

    except Exception as e:
        logger.error(f"[ATELIER] Erreur phase 2 bg (session={session_id}): {e}")
        try:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
                VALUES (?, 'assistant', ?, 'ATELIER', NULL, datetime('now'))
            """, (conversation_id, f"⚠️ Erreur lors de la génération de la démo : {e}"))
            cursor.execute(
                "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
                (conversation_id,)
            )
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ─── Extraction LLM ──────────────────────────────────────────────────────────

async def _extract_form_data(url: str, site_data: dict,
                              config: dict, db) -> dict:
    """Extrait les données SAISIE depuis le contenu scrapé du site."""
    from backend.services.model_router import get_model_id, call_model

    text = site_data.get("text", "")[:3000]
    title = site_data.get("title", "")

    prompt = f"""Analyse ce site web de restaurant/établissement et extrait les informations clés.

Titre de la page : {title}
URL : {url}
Contenu extrait :
{text}

Réponds UNIQUEMENT en JSON valide, aucun texte autour :
{{
  "nom_restaurant": "Nom commercial exact de l'établissement",
  "type_cuisine": "Type de cuisine ou concept (ex: Brasserie, Bistronomie, Cave à vins...)",
  "description": "Description percutante en 1-2 phrases",
  "ambiance": "Ambiance / positionnement (ex: Gastronomique, Familial, Décontracté...)",
  "telephone": "Numéro de téléphone si trouvé ou null",
  "adresse": "Adresse complète si trouvée ou null",
  "outils": {{
    "evenements": true,
    "avis": true,
    "emporter": false
  }}
}}

Si une info est introuvable, déduis une valeur raisonnable depuis le contexte. Ne laisse pas de champ vide."""

    try:
        model_id = get_model_id("structuring", config)
        response = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config["api_keys"],
            session_id=None,
            step_name="atelier_extract_saisie",
            model_type="structuring",
            db_conn=db,
            module_name="atelier"
        )
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
        return json.loads(clean)
    except Exception as e:
        logger.warning(f"[ATELIER] Extraction LLM échouée ({e}), fallback")
        return {
            "nom_restaurant": title or _domain_to_name(url),
            "type_cuisine": "Restaurant",
            "description": "",
            "ambiance": "",
            "telephone": None,
            "adresse": None,
            "outils": {"evenements": True, "avis": True, "emporter": False}
        }


def _fallback_form_data(url: str) -> dict:
    """Données minimales basées sur le domaine quand le scraping échoue."""
    return {
        "nom_restaurant": _domain_to_name(url),
        "type_cuisine": "Restaurant",
        "description": "",
        "ambiance": "",
        "telephone": None,
        "adresse": None,
        "outils": {"evenements": True, "avis": True, "emporter": False}
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_summary(form_data: dict) -> str:
    """Construit un résumé lisible des données extraites."""
    nom      = form_data.get("nom_restaurant", "—")
    cuisine  = form_data.get("type_cuisine", "")
    desc     = form_data.get("description", "")
    ambiance = form_data.get("ambiance", "")
    tel      = form_data.get("telephone")
    adresse  = form_data.get("adresse")
    outils   = form_data.get("outils", {})

    outils_list = ["Réservations ✓", "Menu/Ardoise ✓"]
    if outils.get("evenements"):  outils_list.append("Événements ✓")
    if outils.get("avis"):        outils_list.append("Avis clients ✓")
    if outils.get("emporter"):    outils_list.append("Commande à emporter ✓")

    def _v(val):
        return val if val and str(val).strip().lower() not in ("none", "null", "") else None

    lines = [f"**{_v(nom) or '—'}**" + (f" — {cuisine}" if _v(cuisine) else "")]
    if _v(desc):     lines.append(f"_{desc}_")
    if _v(ambiance): lines.append(f"Ambiance : {ambiance}")
    if _v(tel):      lines.append(f"Tél : {tel}")
    if _v(adresse):  lines.append(f"Adresse : {adresse}")
    lines.append(f"Outils retenus : {', '.join(outils_list)}")

    return "\n".join(lines)


def _extract_name_hint(message: str, url: str) -> str:
    """Extrait un nom depuis le message, sinon depuis le domaine de l'URL."""
    url_match = re.search(r'https?://\S+', message)
    if url_match:
        nom_part = message[:url_match.start()].strip()
        nom_part = re.sub(
            r'^(nouveau\s+prospect|prospect|ajoute|créer|travailler|j\'ai|voici|c\'est)\s+',
            '', nom_part, flags=re.IGNORECASE
        ).strip()
        if len(nom_part) > 2:
            return nom_part
    return _domain_to_name(url)


def _domain_to_name(url: str) -> str:
    domain = urlparse(url).netloc.replace("www.", "")
    return domain.split(".")[0].replace("-", " ").title()


def _create_prospect(nom: str, url: str | None, notes: str | None, db) -> int:
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(prospects)")
    columns = [row[1] for row in cursor.fetchall()]
    if "notes" in columns:
        cursor.execute(
            "INSERT INTO prospects (nom, categorie, url, notes) VALUES (?, 'restauration', ?, ?)",
            (nom, url, notes)
        )
    else:
        cursor.execute(
            "INSERT INTO prospects (nom, categorie, url) VALUES (?, 'restauration', ?)",
            (nom, url)
        )
    db.commit()
    return cursor.lastrowid


def _update_prospect(prospect_id: int, nom: str, form_data_json: str, db):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE prospects SET nom = ?, form_data = ?, updated_at = datetime('now') WHERE id = ?",
        (nom, form_data_json, prospect_id)
    )
    db.commit()
