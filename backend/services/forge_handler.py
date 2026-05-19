import json
import logging
import asyncio
from pathlib import Path
from backend.database import load_config
from backend.services.model_router import get_model_id, call_model
from backend.services import pipeline_engine

logger = logging.getLogger("jarvis")


async def start(mission_prompt_id: int, conversation_id: int, db, inject_message: bool = True) -> dict:
    """
    Démarre un pipeline FORGE depuis un mission_prompt figé.
    Vérifie le filesystem, crée la session, met à jour forge_session_id.
    Injecte un message dans la conversation JARVIS.
    Retourne {"session_id": int, "message": str}.
    """
    config = load_config()
    cursor = db.cursor()

    # Récupérer le mission_prompt avec project_id
    cursor.execute("""
        SELECT mp.*, rs.project_id, rs.titre
        FROM mission_prompts mp
        JOIN reflexion_sessions rs ON rs.id = mp.reflexion_session_id
        WHERE mp.id = ?
    """, (mission_prompt_id,))
    mp = cursor.fetchone()

    if not mp:
        raise ValueError(f"Livrable {mission_prompt_id} introuvable")
    if mp["forge_session_id"]:
        # Autoriser un re-lancement si la session précédente est FAILED ou ABORTED
        cursor.execute("SELECT status FROM sessions WHERE id = ?", (mp["forge_session_id"],))
        prev = cursor.fetchone()
        if prev and prev["status"] not in ("FAILED", "ABORTED"):
            raise ValueError("FORGE a déjà été lancé pour ce livrable — un seul pipeline par livrable")
        # Session cassée → réinitialiser pour permettre un nouveau départ
        cursor.execute(
            "UPDATE mission_prompts SET forge_session_id = NULL, consumed_at = NULL WHERE id = ?",
            (mission_prompt_id,)
        )
        db.commit()
        logger.info(f"[FORGE] Livrable {mission_prompt_id} : session précédente {prev['status']} — réinitialisation autorisée")
    if mp["livrable_type"] != "mission_code":
        raise ValueError(
            f"Le type '{mp['livrable_type']}' ne peut pas être exécuté par FORGE. "
            f"Seules les missions 'mission_code' sont exécutables."
        )

    project_id = mp["project_id"]
    livrable_forge = json.loads(mp["livrable_forge"]) if mp["livrable_forge"] else {}

    # Récupérer le chemin du projet
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    if not project or not project["path"]:
        raise ValueError("Le projet n'a pas de chemin local configuré (local_path manquant)")
    project_path = Path(project["path"])

    # Vérification filesystem (niveau 1) — créer le dossier et les fichiers manquants
    project_path.mkdir(parents=True, exist_ok=True)
    missing = _check_files_exist(livrable_forge, project_path)
    if missing:
        for rel in missing:
            full = project_path / rel.lstrip("/\\")
            full.parent.mkdir(parents=True, exist_ok=True)
            full.touch()
            logger.info(f"[FORGE] Fichier créé automatiquement : {full}")

    # Créer la session pipeline
    modele = mp["recommandation_modele"] or None
    session = pipeline_engine.create_session(
        project_id=project_id,
        workflow_type="code_mission",
        initial_input=mp["content"],
        db=db,
        modele_override=modele,
        source_mission_prompt_id=mission_prompt_id
    )
    session_id = session["id"]

    # Mettre à jour forge_session_id + consumed_at
    cursor.execute(
        "UPDATE mission_prompts SET forge_session_id = ?, consumed_at = datetime('now') WHERE id = ?",
        (session_id, mission_prompt_id)
    )
    db.commit()

    # Injecter un message de confirmation dans la conversation JARVIS
    fichiers = ", ".join(livrable_forge.get("fichiers_concernes", [])) or "à déterminer"
    perimetre = livrable_forge.get("perimetre", mp["titre"] or "mission code")
    message_content = (
        f"**JARVIS** — J'ai transmis la mission à FORGE. Le pipeline est lancé ✅\n\n"
        f"**Mission :** {perimetre}\n"
        f"**Fichiers ciblés :** {fichiers}\n\n"
        f"Je te reviens dès que FORGE a besoin de ta validation ou que la mission est terminée."
    )
    if inject_message:
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'JARVIS', ?, datetime('now'))
        """, (
            conversation_id,
            message_content,
            json.dumps({"type": "pipeline", "id": session_id}, ensure_ascii=False)
        ))
        db.commit()

    # Lancer l'exécution en arrière-plan (steps 0 + 1, puis notification WAITING_VALIDATION)
    asyncio.create_task(_run_pipeline_in_background(
        session_id=session_id,
        project_path=str(project_path),
        conversation_id=conversation_id
    ))

    logger.info(f"[FORGE] Pipeline {session_id} démarré depuis livrable {mission_prompt_id}")
    return {"session_id": session_id, "message": message_content}


async def handle_launch_chat(
    conversation_id: int,
    project_id: int | None,
    db,
    config: dict
) -> tuple:
    """
    Lance FORGE depuis le chat quand l'utilisateur écrit "démarre forge" / "passe au code".
    Fige automatiquement la session MENTOR en cours puis démarre le pipeline.
    Retourne (content, agent, instance_ref, suggest_freeze, freeze_reason).
    """
    if not project_id:
        return (
            "[FORGE] Aucun projet actif — sélectionne un projet avant de lancer FORGE.",
            "FORGE", None, False, None
        )

    from backend.services import reflexion_service
    cursor = db.cursor()

    # Chercher d'abord un livrable déjà figé non consommé
    cursor.execute("""
        SELECT mp.id, mp.livrable_forge, rs.titre
        FROM mission_prompts mp
        JOIN reflexion_sessions rs ON rs.id = mp.reflexion_session_id
        WHERE rs.project_id = ? AND mp.forge_session_id IS NULL
          AND mp.consumed_at IS NULL AND mp.livrable_type = 'mission_code'
        ORDER BY mp.created_at DESC LIMIT 1
    """, (project_id,))
    available = cursor.fetchone()

    if available:
        result = await start(available["id"], conversation_id, db, inject_message=False)
        return (
            result["message"], "JARVIS",
            {"type": "pipeline", "id": result["session_id"]},
            False, None
        )

    # Sinon, chercher une session MENTOR OUVERTE à figer
    cursor.execute("""
        SELECT id FROM reflexion_sessions
        WHERE project_id = ? AND statut = 'OUVERTE'
        ORDER BY created_at DESC LIMIT 1
    """, (project_id,))
    row = cursor.fetchone()

    if not row:
        return (
            "[FORGE] Aucune mission MENTOR en cours pour ce projet.\n\n"
            "Travaille d'abord avec **MENTOR** pour définir et valider ta mission, "
            "puis reviens ici pour démarrer FORGE.",
            "FORGE", None, False, None
        )

    session_id = row["id"]

    try:
        await reflexion_service.freeze_session(session_id, db)
    except ValueError as e:
        return (f"[FORGE] Impossible de figer la session MENTOR : {e}", "FORGE", None, False, None)

    livrable = reflexion_service.get_livrable(session_id, db)
    if not livrable:
        return (
            "[FORGE] Mission figée ✅ — le livrable sera disponible dans quelques secondes. "
            "Clique sur **Démarrer FORGE →** dans le banner qui s'affiche.",
            "FORGE", None, False, None
        )

    result = await start(livrable["id"], conversation_id, db, inject_message=False)
    return (
        result["message"], "JARVIS",
        {"type": "pipeline", "id": result["session_id"]},
        False, None
    )


async def handle_status_query(
    project_id: int | None,
    current_instance_ref: dict | None,
    db
) -> tuple:
    """
    Répond aux questions sur l'état de FORGE dans la conversation JARVIS.
    Retourne (content, agent, instance_ref, suggest_freeze, freeze_reason).
    """
    cursor = db.cursor()

    # Si une instance FORGE est en cours → reporter son statut
    if current_instance_ref and current_instance_ref.get("type") == "pipeline":
        pipeline_id = current_instance_ref["id"]
        cursor.execute("SELECT status FROM sessions WHERE id = ?", (pipeline_id,))
        session = cursor.fetchone()
        if session:
            labels = {
                "CREATED": "créé, démarrage en cours",
                "RUNNING": "en cours d'exécution ⚙️",
                "WAITING_VALIDATION": "en attente de ta validation 👀",
                "COMPLETED": "terminé ✅",
                "FAILED": "échoué ❌",
                "ABORTED": "interrompu ⛔",
            }
            label = labels.get(session["status"], session["status"])
            content = (
                f"[FORGE] Pipeline en cours — statut : **{label}**\n\n"
                f"→ [Voir le détail →](mission.html?session={pipeline_id}&from=jarvis)"
            )
            return content, "FORGE", current_instance_ref, False, None

    # Chercher un livrable disponible (session FIGEE, FORGE pas encore lancé)
    if project_id:
        cursor.execute("""
            SELECT mp.id, mp.livrable_forge, rs.titre
            FROM mission_prompts mp
            JOIN reflexion_sessions rs ON rs.id = mp.reflexion_session_id
            WHERE rs.project_id = ? AND mp.forge_session_id IS NULL
              AND mp.consumed_at IS NULL AND mp.livrable_type = 'mission_code'
            ORDER BY mp.created_at DESC LIMIT 1
        """, (project_id,))
        available = cursor.fetchone()
        if available:
            forge_data = json.loads(available["livrable_forge"]) if available["livrable_forge"] else {}
            fichiers = ", ".join(forge_data.get("fichiers_concernes", [])) or "non spécifiés"
            content = (
                f"[FORGE] Un livrable MENTOR est prêt pour ce projet.\n\n"
                f"**Mission :** {available['titre'] or 'Sans titre'}\n"
                f"**Fichiers ciblés :** {fichiers}\n\n"
                f"Pour lancer l'exécution, clique sur **Démarrer FORGE** "
                f"dans la page MENTOR. FORGE ne démarre jamais automatiquement."
            )
            return content, "FORGE", None, False, None

    # Aucun contexte disponible — mode explicatif
    content = (
        "[FORGE] Je suis l'agent d'exécution de missions code.\n\n"
        "Pour m'utiliser :\n"
        "1. Travaille avec **MENTOR** pour définir et figer ta mission\n"
        "2. Valide le livrable dans MENTOR\n"
        "3. Clique sur **Démarrer FORGE**\n\n"
        "FORGE ne démarre jamais automatiquement — toujours sur validation explicite."
    )
    return content, "FORGE", None, False, None


async def verify(session_id: int, db) -> dict:
    """
    Vérification cohérence MENTOR→FORGE post-exécution (niveau 2).
    Retourne {"coherent": bool, "warning": str | None}.
    """
    config = load_config()
    cursor = db.cursor()

    # Récupérer le mission_prompt source via forge_session_id
    cursor.execute("""
        SELECT content FROM mission_prompts WHERE forge_session_id = ?
    """, (session_id,))
    mp_row = cursor.fetchone()
    if not mp_row:
        return {"coherent": True, "warning": None}

    # Récupérer les summaries des steps COMPLETED
    cursor.execute("""
        SELECT step_display_name, summary_fr
        FROM pipeline_steps
        WHERE session_id = ? AND status = 'COMPLETED'
          AND (sub_step_index IS NULL OR sub_step_index = -1)
        ORDER BY step_index ASC
    """, (session_id,))
    steps = cursor.fetchall()

    if not steps:
        return {"coherent": True, "warning": None}

    summaries = "\n".join([
        f"- {s['step_display_name']}: {s['summary_fr'] or '(résumé non disponible)'}"
        for s in steps
    ])
    intention = (mp_row["content"] or "")[:1000]

    prompt = f"""Vérifie la cohérence entre cette intention de mission et ce qui a été exécuté.

