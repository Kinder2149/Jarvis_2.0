from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import json
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


@router.patch("/conversations/{conversation_id}/title", status_code=200)
def rename_conversation(conversation_id: int, body: dict):
    """Renomme une conversation JARVIS."""
    title = (body.get("title") or "").strip()[:120]
    db = get_connection()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
        (title or None, conversation_id)
    )
    if cursor.rowcount == 0:
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    db.commit()
    db.close()
    return {"id": conversation_id, "title": title}


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


@router.get("/situation")
def get_situation():
    """Retourne l'état actionnable de JARVIS pour le tableau de bord."""
    db = get_connection()
    cursor = db.cursor()

    # 1. Missions CASCADE en cours
    cursor.execute("""
        SELECT c.id, c.title, m.instance_ref, m.created_at
        FROM conversations c
        JOIN messages m ON m.id = (
            SELECT id FROM messages
            WHERE conversation_id = c.id AND role = 'assistant'
            ORDER BY created_at DESC LIMIT 1
        )
        WHERE json_extract(m.instance_ref, '$.type') = 'cascade_mission'
        ORDER BY m.created_at DESC
        LIMIT 5
    """)
    cascade_missions = []
    for row in cursor.fetchall():
        ref = json.loads(row["instance_ref"]) if row["instance_ref"] else {}
        cascade_missions.append({
            "conversation_id": row["id"],
            "title": row["title"] or f"Mission #{row['id']}",
            "step": ref.get("step", 1),
            "total": ref.get("total", 1),
            "updated_at": row["created_at"],
        })

    # 2. Réflexions figées non consommées (prêtes à lancer dans Cascade)
    try:
        cursor.execute("""
            SELECT rs.id, rs.titre, rs.created_at, mp.id as mp_id
            FROM reflexion_sessions rs
            JOIN mission_prompts mp ON mp.reflexion_session_id = rs.id
            WHERE rs.statut = 'FIGEE'
              AND mp.forge_session_id IS NULL
              AND mp.consumed_at IS NULL
            ORDER BY rs.created_at DESC
        """)
        reflexions_pretes = [
            {"session_id": r["id"], "titre": r["titre"] or "Sans titre",
             "mp_id": r["mp_id"], "created_at": r["created_at"]}
            for r in cursor.fetchall()
        ]
    except Exception:
        reflexions_pretes = []

    # 3. Plans en attente de réponse utilisateur
    try:
        cursor.execute("""
            SELECT jp.id, jp.title, jp.home_conversation_id,
                   jps.agent, jps.title as step_title
            FROM jarvis_plans jp
            JOIN jarvis_plan_steps jps ON jps.plan_id = jp.id
            WHERE jps.status = 'EN_ATTENTE_UTILISATEUR'
              AND jp.status = 'EN_COURS'
            ORDER BY jp.updated_at DESC
        """)
        plans_en_attente = [
            {"plan_id": r["id"], "title": r["title"],
             "conversation_id": r["home_conversation_id"],
             "agent": r["agent"], "step_title": r["step_title"]}
            for r in cursor.fetchall()
        ]
    except Exception:
        plans_en_attente = []

    # 4. Alertes Sentinelle non lues
    try:
        cursor.execute("SELECT COUNT(*) as nb FROM sentinelle_alertes WHERE lu = 0")
        alertes_count = cursor.fetchone()["nb"]
    except Exception:
        alertes_count = 0

    # 5. Dernier projet touché
    try:
        cursor.execute("""
            SELECT p.id, p.name, MAX(rs.updated_at) as last_activity
            FROM projects p
            JOIN reflexion_sessions rs ON rs.project_id = p.id
            GROUP BY p.id ORDER BY last_activity DESC LIMIT 1
        """)
        row = cursor.fetchone()
        dernier_projet = {"id": row["id"], "name": row["name"],
                          "last_activity": row["last_activity"]} if row else None
    except Exception:
        dernier_projet = None

    db.close()
    return {
        "cascade_missions": cascade_missions,
        "reflexions_pretes": reflexions_pretes,
        "plans_en_attente": plans_en_attente,
        "alertes_sentinelle": alertes_count,
        "dernier_projet": dernier_projet,
    }


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
