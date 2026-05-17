# backend/routers/jarvis.py

import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.database import get_connection, load_config
from backend.services import jarvis_service as svc

logger = logging.getLogger("jarvis")
router = APIRouter(prefix="/jarvis", tags=["jarvis"])

INTENT_LABELS = {
    "chat": "Chat", "code": "Code", "atelier": "Atelier",
    "reflexion": "Réflexion", "sentinelle": "Sentinelle", "status": "Statut",
}


# ─── Schémas ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str = "Session Jarvis"


class UserMessage(BaseModel):
    content: str
    project_id: int | None = None


class ValidationPayload(BaseModel):
    approved: bool
    feedback: str = ""


# ─── Sessions CRUD ────────────────────────────────────────────────────────────

@router.post("/sessions")
def create_session(data: SessionCreate):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO jarvis_sessions (title) VALUES (?)", (data.title,))
    session_id = cursor.lastrowid
    db.commit()
    cursor.execute("SELECT * FROM jarvis_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    db.close()
    return dict(row)


@router.get("/sessions")
def list_sessions():
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM jarvis_sessions ORDER BY updated_at DESC LIMIT 30")
    rows = cursor.fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/sessions/{session_id}")
def get_session(session_id: int):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM jarvis_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        db.close()
        raise HTTPException(404, "Session introuvable")
    cursor.execute(
        "SELECT * FROM jarvis_messages WHERE session_id = ? ORDER BY id",
        (session_id,)
    )
    messages = [svc._serialize_message(dict(r)) for r in cursor.fetchall()]
    db.close()
    result = dict(row)
    result["messages"] = messages
    return result


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int):
    db = get_connection()
    db.execute("DELETE FROM jarvis_sessions WHERE id = ?", (session_id,))
    db.commit()
    db.close()
    return {"ok": True}


# ─── Background pipeline runner ───────────────────────────────────────────────

async def _run_pipeline_bg(pipeline_session_id: int, project_path: str, config: dict):
    """Exécute un pipeline Code en tâche de fond (connexion DB dédiée)."""
    db = get_connection()
    try:
        from backend.services.pipeline_engine import execute_step
        result = await execute_step(pipeline_session_id, 0, project_path, db, config)
        iterations = 0
        while result.get("status") == "auto_completed" and iterations < 20:
            result = await execute_step(
                pipeline_session_id, result["next_step"], project_path, db, config
            )
            iterations += 1
    except Exception as e:
        logger.error(f"[JARVIS BG] pipeline #{pipeline_session_id} error: {e}")
    finally:
        db.close()