Intention :
{intention}

Exécution :
{summaries}

Réponds UNIQUEMENT en JSON valide :
{{"coherent": true, "warning": null}}
Si incohérent :
{{"coherent": false, "warning": "explication de la divergence en 30 mots max"}}"""

    try:
        model_id = get_model_id("routing", config)
        response = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config["api_keys"],
            session_id=session_id,
            step_name="forge_verify",
            model_type="routing",
            db_conn=db,
            module_name="jarvis"
        )
        result = json.loads(response)
        return {
            "coherent": bool(result.get("coherent", True)),
            "warning": result.get("warning")
        }
    except Exception as e:
        logger.warning(f"[FORGE] Vérification échouée ({e})")
        return {"coherent": True, "warning": None}


def _check_files_exist(livrable_forge: dict, project_path: Path) -> list[str]:
    """Retourne les fichiers de livrable_forge absents du filesystem."""
    fichiers = livrable_forge.get("fichiers_concernes", [])
    return [
        f for f in fichiers
        if not (project_path / f.lstrip("/\\")).exists()
    ]


def _inject_jarvis_message(conversation_id: int, content: str, agent: str = "FORGE",
                            instance_ref: dict | None = None) -> None:
    """Insère un message assistant dans une conversation JARVIS (connexion indépendante)."""
    from backend.database import get_connection
    db = get_connection()
    try:
        ref_json = json.dumps(instance_ref, ensure_ascii=False) if instance_ref else None
        db.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, ?, ?, datetime('now'))
        """, (conversation_id, content, agent, ref_json))
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"[FORGE] _inject_jarvis_message échoué: {e}")
    finally:
        db.close()


