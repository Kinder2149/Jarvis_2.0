import json
import logging
from backend.schemas.reflexion import LivrableType, ReflexionStatut
from backend.services import reflexion_service
from backend.services.model_router import get_model_id, call_model

logger = logging.getLogger("jarvis")

_FORGE_CONFIRM_SIGNALS = [
    "oui", "ok", "go", "vas-y", "yes", "valide", "validé",
    "je valide", "c'est bon", "parfait", "yep", "ouais",
    "bien sûr", "affirmatif", "carrément", "lancé", "lancer",
    "démarre", "demarre", "allez",
]

def _is_forge_validation(message: str) -> bool:
    """Détecte si l'utilisateur répond 'oui' à la question de démarrage FORGE."""
    msg = message.lower().strip()
    return msg.startswith("oui") or any(s == msg or msg.startswith(s + " ") for s in _FORGE_CONFIRM_SIGNALS)


async def handle(
    conversation_id: int,
    project_id: int | None,
    message: str,
    current_instance_ref: dict | None,
    db,
    config: dict
) -> tuple:
    """
    Façade MENTOR. Retourne (content, agent, instance_ref, suggest_freeze, freeze_reason).
    Trouve ou crée une session réflexion OUVERTE, délègue à reflexion_service.
    """
    cursor = db.cursor()

    # Détection : l'utilisateur répond "oui" à la question de démarrage FORGE
    # (current_instance_ref de type "reflexion" + instance précédente avait suggest_freeze)
    if current_instance_ref and current_instance_ref.get("type") == "reflexion":
        if current_instance_ref.get("awaiting_forge_confirm") and _is_forge_validation(message):
            from backend.services import forge_handler
            return await forge_handler.handle_launch_chat(
                conversation_id=conversation_id,
                project_id=project_id,
                db=db,
                config=config
            )

    # Pas de projet → prendre le premier projet code disponible
    fallback_note = None
    if not project_id:
        cursor.execute(
            "SELECT id, path, name FROM projects WHERE module_type IN ('code', 'dossier') ORDER BY id LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            project_id = row["id"]
            path_hint = f" — dossier : `{row['path']}`" if row["path"] else ""
            fallback_note = (
                f"*(Pas de projet sélectionné — je travaille sur le projet **#{project_id} {row['name'] or ''}**{path_hint}. "
                f"Si ce n'est pas le bon, sélectionne ton projet dans le panneau gauche avant de continuer.)*\n\n"
            )
            logger.info(f"[MENTOR] Pas de project_id fourni, fallback sur projet {project_id}")
        else:
            return (
                "[MENTOR] Aucun projet disponible. "
                "Crée d'abord un projet dans JARVIS pour que je puisse travailler.",
                "MENTOR", None, False, None
            )
    
    # Trouver ou créer la session réflexion
    reflexion_session_id = _resolve_session(
        project_id, current_instance_ref, db, cursor
    )
    
    # Envoyer le message à MENTOR
    try:
        messages = await reflexion_service.send_user_message(
            reflexion_session_id, message, db
        )
    except ValueError as e:
        # Session plus ouverte (FIGEE, ABANDONNEE) → en créer une nouvelle
        logger.warning(f"[MENTOR] Session {reflexion_session_id} inaccessible ({e}), nouvelle session")
        reflexion_session_id = reflexion_service.create_session(
            project_id, LivrableType.MISSION_CODE, db
        )
        messages = await reflexion_service.send_user_message(
            reflexion_session_id, message, db
        )
    
    # Récupérer la dernière réponse assistant
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    content = assistant_msgs[-1]["content"] if assistant_msgs else "[MENTOR] Aucune réponse."
    if fallback_note:
        content = fallback_note + content
    
    # [MISSION_PRETE] dans la réponse → forcer suggest_freeze immédiatement
    if "[MISSION_PRETE]" in content or "[mission_prete]" in content.lower():
        suggest_freeze = True
        freeze_reason = "Mission de cadrage complète — cliquez sur Démarrer FORGE pour exécuter"
    else:
        suggest_freeze, freeze_reason = await _check_suggest_freeze(
            reflexion_session_id, messages, config, db
        )

    instance_ref = {"type": "reflexion", "id": reflexion_session_id}

    # Si la mission est prête : ajouter une question conversationnelle oui/non
    # et marquer l'état pour traiter la réponse au prochain tour
    if suggest_freeze:
        content = content.rstrip() + (
            "\n\n---\n"
            "**Mission prête.** Réponds **oui** pour passer à FORGE et démarrer l'exécution, "
            "ou continue à affiner si tu veux ajuster quelque chose."
        )
        instance_ref = {"type": "reflexion", "id": reflexion_session_id, "awaiting_forge_confirm": True}

    return content, "MENTOR", instance_ref, suggest_freeze, freeze_reason


def _resolve_session(
    project_id: int,
    current_instance_ref: dict | None,
    db,
    cursor
) -> int:
    """Retourne l'ID de session à utiliser (existante ou nouvelle).

    Règle d'isolation : une conversation JARVIS = une session MENTOR.
    On ne réutilise jamais une session d'une autre conversation — sinon
    MENTOR voit l'historique d'anciennes conversations et détecte de
    fausses boucles.
    """
    # 1. Instance connue depuis CETTE conversation → continuer cette session
    if current_instance_ref and current_instance_ref.get("type") == "reflexion":
        session_id = current_instance_ref["id"]
        session = reflexion_service.get_session(session_id, db)
        if session and session["statut"] == ReflexionStatut.OUVERTE.value:
            return session_id
        # Session fermée (figée/abandonnée) → en créer une nouvelle pour cette conversation
        return reflexion_service.create_session(
            project_id, LivrableType.MISSION_CODE, db
        )

    # 2. Pas d'instance_ref = premier message MENTOR dans cette conversation
    #    → toujours créer une session fraîche (pas de réutilisation cross-conversation)
    return reflexion_service.create_session(
        project_id, LivrableType.MISSION_CODE, db
    )


async def _check_suggest_freeze(
    session_id: int,
    messages: list,
    config: dict,
    db
) -> tuple[bool, str | None]:
    """
    Propose le figement si la réflexion est mature (>= 3 réponses MENTOR).
    Appel Gemini Flash (routing). Retourne (suggest_freeze, reason).
    """
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    if len(assistant_msgs) < 3:
        return False, None
    
    # Résumé des 8 derniers échanges
    convo_summary = "\n".join([
        f"{m['role'].upper()}: {m['content'][:300]}"
        for m in messages[-8:]
        if m["role"] in ("user", "assistant")
    ])
    
    prompt = f"""Analyse cette session de réflexion et dis si elle est mature pour être figée.

Une réflexion est mature si :
1. L'objectif de la mission est clairement défini
2. Les fichiers à modifier sont identifiés
3. Les critères de succès sont formulés

Conversation :
{convo_summary}

Réponds UNIQUEMENT en JSON valide, aucun texte autour :
{{"suggest_freeze": true, "reason": "explication en 20 mots max"}}"""
    
    try:
        model_id = get_model_id("routing", config)
        response = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config["api_keys"],
            session_id=session_id,
            step_name="mentor_suggest_freeze",
            model_type="routing",
            db_conn=db,
            module_name="jarvis"
        )
        result = json.loads(response)
        return bool(result.get("suggest_freeze", False)), result.get("reason")
    except Exception as e:
        logger.warning(f"[MENTOR] suggest_freeze échoué ({e})")
        return False, None
