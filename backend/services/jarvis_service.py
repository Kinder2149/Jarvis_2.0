# backend/services/jarvis_service.py

import json
import logging
from datetime import datetime

from backend.services.model_router import call_model, get_model_id

logger = logging.getLogger("jarvis")

# ─── Intent classification ────────────────────────────────────────────────────

INTENT_SYSTEM = """Tu es le routeur de JARVIS, un assistant IA orchestrateur.
Analyse le message utilisateur et réponds UNIQUEMENT par un JSON :
{"intent": "<code>", "summary": "<résumé court en français>"}

Codes d'intent disponibles :
- "chat"       : question générale, discussion, aide ponctuelle
- "code"       : créer un pipeline de développement code / mission technique
- "atelier"    : pipeline Atelier (prospection, démo client, proposition commerciale)
- "reflexion"  : démarrer une session de réflexion / analyse approfondie
- "sentinelle" : question ou action relative au portefeuille financier / Sentinelle
- "status"     : demande de statut sur les agents/pipelines en cours

Réponds uniquement avec le JSON, sans markdown, sans explication."""


async def classify_intent(message: str, config: dict, db_conn) -> dict:
    """Classifie l'intent du message utilisateur via le modèle de routing."""
    model_id = get_model_id("routing", config)
    if not model_id:
        return {"intent": "chat", "summary": message[:80]}

    messages = [
        {"role": "user", "content": f"{INTENT_SYSTEM}\n\nMessage utilisateur :\n{message}"}
    ]

    try:
        raw = await call_model(
            model_id=model_id,
            messages=messages,
            api_keys=config.get("api_keys", {}),
            session_id=0,
            step_name="jarvis_intent",
            model_type="routing",
            db_conn=None,
            module_name="jarvis"
        )
        data = json.loads(raw)
        intent = data.get("intent", "chat")
        if intent not in ("chat", "code", "atelier", "reflexion", "sentinelle", "status"):
            intent = "chat"
        return {"intent": intent, "summary": data.get("summary", message[:80])}
    except Exception as e:
        logger.warning(f"[JARVIS] classify_intent error : {e}")
        return {"intent": "chat", "summary": message[:80]}


# ─── Message helpers ──────────────────────────────────────────────────────────