_CONFIRM_SIGNALS = [
    "oui", "ok", "go", "valide", "validé", "je valide", "c'est bon",
    "parfait", "yes", "ouais", "yep", "continue", "affirmatif", "lancé",
    "lancer", "vas-y", "allez", "bien sûr", "carrément", "approuvé"
]


async def handle_chat_validation(session_id: int, message: str,
                                  conversation_id: int, db) -> tuple:
    """
    Valide ou rejette une étape FORGE WAITING_VALIDATION depuis la conversation JARVIS.
    Permet à l'utilisateur de dire 'oui'/'non' dans le chat au lieu d'aller sur mission.html.
    """
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, step_display_name, summary_fr, output_data
        FROM pipeline_steps
        WHERE session_id = ? AND status = 'WAITING_VALIDATION'
        ORDER BY step_index ASC LIMIT 1
    """, (session_id,))
    step = cursor.fetchone()

    if not step:
        return (
            "**FORGE** — Plus d'étape en attente de validation. "
            "Le pipeline a peut-être déjà avancé — vérifie le statut ci-dessous.",
            "FORGE", {"type": "pipeline", "id": session_id}, False, None
        )

    msg_lower = message.lower().strip()
    is_confirm = msg_lower.startswith("oui") or any(s in msg_lower for s in _CONFIRM_SIGNALS)
    _QUESTION_SIGNALS = ["?", "où est", "ou est", "comment", "qu'est-ce", "qu est", "c'est quoi",
                         "explique", "dis-moi", "montre", "trouve", "chemin", "dossier", "fichier"]
    is_question = not is_confirm and any(s in msg_lower for s in _QUESTION_SIGNALS)

    # Récupérer le chemin du projet
    cursor.execute("""
        SELECT p.path FROM sessions s
        JOIN projects p ON p.id = s.project_id
        WHERE s.id = ?
    """, (session_id,))
    path_row = cursor.fetchone()
    project_path = path_row["path"] if path_row else ""

    if is_confirm:
        from backend.services import pipeline_engine
        result = pipeline_engine.validate_step(
            session_id, step["id"], {"approved": True}, db,
            project_path=project_path if project_path else None
        )
        if result["status"] == "completed":
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=(
                    f"**FORGE** — Pipeline terminé ✅\n\n"
                    f"Les fichiers ont été écrits dans : `{project_path}`\n\n"
                    "Lance un test manuel pour valider le résultat, "
                    "puis dis-moi ce que tu observes."
                )
            )
            return (
                "Validation confirmée ✅ — pipeline terminé. Je t'ai envoyé un récapitulatif.",
                "FORGE", {"type": "pipeline", "id": session_id}, False, None
            )
        elif result["status"] == "validated":
            asyncio.create_task(_continue_pipeline_in_background(
                session_id=session_id,
                start_step=result["next_step"],
                project_path=project_path,
                conversation_id=conversation_id
            ))
            return (
                "**FORGE** — Validation confirmée ✅ — je continue l'exécution.\n\n"
                "Je te reviens dès la prochaine étape ou la fin du pipeline.",
                "FORGE", {"type": "pipeline", "id": session_id}, False, None
            )
        else:
            return (
                f"**FORGE** — Erreur lors de la validation : {result.get('error', 'inconnue')}",
                "FORGE", {"type": "pipeline", "id": session_id}, False, None
            )
    elif is_question:
        step_name = step["step_display_name"] or "cette étape"
        summary = step.get("summary_fr") or "Résumé non disponible."
        path_info = f"\n\nLes fichiers seront écrits dans : `{project_path}`" if project_path else ""
        return (
            f"**FORGE** — *{step_name}* est en attente de ta validation.{path_info}\n\n"
            f"**Résumé de l'étape :** {summary}\n\n"
            "Réponds **oui** pour valider et continuer, ou décris ce que tu veux modifier.",
            "FORGE", {"type": "pipeline", "id": session_id}, False, None
        )
    else:
        step_name = step["step_display_name"] or "cette étape"
        return (
            f"**FORGE** — Compris. Qu'est-ce que tu veux modifier sur *{step_name}* ?\n\n"
            "Décris le changement et je le transmets à FORGE pour un nouveau passage. "
            "Si tu veux finalement valider, réponds **oui**.",
            "FORGE", {"type": "pipeline", "id": session_id}, False, None
        )


async def _continue_pipeline_in_background(session_id: int, start_step: int,
                                            project_path: str, conversation_id: int) -> None:
    """Continue le pipeline depuis start_step après une validation dans le chat.
    Injecte un message de progression après chaque step automatique."""
    from backend.database import get_connection, load_config
    db = get_connection()
    try:
        config = load_config()
        cursor = db.cursor()
        current_step_idx = start_step
        result = await pipeline_engine.execute_step(session_id, current_step_idx, project_path, db, config)

        while result.get("status") == "auto_completed":
            cursor.execute("""
                SELECT step_display_name FROM pipeline_steps
                WHERE session_id = ? AND step_index = ?
                  AND (sub_step_index IS NULL OR sub_step_index = -1)
                LIMIT 1
            """, (session_id, current_step_idx))
            step_row = cursor.fetchone()
            step_name = step_row["step_display_name"] if step_row else f"Étape {current_step_idx + 1}"
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=f"**FORGE** — ✓ *{step_name}* terminé — je continue...",
                instance_ref={"type": "pipeline", "id": session_id}
            )
            current_step_idx = result["next_step"]
            result = await pipeline_engine.execute_step(session_id, current_step_idx, project_path, db, config)

        if result.get("status") == "waiting_validation":
            cursor.execute("""
                SELECT step_display_name, summary_fr FROM pipeline_steps
                WHERE session_id = ? AND status = 'WAITING_VALIDATION'
                ORDER BY step_index ASC LIMIT 1
            """, (session_id,))
            waiting_step = cursor.fetchone()
            step_name = waiting_step["step_display_name"] if waiting_step else "prochaine étape"
            summary = (waiting_step["summary_fr"] + "\n\n") if waiting_step and waiting_step["summary_fr"] else ""
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=(
                    f"**FORGE** — J'ai besoin de ta validation pour : *{step_name}*\n\n"
                    f"{summary}"
                    "Réponds **oui** pour valider et continuer, ou décris ce que tu veux modifier."
                ),
                instance_ref={"type": "pipeline", "id": session_id}
            )
        elif result.get("status") == "completed":
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=(
                    f"**FORGE** — Mission accomplie ✅\n\n"
                    f"Les fichiers sont écrits dans : `{project_path}`\n\n"
                    "Lance un test manuel pour valider, puis dis-moi ce que tu observes."
                )
            )
        elif result.get("status") == "failed":
            error_msg = result.get("error", "erreur inconnue")
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=(
                    f"**FORGE** — Le pipeline a rencontré une erreur : *{error_msg}*\n\n"
                    "Tu peux me décrire ce qui s'est passé — on ajuste la mission avant de retenter."
                )
            )
    except Exception as e:
        logger.error(f"[FORGE] _continue_pipeline_in_background échoué (session={session_id}): {e}")
        try:
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=f"**FORGE** — Erreur inattendue pendant l'exécution : {e}"
            )
        except Exception:
            pass
    finally:
        db.close()


async def _run_pipeline_in_background(session_id: int, project_path: str, conversation_id: int) -> None:
    """
    Exécute les steps du pipeline jusqu'au premier WAITING_VALIDATION,
    puis injecte un message dans la conversation JARVIS pour demander la validation.
    Injecte un message de progression après chaque step automatique.
    S'exécute en arrière-plan via asyncio.create_task.
    """
    from backend.database import get_connection, load_config
    db = get_connection()
    try:
        config = load_config()
        cursor = db.cursor()
        current_step_idx = 0
        result = await pipeline_engine.execute_step(session_id, current_step_idx, project_path, db, config)

        while result.get("status") == "auto_completed":
            cursor.execute("""
                SELECT step_display_name FROM pipeline_steps
                WHERE session_id = ? AND step_index = ?
                  AND (sub_step_index IS NULL OR sub_step_index = -1)
                LIMIT 1
            """, (session_id, current_step_idx))
            step_row = cursor.fetchone()
            step_name = step_row["step_display_name"] if step_row else f"Étape {current_step_idx + 1}"
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=f"**FORGE** — ✓ *{step_name}* terminé — je continue...",
                instance_ref={"type": "pipeline", "id": session_id}
            )
            current_step_idx = result["next_step"]
            result = await pipeline_engine.execute_step(session_id, current_step_idx, project_path, db, config)

        if result.get("status") == "waiting_validation":
            cursor.execute("""
                SELECT step_display_name, summary_fr FROM pipeline_steps
                WHERE session_id = ? AND status = 'WAITING_VALIDATION'
                ORDER BY step_index ASC LIMIT 1
            """, (session_id,))
            _ws = cursor.fetchone()
            step_name = _ws["step_display_name"] if _ws else "Code généré"
            summary = (_ws["summary_fr"] + "\n\n") if _ws and _ws["summary_fr"] else ""
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=(
                    f"**FORGE** — J'ai terminé l'étape *{step_name}* et j'attends ta validation.\n\n"
                    f"{summary}"
                    "Réponds **oui** pour valider et continuer, ou décris ce que tu veux modifier."
                ),
                instance_ref={"type": "pipeline", "id": session_id}
            )
            logger.info(f"[FORGE] Pipeline {session_id} en attente de validation — message FORGE injecté conv {conversation_id}")

        elif result.get("status") == "completed":
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=(
                    f"**FORGE** — Mission accomplie ✅\n\n"
                    f"Les fichiers sont écrits dans : `{project_path}`\n\n"
                    "Lance un test manuel pour valider le résultat. "
                    "Dis-moi ce que tu observes — on ajuste si besoin ou on passe à la prochaine mission."
                ),
                instance_ref={"type": "pipeline", "id": session_id}
            )

        elif result.get("status") == "failed":
            error_msg = result.get('error', 'erreur inconnue')
            _inject_jarvis_message(
                conversation_id=conversation_id,
                content=(
                    f"**FORGE** — Le pipeline a rencontré une erreur : *{error_msg}*\n\n"
                    "Décris-moi ce qui s'est passé — on ajuste la mission et on relance."
                ),
                instance_ref={"type": "pipeline", "id": session_id}
            )
            logger.error(f"[FORGE] Pipeline {session_id} échoué: {error_msg}")

    except Exception as e:
        logger.error(f"[FORGE] Erreur pipeline background session {session_id}: {e}")
        _inject_jarvis_message(
            conversation_id=conversation_id,
            content=f"**FORGE** — Erreur inattendue pendant l'exécution : {e}",
            instance_ref={"type": "pipeline", "id": session_id}
        )
    finally:
        db.close()
