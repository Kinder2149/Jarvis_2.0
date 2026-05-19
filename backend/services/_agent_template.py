"""
TEMPLATE AGENT JARVIS — modèle de référence pour tout nouvel agent.

Règles du contrat :
  1. Signature handle() fixe : (conversation_id, message, current_instance_ref, db, config) → tuple
  2. Retour toujours un 5-tuple : (content, agent_used, instance_ref, suggest_freeze, freeze_reason)
  3. agent_used = NOM_AGENT (ex: "MENTOR") pour TOUS les messages de cet agent,
     y compris les demandes de validation et de cadrage.
  4. Les messages injectés en background utilisent aussi agent_used = NOM_AGENT.
  5. suggest_freeze = réservé à MENTOR uniquement.
  6. instance_ref = dict {"type": "...", "id": ...} si un travail de fond est en cours, sinon None.

Cycle de validation obligatoire :
  - Quand l'agent a besoin d'une validation ou d'un cadrage :
    → Terminer le message par une question explicite oui/non ou une demande précise
    → Stocker l'état dans instance_ref pour reprendre au prochain tour
    → NE PAS déléguer la question à un bandeau UI externe

Cycle de travail en arrière-plan :
  - Lancer via asyncio.create_task()
  - Injecter les messages de progression/résultat via _inject_message()
  - Utiliser une connexion db indépendante (get_connection()) dans la tâche background
"""

import asyncio
import json
import logging
from backend.database import get_connection
from backend.services.model_router import get_model_id, call_model

logger = logging.getLogger("jarvis")

# Nom de l'agent — à remplacer dans chaque implémentation
AGENT_NAME = "MON_AGENT"

# Signaux de confirmation positifs
_CONFIRM_SIGNALS = [
    "oui", "ok", "go", "vas-y", "yes", "valide", "validé",
    "parfait", "c'est bon", "yep", "ouais", "bien sûr", "affirmatif",
]

# Signaux d'annulation
_ABORT_SIGNALS = [
    "non", "annule", "annuler", "stop", "laisse tomber",
    "oublie", "abort", "erreur", "recommence",
]


def _is_confirm(message: str) -> bool:
    msg = message.lower().strip()
    return msg.startswith("oui") or any(s in msg for s in _CONFIRM_SIGNALS)


def _is_abort(message: str) -> bool:
    msg = message.lower().strip()
    return msg.startswith("non") or any(s in msg for s in _ABORT_SIGNALS)


# ─── Point d'entrée principal ─────────────────────────────────────────────────

async def handle(
    conversation_id: int,
    message: str,
    current_instance_ref: dict | None,
    db,
    config: dict
) -> tuple:
    """
    Dispatcher principal.
    Inspecte current_instance_ref pour savoir dans quel état on est,
    puis route vers la bonne étape de travail.
    """
    state_type = current_instance_ref.get("type") if current_instance_ref else None

    # État : en attente de validation utilisateur
    if state_type == f"{AGENT_NAME.lower()}_confirm":
        return await _handle_confirmation(conversation_id, message, current_instance_ref, db, config)

    # État : travail de fond en cours
    if state_type == f"{AGENT_NAME.lower()}_running":
        return _handle_status_query(current_instance_ref, db)

    # État : annulation en cours de flow
    if _is_abort(message) and current_instance_ref:
        return (
            "D'accord, j'annule. Comment puis-je t'aider ?",
            AGENT_NAME, None, False, None
        )

    # Point d'entrée : nouveau travail
    return await _handle_new_task(conversation_id, message, db, config)


# ─── Nouveau travail ──────────────────────────────────────────────────────────

async def _handle_new_task(
    conversation_id: int,
    message: str,
    db,
    config: dict
) -> tuple:
    """
    Initialise le travail. Pose une question de cadrage si nécessaire,
    sinon présente le résultat et demande une confirmation.
    """
    # Exemple : manque d'information → cadrage
    if not _has_required_info(message):
        return (
            "[MON_AGENT] Pour commencer, j'ai besoin de savoir : **[question de cadrage]** ?",
            AGENT_NAME, None, False, None
        )

    # Exemple : traitement synchrone rapide
    result = await _do_quick_work(message, config, db)
    state = {"type": f"{AGENT_NAME.lower()}_confirm", "result": result}

    # Toujours terminer par une question explicite oui/non
    content = (
        f"[MON_AGENT] Voici ce que j'ai préparé :\n\n{result}\n\n"
        f"**Tu valides ? Réponds oui pour continuer, non pour annuler.**"
    )
    return content, AGENT_NAME, state, False, None


