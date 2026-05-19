from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging

from backend.database import get_connection, load_config
from backend.services import jarvis_service, forge_handler

logger = logging.getLogger("jarvis")
router = APIRouter(prefix="/jarvis", tags=["jarvis"])


class JarvisConversationCreate(BaseModel):
    project_id: int | None = None
    title: str = "Nouvelle conversation JARVIS"


class JarvisChatMessage(BaseModel):
    message: str
    force_agent: str | None = None


class ForgeStartRequest(BaseModel):
    mission_prompt_id: int
    conversation_id: int


class ForgeLaunchFromMentorRequest(BaseModel):
    reflexion_session_id: int
    conversation_id: int


class ConversationProjectUpdate(BaseModel):
    project_id: int | None


@router.post("/conversations", status_code=201)
def create_conversation(body: JarvisConversationCreate):
    db = get_connection()
    cursor = db.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute(
        """INSERT INTO conversations (project_id, title, folder_path,
           internet_access, context_summary, model, created_at, updated_at)
           VALUES (?, ?, NULL, 0, '', 'jarvis', ?, ?)""",
        (body.project_id, body.title, now, now)
    )
    conv_id = cursor.lastrowid
    db.commit()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    row = cursor.fetchone()
    db.close()
    return dict(row)


@router.get("/conversations")
def list_conversations():
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON m.conversation_id = c.id
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        LIMIT 50
    """)
    rows = cursor.fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    conv = cursor.fetchone()
    if not conv:
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    # Vérifier alertes Sentinelle
    alerte_content = jarvis_service.check_sentinelle_alertes(conversation_id, db)
    if alerte_content:
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'SENTINELLE_ALERT', NULL, datetime('now'))
        """, (conversation_id, alerte_content))
        db.commit()

    cursor.execute("""
        SELECT id, role, content, agent, instance_ref, created_at
        FROM messages WHERE conversation_id = ?
        ORDER BY created_at ASC
    """, (conversation_id,))
    messages = [dict(m) for m in cursor.fetchall()]
    db.close()

    return {**dict(conv), "messages": messages}


@router.post("/conversations/{conversation_id}/chat")
async def chat(conversation_id: int, body: JarvisChatMessage):
    """Envoie un message dans une conversation JARVIS et retourne la réponse."""
    db = get_connection()
    try:
        result = await jarvis_service.process_message(
            conversation_id=conversation_id,
            user_message=body.message,
            db=db,
            force_agent=body.force_agent
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"[JARVIS] Erreur chat conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/forge/start")
async def forge_start(body: ForgeStartRequest):
    """Démarre un pipeline FORGE depuis un livrable MENTOR figé."""
    db = get_connection()
    try:
        result = await forge_handler.start(
            mission_prompt_id=body.mission_prompt_id,
            conversation_id=body.conversation_id,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"[JARVIS] Erreur forge/start: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/verify/{session_id}")
async def verify_forge(session_id: int):
    """Vérification cohérence MENTOR→FORGE après exécution du pipeline."""
    db = get_connection()
    try:
        result = await forge_handler.verify(session_id, db)
        return result
    except Exception as e:
        logger.exception(f"[JARVIS] Erreur verify {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.patch("/conversations/{conversation_id}/project", status_code=200)
def update_conversation_project(conversation_id: int, body: ConversationProjectUpdate):
    """Met à jour le projet associé à une conversation JARVIS."""
    db = get_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE conversations SET project_id = ?, updated_at = datetime('now') WHERE id = ?",
        (body.project_id, conversation_id)
    )
    if cursor.rowcount == 0:
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    db.commit()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    row = dict(cursor.fetchone())
    db.close()
    return row