# ─── SSE message endpoint ─────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/message")
async def send_message(session_id: int, data: UserMessage):
    """
    Endpoint SSE : stream les événements de traitement en temps réel.
    Format : data: {"type": "...", ...}\\n\\n
    Types : thinking | message | agent_status | done | error
    """

    async def event_stream():
        db = get_connection()
        try:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM jarvis_sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                yield svc.sse("error", {"content": "Session introuvable"})
                return

            config = load_config()

            # ── Étape 1 : save user message ────────────────────────────────
            user_msg_id = svc.add_message(session_id, "user", data.content, db)

            # ── Étape 2 : classification intent ───────────────────────────
            yield svc.sse("thinking", {"step": "classify", "content": "Analyse de votre demande…"})

            intent_data = await svc.classify_intent(data.content, config)
            intent = intent_data["intent"]
            summary = intent_data["summary"]

            yield svc.sse("thinking", {
                "step": "intent",
                "content": f"Intent détecté : {INTENT_LABELS.get(intent, intent)}"
            })

            # ── Dispatch ────────────────────────────────────────────────────

            if intent in ("chat", "status"):
                yield svc.sse("thinking", {"step": "reply", "content": "Génération de la réponse…"})

                # Historique SANS le message utilisateur courant
                cursor.execute(
                    """SELECT role, content FROM jarvis_messages
                       WHERE session_id = ? AND id < ?
                       ORDER BY id DESC LIMIT 20""",
                    (session_id, user_msg_id)
                )
                history = list(reversed([dict(r) for r in cursor.fetchall()]))

                if intent == "status":
                    tracked = svc.get_tracked_pipelines(session_id, db)
                    parts = []
                    for t in tracked:
                        st = svc.get_pipeline_status(
                            t["pipeline_session_id"], t.get("agent_type", "code"), db
                        )
                        if st:
                            parts.append(svc.format_status_content(t.get("agent_type", "?"), st))
                    reply = (
                        "**Statut de vos agents actifs :**\n\n" + "\n\n".join(parts)
                        if parts else "Aucun agent actif en ce moment."
                    )
                else:
                    reply = await svc.generate_chat_reply(data.content, history, config, db)

                reply_id = svc.add_message(session_id, "jarvis", reply, db)
                cursor.execute("SELECT * FROM jarvis_messages WHERE id = ?", (reply_id,))
                row = cursor.fetchone()
                yield svc.sse("message", {"data": svc._serialize_message(dict(row))})

            elif intent == "code":
                yield svc.sse("thinking", {"step": "dispatch", "content": "Initialisation du pipeline Code…"})

                project_id = data.project_id
                pipeline_session_id = None
                extra_context = ""

                if not project_id:
                    cursor.execute(
                        "SELECT id FROM projects WHERE module_type='code' ORDER BY id DESC LIMIT 1"
                    )
                    prow = cursor.fetchone()
                    project_id = prow["id"] if prow else None

                if project_id:
                    try:
                        from backend.services.pipeline_engine import create_session as pe_create
                        cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
                        prow = cursor.fetchone()
                        project_path = prow["path"] if prow else ""

                        ps = pe_create(project_id, "analyse", data.content, db)
                        pipeline_session_id = ps["id"]

                        yield svc.sse("thinking", {
                            "step": "pipeline_created",
                            "content": f"Pipeline #{pipeline_session_id} créé — exécution en cours…"
                        })

                        # Émettre le statut initial
                        status = svc.get_pipeline_status(pipeline_session_id, "code", db)
                        if status:
                            svc.add_message(
                                session_id, "jarvis",
                                svc.format_status_content("code", status), db,
                                message_type="agent_status", agent_type="code",
                                pipeline_session_id=pipeline_session_id,
                                metadata={"session_status": status["status"], "step_id": None, "step_status": None},
                            )

                        # Lancer l'exécution en tâche de fond
                        asyncio.create_task(
                            _run_pipeline_bg(pipeline_session_id, project_path, config)
                        )
                        extra_context = f"Pipeline #{pipeline_session_id} lancé sur le projet #{project_id}."

                    except Exception as e:
                        logger.error(f"[JARVIS] code dispatch error: {e}")
                        extra_context = f"Erreur lors du lancement : {e}"
                else:
                    extra_context = "Aucun projet code disponible — créez d'abord un projet dans le Module Code."

                yield svc.sse("thinking", {"step": "reply", "content": "Rédaction de la confirmation…"})
                reply = await svc.generate_dispatch_reply(
                    intent, summary, pipeline_session_id, config, db, extra_context
                )
                reply_id = svc.add_message(session_id, "jarvis", reply, db)

                # Retourner les nouveaux messages (statut + réponse)
                cursor.execute(
                    "SELECT * FROM jarvis_messages WHERE session_id = ? ORDER BY id DESC LIMIT 5",
                    (session_id,)
                )
                for row in reversed(cursor.fetchall()):
                    yield svc.sse("message", {"data": svc._serialize_message(dict(row))})

            elif intent == "reflexion":
                yield svc.sse("thinking", {"step": "dispatch", "content": "Création de la session Réflexion…"})

                project_id = data.project_id
                pipeline_session_id = None
                extra_context = ""

                if not project_id:
                    cursor.execute(
                        "SELECT id FROM projects WHERE module_type='dossier' ORDER BY id DESC LIMIT 1"
                    )
                    prow = cursor.fetchone()
                    project_id = prow["id"] if prow else None

                if project_id:
                    try:
                        from backend.services.reflexion_service import (
                            create_session as ref_create, LivrableType, send_user_message as ref_send
                        )
                        ref_id = ref_create(project_id, LivrableType.MISSION_CODE, db)
                        pipeline_session_id = ref_id

                        yield svc.sse("thinking", {
                            "step": "reflexion_created",
                            "content": f"Session Réflexion #{ref_id} créée — envoi du message initial…"
                        })

                        # Envoyer le prompt initial en fond (appel LLM lent)
                        asyncio.create_task(_run_reflexion_bg(ref_id, data.content))
                        extra_context = f"Session Réflexion #{ref_id} démarrée dans le projet #{project_id}."

                        # Émettre le statut initial
                        status = svc.get_pipeline_status(pipeline_session_id, "reflexion", db)
                        if status:
                            svc.add_message(
                                session_id, "jarvis",
                                svc.format_status_content("reflexion", status), db,
                                message_type="agent_status", agent_type="reflexion",
                                pipeline_session_id=pipeline_session_id,
                                metadata={"session_status": status["status"], "step_id": None, "step_status": None},
                            )

                    except Exception as e:
                        logger.error(f"[JARVIS] reflexion dispatch error: {e}")
                        extra_context = f"Erreur : {e}"
                else:
                    extra_context = "Aucun dossier projet disponible — créez d'abord un dossier."

                yield svc.sse("thinking", {"step": "reply", "content": "Rédaction de la confirmation…"})
                reply = await svc.generate_dispatch_reply(
                    intent, summary, pipeline_session_id, config, db, extra_context
                )
                reply_id = svc.add_message(session_id, "jarvis", reply, db)

                cursor.execute(
                    "SELECT * FROM jarvis_messages WHERE session_id = ? ORDER BY id DESC LIMIT 5",
                    (session_id,)
                )
                for row in reversed(cursor.fetchall()):
                    yield svc.sse("message", {"data": svc._serialize_message(dict(row))})

            elif intent == "atelier":
                reply = (
                    "Je transmets votre demande au Module Atelier. "
                    "Rendez-vous sur la page Atelier pour créer ou gérer un prospect et lancer le pipeline."
                )
                reply_id = svc.add_message(
                    session_id, "jarvis", reply, db,
                    message_type="text", agent_type="atelier"
                )
                cursor.execute("SELECT * FROM jarvis_messages WHERE id = ?", (reply_id,))
                row = cursor.fetchone()
                yield svc.sse("message", {"data": svc._serialize_message(dict(row))})

            elif intent == "sentinelle":
                reply = (
                    "Je relaye votre demande au module Sentinelle. "
                    "Rendez-vous sur la page Sentinelle pour les données en temps réel, "
                    "ou précisez ce que vous souhaitez faire."
                )
                reply_id = svc.add_message(
                    session_id, "jarvis", reply, db,
                    message_type="text", agent_type="sentinelle"
                )
                cursor.execute("SELECT * FROM jarvis_messages WHERE id = ?", (reply_id,))
                row = cursor.fetchone()
                yield svc.sse("message", {"data": svc._serialize_message(dict(row))})

            yield svc.sse("done", {})

        except Exception as e:
            logger.error(f"[JARVIS] event_stream error: {e}")
            yield svc.sse("error", {"content": str(e)})
        finally:
            db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _run_reflexion_bg(ref_id: int, content: str):
    """Envoie le message initial à la réflexion en fond (connexion DB dédiée)."""
    db = get_connection()
    try:
        from backend.services.reflexion_service import send_user_message
        await send_user_message(ref_id, content, db)
    except Exception as e:
        logger.error(f"[JARVIS BG] reflexion #{ref_id} error: {e}")
    finally:
        db.close()