# ─── Confirmation ─────────────────────────────────────────────────────────────

async def _handle_confirmation(
    conversation_id: int,
    message: str,
    state: dict,
    db,
    config: dict
) -> tuple:
    """
    Traite la réponse oui/non de l'utilisateur après une demande de validation.
    """
    if _is_confirm(message):
        # Lancer le travail de fond
        asyncio.create_task(
            _run_background_task(conversation_id, state, config)
        )
        instance_ref = {"type": f"{AGENT_NAME.lower()}_running", "state": state}
        return (
            "[MON_AGENT] C'est parti ! Je te notifie dès que c'est terminé.",
            AGENT_NAME, instance_ref, False, None
        )

    elif _is_abort(message):
        return (
            "[MON_AGENT] D'accord, annulé.",
            AGENT_NAME, None, False, None
        )

    else:
        # Signal ambigu → re-présenter le choix sans perdre l'état
        return (
            "[MON_AGENT] Je n'ai pas compris. Réponds **oui** pour valider ou **non** pour annuler.",
            AGENT_NAME, state, False, None
        )


# ─── Requête de statut ────────────────────────────────────────────────────────

def _handle_status_query(current_instance_ref: dict, db) -> tuple:
    """
    Répond à une question sur l'état du travail en cours.
    """
    return (
        "[MON_AGENT] Le travail est toujours en cours. Je te notifie dès que c'est prêt.",
        AGENT_NAME, current_instance_ref, False, None
    )


# ─── Travail de fond ──────────────────────────────────────────────────────────

async def _run_background_task(
    conversation_id: int,
    state: dict,
    config: dict
) -> None:
    """
    Tâche asyncio exécutée en fond.
    Règles :
      - Utiliser get_connection() (connexion indépendante)
      - Toujours appeler _inject_message() pour notifier l'utilisateur
      - Toujours fermer la connexion dans finally
    """
    db = get_connection()
    try:
        # ... travail ici ...
        result = "résultat du travail"

        _inject_message(
            conversation_id=conversation_id,
            content=(
                f"[MON_AGENT] Travail terminé ✅\n\n{result}\n\n"
                f"Dis-moi ce que tu observes — on ajuste si besoin."
            ),
            db=db
        )

    except Exception as e:
        logger.error(f"[{AGENT_NAME}] Erreur background (conv={conversation_id}): {e}")
        _inject_message(
            conversation_id=conversation_id,
            content=f"[MON_AGENT] Erreur inattendue : {e}",
            db=db
        )
    finally:
        db.close()


# ─── Injection de message (background) ───────────────────────────────────────

def _inject_message(
    conversation_id: int,
    content: str,
    db,
    instance_ref: dict | None = None
) -> None:
    """
    Insère un message assistant dans la conversation depuis une tâche de fond.
    Utilise agent_used = AGENT_NAME — jamais "JARVIS".
    """
    try:
        ref_json = json.dumps(instance_ref, ensure_ascii=False) if instance_ref else None
        db.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, ?, ?, datetime('now'))
        """, (conversation_id, content, AGENT_NAME, ref_json))
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"[{AGENT_NAME}] _inject_message échoué: {e}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _has_required_info(message: str) -> bool:
    """Vérifie que le message contient les infos nécessaires pour commencer."""
    return True  # À adapter selon l'agent


async def _do_quick_work(message: str, config: dict, db) -> str:
    """Exemple de travail synchrone rapide via LLM."""
    model_id = get_model_id("analysis", config)
    return await call_model(
        model_id=model_id,
        messages=[{"role": "user", "content": message}],
        api_keys=config["api_keys"],
        session_id=None,
        step_name=f"{AGENT_NAME.lower()}_work",
        model_type="analysis",
        db_conn=db,
        module_name=AGENT_NAME.lower()
    )
