# backend/services/jarvis_service.py

import json
import logging
from datetime import datetime

from backend.services.model_router import call_model, get_model_id

logger = logging.getLogger("jarvis")

# ─── SSE helper ──────────────────────────────────────────────────────────────

def sse(event_type: str, data: dict | str) -> str:
    """Formate un événement SSE."""
    if isinstance(data, str):
        data = {"content": data}
    return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"


# ─── Intent classification ────────────────────────────────────────────────────

INTENT_SYSTEM = """Tu es le routeur de JARVIS. Analyse le message et réponds UNIQUEMENT par JSON :
{"intent": "<code>", "summary": "<résumé court en français>"}

Codes :
- "chat"       : question générale, discussion
- "code"       : tâche de développement, pipeline code
- "atelier"    : pipeline Atelier (prospection, démo, proposition)
- "reflexion"  : analyse approfondie, session de réflexion
- "sentinelle" : portefeuille financier, Sentinelle
- "status"     : demande statut des agents en cours

JSON uniquement, sans markdown."""


async def classify_intent(message: str, config: dict) -> dict:
    model_id = get_model_id("routing", config)
    if not model_id:
        return {"intent": "chat", "summary": message[:80]}

    try:
        raw = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": f"{INTENT_SYSTEM}\n\nMessage :\n{message}"}],
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


def _serialize_message(row: dict) -> dict:
    if row.get("metadata") and isinstance(row["metadata"], str):
        try:
            row["metadata"] = json.loads(row["metadata"])
        except Exception:
            row["metadata"] = None
    return row


# ─── Chat reply ───────────────────────────────────────────────────────────────

JARVIS_SYSTEM = """Tu es JARVIS, assistant IA orchestrateur personnel.
Tu peux discuter, analyser, expliquer, et déléguer aux agents spécialisés.
Sois concis, direct, utile. Réponds en français."""


async def generate_chat_reply(
    message: str,
    history: list[dict],
    config: dict,
    db_conn,
) -> str:
    model_id = get_model_id("analysis", config)
    if not model_id:
        return "Aucun modèle configuré. Vérifiez les paramètres."

    messages = [{"role": "system", "content": JARVIS_SYSTEM}]
    for msg in history:
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
        return f"Erreur : {e}"


async def generate_dispatch_reply(
    intent: str,
    summary: str,
    pipeline_session_id: int | None,
    config: dict,
    db_conn,
    extra_context: str = "",
) -> str:
    labels = {
        "code": "Module Code", "atelier": "Module Atelier",
        "reflexion": "Module Réflexion", "sentinelle": "Module Sentinelle",
    }
    label = labels.get(intent, intent)
    ps_info = f" (session #{pipeline_session_id})" if pipeline_session_id else ""
    model_id = get_model_id("routing", config)

    prompt = (
        f"Tu es JARVIS. Tu viens de déléguer au {label}{ps_info} : « {summary} »\n"
        f"{extra_context}\n"
        f"Réponds en 1-2 phrases : confirme la délégation, indique que tu suivras. Concis, en français."
    )

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


# ─── Pipeline status (pipeline + réflexion) ──────────────────────────────────

def get_pipeline_status(pipeline_session_id: int, pipeline_type: str, db_conn) -> dict | None:
    """
    Récupère le statut d'un pipeline — adaptatif selon le type :
    - "code"      → table sessions + pipeline_steps
    - "reflexion" → table reflexion_sessions
    """
    cursor = db_conn.cursor()

    if pipeline_type == "reflexion":
        cursor.execute(
            "SELECT id, statut, livrable_type FROM reflexion_sessions WHERE id = ?",
            (pipeline_session_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "status": _map_reflexion_statut(row["statut"]),
            "workflow_type": row["livrable_type"],
            "reflexion_statut": row["statut"],
            "current_step": None,
        }

    # Pipeline code/atelier
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
           ORDER BY step_index DESC, id DESC LIMIT 1""",
        (pipeline_session_id,)
    )
    step = cursor.fetchone()
    if step:
        result["current_step"] = dict(step)
    return result


def _map_reflexion_statut(statut: str) -> str:
    """Mappe le statut réflexion vers un statut générique Jarvis."""
    mapping = {
        "OUVERTE": "RUNNING",
        "EN_FIGEMENT": "WAITING_VALIDATION",
        "FIGEE": "COMPLETED",
        "ABANDONNEE": "ABORTED",
    }
    return mapping.get(statut, statut)


def get_tracked_pipelines(jarvis_session_id: int, db_conn) -> list[dict]:
    cursor = db_conn.cursor()
    cursor.execute(
        """SELECT DISTINCT pipeline_session_id, agent_type
           FROM jarvis_messages
           WHERE session_id = ? AND pipeline_session_id IS NOT NULL""",
        (jarvis_session_id,)
    )
    return [dict(r) for r in cursor.fetchall()]


def format_status_content(agent_type: str, status: dict) -> str:
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


# ─── Polling agent updates ────────────────────────────────────────────────────

def _get_last_meta(jarvis_session_id: int, pipeline_session_id: int, db_conn) -> dict | None:
    cursor = db_conn.cursor()
    cursor.execute(
        """SELECT metadata FROM jarvis_messages
           WHERE session_id = ? AND pipeline_session_id = ? AND message_type IN ('agent_status','validation_request')
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


def _status_changed(last_meta: dict | None, current_status: dict) -> bool:
    if last_meta is None:
        return True
    if last_meta.get("session_status") != current_status.get("status"):
        return True
    step = current_status.get("current_step")
    if step:
        if step.get("id") != last_meta.get("step_id"):
            return True
        if step.get("status") != last_meta.get("step_status"):
            return True
    return False


def check_and_emit_agent_updates(jarvis_session_id: int, db_conn) -> list[dict]:
    """Vérifie tous les pipelines suivis et émet des messages si le statut a changé."""
    tracked = get_tracked_pipelines(jarvis_session_id, db_conn)
    new_messages = []

    for item in tracked:
        ps_id = item["pipeline_session_id"]
        agent_type = item.get("agent_type") or "unknown"
        pipeline_type = agent_type  # "code", "reflexion", etc.

        status = get_pipeline_status(ps_id, pipeline_type, db_conn)
        if not status:
            continue

        terminal = status["status"] in ("COMPLETED", "FAILED", "ABORTED")
        last_meta = _get_last_meta(jarvis_session_id, ps_id, db_conn)

        if terminal and last_meta and last_meta.get("session_status") == status["status"]:
            continue
        if not _status_changed(last_meta, status):
            continue

        step = status.get("current_step")
        step_id = step.get("id") if step else None
        step_status = step.get("status") if step else None
        needs_validation = step_status == "WAITING_VALIDATION"

        msg_type = "validation_request" if needs_validation else "agent_status"
        content = format_status_content(agent_type, status)

        if needs_validation and step:
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
        cursor.execute("SELECT * FROM jarvis_messages WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        if row:
            new_messages.append(_serialize_message(dict(row)))

    return new_messages