# ─── Polling agent updates ────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/agent-updates")
def get_agent_updates(session_id: int, since_id: int = 0):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM jarvis_sessions WHERE id = ?", (session_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(404, "Session introuvable")

    svc.check_and_emit_agent_updates(session_id, db)

    cursor.execute(
        "SELECT * FROM jarvis_messages WHERE session_id = ? AND id > ? ORDER BY id",
        (session_id, since_id)
    )
    msgs = [svc._serialize_message(dict(r)) for r in cursor.fetchall()]
    db.close()
    return {"messages": msgs}


# ─── Validation ───────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/validate/{pipeline_session_id}/{step_id}")
def validate_step(
    session_id: int,
    pipeline_session_id: int,
    step_id: int,
    data: ValidationPayload,
):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM jarvis_sessions WHERE id = ?", (session_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(404, "Session Jarvis introuvable")

    cursor.execute(
        "SELECT path FROM projects p JOIN sessions s ON s.project_id=p.id WHERE s.id=?",
        (pipeline_session_id,)
    )
    prow = cursor.fetchone()
    project_path = prow["path"] if prow else None

    from backend.services.pipeline_engine import validate_step as pe_validate
    result = pe_validate(
        session_id=pipeline_session_id,
        step_id=step_id,
        validation={"approved": data.approved, "feedback": data.feedback},
        db=db,
        project_path=project_path,
    )

    action = "validée" if data.approved else "rejetée"
    content = f"{'✅' if data.approved else '❌'} Étape #{step_id} **{action}**."
    if not data.approved and data.feedback:
        content += f"\nRetour : {data.feedback}"

    svc.add_message(
        session_id, "jarvis", content, db,
        message_type="text",
        pipeline_session_id=pipeline_session_id,
        pipeline_step_id=step_id,
    )
    db.close()
    return {"ok": True, "action": action, "result": result}
