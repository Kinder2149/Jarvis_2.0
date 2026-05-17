# backend/routers/jarvis.py

import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import get_connection, load_config
from backend.services import jarvis_service as svc

logger = logging.getLogger("jarvis")
router = APIRouter(prefix="/jarvis", tags=["jarvis"])


# ─── Schémas ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str = "Session Jarvis"


class UserMessage(BaseModel):
    content: str
    project_id: int | None = None


class ValidationPayload(BaseModel):
    approved: bool
    feedback: str = ""


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.post("/sessions")
def create_session(data: SessionCreate):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO jarvis_sessions (title) VALUES (?)",
        (data.title,)
    )
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
    cursor.execute(
        "SELECT * FROM jarvis_sessions ORDER BY updated_at DESC LIMIT 30"
    )
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
    cursor = db.cursor()
    cursor.execute("DELETE FROM jarvis_sessions WHERE id = ?", (session_id,))
    db.commit()
    db.close()
    return {"ok": True}


# ─── Envoi d'un message utilisateur ──────────────────────────────────────────

@router.post("/sessions/{session_id}/message")
async def send_message(session_id: int, data: UserMessage):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM jarvis_sessions WHERE id = ?", (session_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(404, "Session introuvable")

    config = load_config()

    # 1 — Sauvegarder le message utilisateur
    user_msg_id = svc.add_message(
        session_id=session_id,
        role="user",
        content=data.content,
        db_conn=db,
    )

    # 2 — Classifier l'intent
    intent_data = await svc.classify_intent(data.content, config, db)
    intent = intent_data["intent"]
    summary = intent_data["summary"]

    logger.info(f"[JARVIS] session={session_id} intent={intent} summary={summary!r}")

    # 3 — Dispatch selon intent
    if intent in ("chat", "status"):
        cursor.execute(
            "SELECT role, content FROM jarvis_messages WHERE session_id = ? ORDER BY id DESC LIMIT 20",
            (session_id,)
        )
        history = list(reversed([dict(r) for r in cursor.fetchall()]))

        if intent == "status":
            tracked = svc.get_tracked_pipelines(session_id, db)
            status_parts = []
            for t in tracked:
                ps = svc.get_pipeline_status(t["pipeline_session_id"], db)
                if ps:
                    status_parts.append(svc.format_status_content(
                        t.get("agent_type", "unknown"), ps
                    ))
            reply = (
                "**Statut de vos agents actifs :**\n\n" + "\n\n".join(status_parts)
                if status_parts
                else "Aucun agent actif en ce moment."
            )
        else:
            reply = await svc.generate_chat_reply(data.content, history, config, db)

        reply_id = svc.add_message(
            session_id=session_id,
            role="jarvis",
            content=reply,
            db_conn=db,
            message_type="text",
        )

        cursor.execute(
            "SELECT * FROM jarvis_messages WHERE id IN (?, ?)",
            (user_msg_id, reply_id)
        )
        rows = [svc._serialize_message(dict(r)) for r in cursor.fetchall()]
        db.close()
        return {"messages": rows, "intent": intent}

    elif intent == "code":
        pipeline_session_id = None
        extra_context = ""

        project_id = data.project_id
        if not project_id:
            cursor.execute(
                "SELECT id FROM projects WHERE module_type='code' ORDER BY id DESC LIMIT 1"
            )
            prow = cursor.fetchone()
            project_id = prow["id"] if prow else None

        if project_id:
            try:
                from backend.services.pipeline_engine import create_session as pe_create, execute_step
                cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
                prow = cursor.fetchone()
                project_path = prow["path"] if prow else ""

                ps = pe_create(project_id, "analyse", data.content, db)
                pipeline_session_id = ps["id"]

                exec_result = await execute_step(
                    pipeline_session_id, 0, project_path, db, config
                )
                while exec_result.get("status") == "auto_completed":
                    exec_result = await execute_step(
                        pipeline_session_id,
                        exec_result["next_step"],
                        project_path, db, config
                    )

                extra_context = f"Pipeline démarré sur le projet #{project_id}."
            except Exception as e:
                logger.error(f"[JARVIS] code dispatch error : {e}")
                extra_context = f"Erreur lors du lancement du pipeline : {e}"
        else:
            extra_context = "Aucun projet code disponible — créez d'abord un projet dans le Module Code."

        return await _finish_dispatch(
            db, cursor, session_id, user_msg_id,
            intent, summary, pipeline_session_id, config, extra_context
        )

    elif intent == "reflexion":
        pipeline_session_id = None
        extra_context = ""

        project_id = data.project_id
        if not project_id:
            cursor.execute(
                "SELECT id FROM projects WHERE module_type='dossier' ORDER BY id DESC LIMIT 1"
            )
            prow = cursor.fetchone()
            project_id = prow["id"] if prow else None

        if project_id:
            try:
                from backend.services.reflexion_service import (
                    create_session as ref_create,
                    LivrableType,
                    send_user_message as ref_send,
                )
                ref_id = ref_create(project_id, LivrableType.RAPPORT, db)
                pipeline_session_id = ref_id
                # Envoyer le prompt initial dans la réflexion
                await ref_send(ref_id, data.content, db)
                extra_context = f"Session Réflexion #{ref_id} démarrée dans le projet #{project_id}."
            except Exception as e:
                logger.error(f"[JARVIS] reflexion dispatch error : {e}")
                extra_context = f"Erreur lors de la création de la réflexion : {e}"
        else:
            extra_context = "Aucun dossier projet disponible — créez d'abord un dossier."

        return await _finish_dispatch(
            db, cursor, session_id, user_msg_id,
            intent, summary, pipeline_session_id, config, extra_context
        )

    elif intent == "atelier":
        reply = (
            "Je transmets votre demande au Module Atelier. "
            "Rendez-vous sur la page Atelier pour créer ou gérer un prospect et lancer le pipeline."
        )
        reply_id = svc.add_message(
            session_id=session_id,
            role="jarvis",
            content=reply,
            db_conn=db,
            message_type="text",
            agent_type="atelier",
        )
        cursor.execute(
            "SELECT * FROM jarvis_messages WHERE id IN (?, ?)",
            (user_msg_id, reply_id)
        )
        rows = [svc._serialize_message(dict(r)) for r in cursor.fetchall()]
        db.close()
        return {"messages": rows, "intent": intent}

    elif intent == "sentinelle":
        reply = (
            "Je relaye votre demande au module Sentinelle. "
            "Rendez-vous sur la page Sentinelle pour les données temps réel, "
            "ou précisez ce que vous souhaitez faire (ajouter position, lancer un cycle…)."
        )
        reply_id = svc.add_message(
            session_id=session_id,
            role="jarvis",
            content=reply,
            db_conn=db,
            message_type="text",
            agent_type="sentinelle",
        )
        cursor.execute(
            "SELECT * FROM jarvis_messages WHERE id IN (?, ?)",
            (user_msg_id, reply_id)
        )
        rows = [svc._serialize_message(dict(r)) for r in cursor.fetchall()]
        db.close()
        return {"messages": rows, "intent": intent}

    db.close()
    return {"messages": [], "intent": intent}