@router.post("/forge/launch-from-mentor")
async def forge_launch_from_mentor(body: ForgeLaunchFromMentorRequest):
    """
    Fige la session MENTOR puis démarre FORGE en un seul appel.
    Appelé depuis le bouton "Démarrer FORGE" du banner suggest_freeze dans jarvis.html.
    """
    db = get_connection()
    try:
        from backend.services import reflexion_service

        # Récupérer la session pour vérifier son statut
        session = reflexion_service.get_session(body.reflexion_session_id, db)
        if not session:
            raise ValueError(f"Session réflexion {body.reflexion_session_id} introuvable")

        # Figer si pas encore figé
        if session["statut"] != "FIGEE":
            await reflexion_service.freeze_session(body.reflexion_session_id, db)

        # Récupérer le mission_prompt généré par le figement
        livrable = reflexion_service.get_livrable(body.reflexion_session_id, db)
        if not livrable:
            raise ValueError("Aucun livrable disponible après figement — réessaie dans quelques secondes.")

        mission_prompt_id = livrable["id"]

        # Démarrer FORGE
        result = await forge_handler.start(
            mission_prompt_id=mission_prompt_id,
            conversation_id=body.conversation_id,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"[JARVIS] Erreur forge/launch-from-mentor: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/pipeline/{session_id}/progress")
def get_pipeline_progress(session_id: int):
    """Retourne l'état détaillé des steps d'un pipeline FORGE pour l'affichage dans JARVIS."""
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT status, current_step_index FROM sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    if not session:
        db.close()
        raise HTTPException(status_code=404, detail="Pipeline introuvable")
    cursor.execute("""
        SELECT step_index, step_display_name, status, summary_fr, error_message
        FROM pipeline_steps
        WHERE session_id = ? AND (sub_step_index IS NULL OR sub_step_index = -1)
        ORDER BY step_index ASC
    """, (session_id,))
    steps = [dict(s) for s in cursor.fetchall()]
    db.close()
    return {
        "session_id": session_id,
        "status": session["status"],
        "current_step_index": session["current_step_index"],
        "steps": steps
    }


@router.post("/project/{project_id}/reset-forge", status_code=200)
def reset_forge_state(project_id: int):
    """
    Réinitialise les sessions FORGE FAILED/ABORTED/CREATED (fantômes) d'un projet.
    Débloque les livrables MENTOR coincés, permettant un nouveau lancement.
    """
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT mp.id FROM mission_prompts mp
        JOIN reflexion_sessions rs ON rs.id = mp.reflexion_session_id
        JOIN sessions s ON s.id = mp.forge_session_id
        WHERE rs.project_id = ? AND s.status IN ('FAILED', 'ABORTED', 'CREATED')
    """, (project_id,))
    rows = cursor.fetchall()
    count = len(rows)
    for row in rows:
        cursor.execute(
            "UPDATE mission_prompts SET forge_session_id = NULL, consumed_at = NULL WHERE id = ?",
            (row["id"],)
        )
    db.commit()
    db.close()
    return {"reset_count": count, "message": f"{count} livrable(s) débloqué(s) — tu peux relancer FORGE."}


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int):
    """Supprime une conversation JARVIS et tous ses messages."""
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    db.commit()
    if cursor.rowcount == 0:
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    db.close()


@router.get("/pipelines/overview")
def get_pipelines_overview(active_only: bool = False):
    """Retourne les 50 sessions FORGE les plus récentes avec contexte projet et mission."""
    db = get_connection()
    cursor = db.cursor()

    active_statuses = ('CREATED', 'RUNNING', 'WAITING_VALIDATION')
    where_clause = f"WHERE s.status IN {active_statuses}" if active_only else ""

    cursor.execute(f"""
        SELECT
            s.id, s.status, s.current_step_index, s.created_at, s.updated_at,
            p.id AS project_id, p.name AS project_name,
            rs.titre AS mission_title,
            ps_current.step_display_name AS current_step_name,
            ps_total.total_steps
        FROM sessions s
        LEFT JOIN projects p ON p.id = s.project_id
        LEFT JOIN mission_prompts mp ON mp.forge_session_id = s.id
        LEFT JOIN reflexion_sessions rs ON rs.id = mp.reflexion_session_id
        LEFT JOIN pipeline_steps ps_current
            ON ps_current.session_id = s.id
            AND ps_current.step_index = s.current_step_index
            AND (ps_current.sub_step_index IS NULL OR ps_current.sub_step_index = -1)
        LEFT JOIN (
            SELECT session_id, COUNT(*) AS total_steps
            FROM pipeline_steps
            WHERE sub_step_index IS NULL OR sub_step_index = -1
            GROUP BY session_id
        ) ps_total ON ps_total.session_id = s.id
        {where_clause}
        ORDER BY s.updated_at DESC
        LIMIT 50
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    db.close()
    return {"pipelines": rows, "count": len(rows)}