def add_message(
    session_id: int,
    role: str,
    content: str,
    db_conn,
    message_type: str = "text",
    agent_type: str | None = None,
    pipeline_session_id: int | None = None,
    pipeline_step_id: int | None = None,
    metadata: dict | None = None,
) -> int:
    cursor = db_conn.cursor()
    cursor.execute(
        """INSERT INTO jarvis_messages
           (session_id, role, content, message_type, agent_type,
            pipeline_session_id, pipeline_step_id, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id, role, content, message_type, agent_type,
            pipeline_session_id, pipeline_step_id,
            json.dumps(metadata) if metadata else None,
        )
    )
    db_conn.execute(
        "UPDATE jarvis_sessions SET updated_at=? WHERE id=?",
        (datetime.utcnow().isoformat(), session_id)
    )
    db_conn.commit()
    return cursor.lastrowid


# ─── Jarvis response generator ────────────────────────────────────────────────

JARVIS_SYSTEM = """Tu es JARVIS, un assistant IA orchestrateur personnel.
Tu peux discuter librement, analyser, expliquer, et quand l'utilisateur a besoin d'un agent
spécialisé (Code, Atelier, Réflexion, Sentinelle), tu délègues et tu communiques le statut.
Sois concis, direct, utile. Réponds en français."""


async def generate_chat_reply(
    message: str,
    history: list[dict],
    config: dict,
    db_conn,
) -> str:
    """Génère une réponse Jarvis pour un intent 'chat'."""
    model_id = get_model_id("analysis", config)
    if not model_id:
        return "Je n'ai pas de modèle configuré. Vérifiez les paramètres."

    messages = [{"role": "system", "content": JARVIS_SYSTEM}]
    for msg in history[-20:]:
        if msg["role"] in ("user", "jarvis"):
            messages.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"]
            })
    messages.append({"role": "user", "content": message})

    try:
        return await call_model(
            model_id=model_id,
            messages=messages,
            api_keys=config.get("api_keys", {}),
            session_id=0,
            step_name="jarvis_chat",
            model_type="analysis",
            db_conn=db_conn,
            module_name="jarvis"
        )
    except Exception as e:
        logger.error(f"[JARVIS] generate_chat_reply error : {e}")
        return f"Erreur lors de la génération : {e}"


async def generate_dispatch_reply(
    intent: str,
    summary: str,
    pipeline_session_id: int | None,
    config: dict,
    db_conn,
    extra_context: str = "",
) -> str:
    """Génère un message de confirmation après dispatch d'un agent."""
    agent_labels = {
        "code": "Module Code",
        "atelier": "Module Atelier",
        "reflexion": "Module Réflexion",
        "sentinelle": "Module Sentinelle",
    }
    label = agent_labels.get(intent, intent)
    ps_info = f" (session #{pipeline_session_id})" if pipeline_session_id else ""
    model_id = get_model_id("routing", config)

    prompt = f"""Tu es JARVIS. Tu viens de déléguer la tâche suivante au {label}{ps_info} :
« {summary} »
{extra_context}
Réponds en 1-2 phrases : confirme que tu as transmis, dis que tu suivras l'avancement.
Sois concis, direct, en français."""

    try:
        return await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config.get("api_keys", {}),
            session_id=0,
            step_name="jarvis_dispatch_reply",
            model_type="routing",
            db_conn=None,
            module_name="jarvis"
        )
    except Exception:
        return f"J'ai transmis votre demande au {label}{ps_info}. Je vous tiens informé de l'avancement."


# ─── Agent status polling ─────────────────────────────────────────────────────

def get_tracked_pipelines(jarvis_session_id: int, db_conn) -> list[dict]:
    """Retourne tous les pipeline_session_id suivis dans cette session Jarvis."""
    cursor = db_conn.cursor()
    cursor.execute(
        """SELECT DISTINCT pipeline_session_id, agent_type
           FROM jarvis_messages
           WHERE session_id = ? AND pipeline_session_id IS NOT NULL""",
        (jarvis_session_id,)
    )
    return [dict(r) for r in cursor.fetchall()]


