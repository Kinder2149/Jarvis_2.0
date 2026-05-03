from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import asyncio
import logging

logger = logging.getLogger("jarvis")

from backend.database import get_connection
from backend.schemas.reflexion import (
    CreateReflexion,
    SendMessage,
    ProposerEdit,
    AppliquerEdit,
    ReflexionSession,
    ReflexionSessionWithMessages,
    ReflexionMessage,
    CadrageHealth
)
from backend.services import reflexion_service
from backend.services.cadrage import check_cadrage_health

router = APIRouter(prefix="/reflexions", tags=["reflexions"])


@router.post("", status_code=201)
def create_reflexion(body: CreateReflexion):
    """Crée une nouvelle session de réflexion."""
    conn = get_connection()
    try:
        session_id = reflexion_service.create_session(
            body.project_id,
            body.livrable_type,
            conn
        )
        session = reflexion_service.get_session(session_id, conn)
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[REFLEXIONS] Erreur dans create_reflexion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("")
def list_reflexions(project_id: Optional[int] = Query(None)):
    """Liste les sessions de réflexion, optionnellement filtrées par projet."""
    conn = get_connection()
    try:
        if project_id is not None:
            sessions = reflexion_service.get_sessions_by_project(project_id, conn)
        else:
            # Retourner toutes les sessions (non implémenté dans le service, on retourne vide)
            sessions = []
        return sessions
    finally:
        conn.close()


@router.get("/{session_id}")
def get_reflexion(session_id: int):
    """Récupère une session avec ses messages."""
    conn = get_connection()
    try:
        session = reflexion_service.get_session(session_id, conn)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} introuvable")
        
        messages = reflexion_service.get_messages(session_id, conn, include_compacted=False)
        
        return {
            **session,
            "messages": messages
        }
    finally:
        conn.close()


@router.delete("/{session_id}", status_code=204)
def delete_reflexion(session_id: int):
    """Supprime une session (uniquement OUVERTE ou ABANDONNEE)."""
    conn = get_connection()
    try:
        reflexion_service.delete_session(session_id, conn)
    except ValueError as e:
        if "introuvable" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception(f"[REFLEXIONS] Erreur dans delete_reflexion session={session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{session_id}/abandon", status_code=200)
def abandon_reflexion(session_id: int):
    """Passe une session en statut ABANDONNEE."""
    conn = get_connection()
    try:
        reflexion_service.abandon_session(session_id, conn)
        session = reflexion_service.get_session(session_id, conn)
        return session
    except ValueError as e:
        if "introuvable" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception(f"[REFLEXIONS] Erreur dans abandon_reflexion session={session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{session_id}/messages", status_code=201)
async def send_message(session_id: int, body: SendMessage):
    """
    Envoie un message utilisateur et appelle Claude Sonnet 4.5 pour obtenir une réponse.
    """
    conn = get_connection()
    try:
        messages = await reflexion_service.send_user_message(
            session_id,
            body.content,
            conn
        )
        return messages
    except ValueError as e:
        if "introuvable" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception(f"[REFLEXIONS] Erreur dans send_message session={session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/{session_id}/messages")
def get_messages(session_id: int, include_compacted: bool = Query(False)):
    """Récupère les messages d'une session."""
    conn = get_connection()
    try:
        messages = reflexion_service.get_messages(session_id, conn, include_compacted)
        return messages
    finally:
        conn.close()


@router.post("/{session_id}/sante-cadrage", status_code=200)
def check_sante_cadrage(session_id: int):
    """Relance le check santé cadrage pour une session."""
    conn = get_connection()
    try:
        session = reflexion_service.get_session(session_id, conn)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} introuvable")
        
        health = check_cadrage_health(session["project_id"], conn)
        return health
    finally:
        conn.close()


@router.post("/{session_id}/proposer-edit", status_code=200)
def proposer_edit(session_id: int, body: ProposerEdit):
    """Calcule le diff pour une édition proposée."""
    conn = get_connection()
    try:
        diff_result = reflexion_service.propose_edit(
            session_id,
            body.file_path,
            body.new_content,
            conn
        )
        return diff_result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.exception(f"[REFLEXIONS] Erreur dans proposer_edit session={session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{session_id}/appliquer-edit", status_code=200)
def appliquer_edit(session_id: int, body: AppliquerEdit):
    """Applique une édition sur un fichier .md autorisé."""
    conn = get_connection()
    try:
        if not body.confirmed:
            raise HTTPException(status_code=400, detail="confirmed doit être true")
        
        reflexion_service.apply_edit(
            session_id,
            body.file_path,
            body.new_content,
            conn
        )
        
        return {"status": "applied", "file_path": body.file_path}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.exception(f"[REFLEXIONS] Erreur dans appliquer_edit session={session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{session_id}/figer", status_code=200)
async def figer_session(session_id: int):
    """Fige une session de réflexion et génère le livrable final."""
    conn = get_connection()
    try:
        livrable = await reflexion_service.freeze_session(session_id, conn)
        return livrable
    except ValueError as e:
        if "introuvable" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception(f"[REFLEXIONS] Erreur dans figer_session session={session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/{session_id}/livrable", status_code=200)
def get_livrable(session_id: int):
    """Récupère le livrable (mission_prompts) d'une session figée."""
    conn = get_connection()
    try:
        livrable = reflexion_service.get_livrable(session_id, conn)
        if not livrable:
            raise HTTPException(status_code=404, detail=f"Aucun livrable pour la session {session_id}")
        return livrable
    finally:
        conn.close()


@router.post("/{session_id}/marquer-consomme", status_code=200)
def marquer_consomme(session_id: int):
    """Marque le livrable d'une session comme consommé (copié dans Module Code)."""
    conn = get_connection()
    try:
        livrable = reflexion_service.get_livrable(session_id, conn)
        if not livrable:
            raise HTTPException(status_code=404, detail=f"Aucun livrable pour la session {session_id}")
        
        reflexion_service.mark_consumed(livrable["id"], conn)
        return {"status": "marked_consumed", "mission_prompt_id": livrable["id"]}
    finally:
        conn.close()