async def _finish_dispatch(
    db, cursor, session_id, user_msg_id,
    intent, summary, pipeline_session_id, config, extra_context
):
    """Émet le message de statut initial et la réponse de confirmation Jarvis."""
    if pipeline_session_id:
        status = svc.get_pipeline_status(pipeline_session_id, db)
        if status:
            svc.add_message(
                session_id=session_id,
                role="jarvis",
                content=svc.format_status_content(intent, status),
                db_conn=db,
                message_type="agent_status",
                agent_type=intent,
                pipeline_session_id=pipeline_session_id,
                metadata={
                    "session_status": status.get("status"),
                    "step_id": None,
                    "step_status": None,
                },
            )

    reply = await svc.generate_dispatch_reply(
        intent=intent,
        summary=summary,
        pipeline_session_id=pipeline_session_id,
        config=config,
        db_conn=db,
        extra_context=extra_context,
    )
    reply_id = svc.add_message(
        session_id=session_id,
        role="jarvis",
        content=reply,
        db_conn=db,
        message_type="text",
    )

    cursor.execute(
        "SELECT * FROM jarvis_messages WHERE session_id = ? ORDER BY id DESC LIMIT 10",
        (session_id,)
    )
    rows = list(reversed([svc._serialize_message(dict(r)) for r in cursor.fetchall()]))
    db.close()
    return {"messages": rows, "intent": intent, "pipeline_session_id": pipeline_session_id}


# ─── Polling agent status ─────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/agent-updates")
def get_agent_updates(session_id: int, since_id: int = 0):
    """Vérifie les mises à jour des agents et retourne les nouveaux messages."""
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
    all_new = [svc._serialize_message(dict(r)) for r in cursor.fetchall()]
    db.close()
    return {"messages": all_new}


# ─── Validation ───────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/validate/{pipeline_session_id}/{step_id}")
def validate_step(
    session_id: int,
    pipeline_session_id: int,
    step_id: int,
    data: ValidationPayload,
):
    """Valide ou rejette une étape pipeline depuis l'interface Jarvis."""
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM jarvis_sessions WHERE id = ?", (session_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(404, "Session Jarvis introuvable")

    cursor.execute("SELECT path FROM projects p JOIN sessions s ON s.project_id=p.id WHERE s.id=?",
                   (pipeline_session_id,))
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
        session_id=session_id,
        role="jarvis",
        content=content,
        db_conn=db,
        message_type="text",
        pipeline_session_id=pipeline_session_id,
        pipeline_step_id=step_id,
    )
    db.close()
    return {"ok": True, "action": action, "result": result}