def get_pipeline_status(pipeline_session_id: int, db_conn) -> dict | None:
    """Récupère le statut courant d'une session pipeline."""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT id, status, workflow_type, current_step_index FROM sessions WHERE id = ?",
        (pipeline_session_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    result = dict(row)

    cursor.execute(
        """SELECT id, step_index, step_display_name, status, output_data, error_message
           FROM pipeline_steps
           WHERE session_id = ? AND status NOT IN ('PENDING')
           ORDER BY step_index DESC, id DESC
           LIMIT 1""",
        (pipeline_session_id,)
    )
    step = cursor.fetchone()
    if step:
        result["current_step"] = dict(step)
    return result


def get_last_agent_message_metadata(
    jarvis_session_id: int, pipeline_session_id: int, db_conn
) -> dict | None:
    """Récupère les métadonnées du dernier message agent_status pour ce pipeline."""
    cursor = db_conn.cursor()
    cursor.execute(
        """SELECT metadata FROM jarvis_messages
           WHERE session_id = ? AND pipeline_session_id = ? AND message_type = 'agent_status'
           ORDER BY id DESC LIMIT 1""",
        (jarvis_session_id, pipeline_session_id)
    )
    row = cursor.fetchone()
    if not row or not row["metadata"]:
        return None
    try:
        return json.loads(row["metadata"])
    except Exception:
        return None


def should_emit_status_update(
    last_meta: dict | None, current_status: dict
) -> bool:
    """Détermine si un nouveau message de statut doit être émis."""
    if last_meta is None:
        return True
    if last_meta.get("session_status") != current_status.get("status"):
        return True
    cur_step = current_status.get("current_step")
    if cur_step:
        last_step_id = last_meta.get("step_id")
        last_step_status = last_meta.get("step_status")
        if cur_step.get("id") != last_step_id or cur_step.get("status") != last_step_status:
            return True
    return False


def format_status_content(agent_type: str, status: dict) -> str:
    """Formate le contenu texte d'un message agent_status."""
    icons = {
        "code": "⚙️", "atelier": "🏭", "reflexion": "🧠",
        "sentinelle": "🛡️", "chat": "💬"
    }
    icon = icons.get(agent_type, "🤖")
    session_status = status.get("status", "?")
    wf = status.get("workflow_type", "")
    ps_id = status.get("id")

    step = status.get("current_step")
    if step:
        step_label = step.get("step_display_name") or f"étape {step.get('step_index', '?')}"
        step_status = step.get("status", "?")
        return (
            f"{icon} **{wf}** #{ps_id} — {session_status}\n"
            f"Étape : {step_label} → {step_status}"
        )
    return f"{icon} **{wf}** #{ps_id} — {session_status}"


def check_and_emit_agent_updates(jarvis_session_id: int, db_conn) -> list[dict]:
    """
    Vérifie l'état de tous les pipelines suivis et insère des messages de statut
    si quelque chose a changé. Retourne la liste des nouveaux messages créés.
    """
    tracked = get_tracked_pipelines(jarvis_session_id, db_conn)
    new_messages = []

    for tracked_item in tracked:
        ps_id = tracked_item["pipeline_session_id"]
        agent_type = tracked_item["agent_type"] or "unknown"

        status = get_pipeline_status(ps_id, db_conn)
        if not status:
            continue

        # Ne rien émettre pour des sessions déjà terminées et déjà signalées
        terminal = status["status"] in ("COMPLETED", "FAILED", "ABORTED")
        last_meta = get_last_agent_message_metadata(jarvis_session_id, ps_id, db_conn)

        if terminal and last_meta and last_meta.get("session_status") == status["status"]:
            continue

        if not should_emit_status_update(last_meta, status):
            continue

        step = status.get("current_step")
        step_id = step.get("id") if step else None
        step_status = step.get("status") if step else None
        needs_validation = step_status == "WAITING_VALIDATION"

        msg_type = "validation_request" if needs_validation else "agent_status"
        content = format_status_content(agent_type, status)

        if needs_validation:
            step_label = step.get("step_display_name", "cette étape")
            content += f"\n\n⏸️ **Validation requise** pour : {step_label}"
            if step.get("output_data"):
                try:
                    out = json.loads(step["output_data"])
                    preview = out.get("content") or out.get("result") or str(out)
                    content += f"\n\n---\n{preview[:1500]}"
                except Exception:
                    content += f"\n\n---\n{step['output_data'][:1500]}"

        metadata = {
            "session_status": status["status"],
            "step_id": step_id,
            "step_status": step_status,
            "step_index": step.get("step_index") if step else None,
        }

        msg_id = add_message(
            session_id=jarvis_session_id,
            role="jarvis",
            content=content,
            db_conn=db_conn,
            message_type=msg_type,
            agent_type=agent_type,
            pipeline_session_id=ps_id,
            pipeline_step_id=step_id,
            metadata=metadata,
        )

        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT * FROM jarvis_messages WHERE id = ?", (msg_id,)
        )
        row = cursor.fetchone()
        if row:
            new_messages.append(_serialize_message(dict(row)))

    return new_messages


def _serialize_message(row: dict) -> dict:
    if row.get("metadata") and isinstance(row["metadata"], str):
        try:
            row["metadata"] = json.loads(row["metadata"])
        except Exception:
            row["metadata"] = None
    return row
