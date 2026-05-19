from fastapi import APIRouter, HTTPException
from backend.database import get_connection
import logging

logger = logging.getLogger("jarvis")
router = APIRouter(prefix="/media", tags=["media"])


@router.get("/stats")
def get_stats():
    """Stats pour la carte agent MEDIA dans l'Orchestrateur."""
    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as total FROM media_jobs WHERE status = 'done'")
        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT media_type, created_at, result_url
            FROM media_jobs WHERE status = 'done'
            ORDER BY created_at DESC LIMIT 1
        """)
        last = cursor.fetchone()

        return {
            "total": total,
            "last_type": last["media_type"] if last else None,
            "last_at": last["created_at"] if last else None,
        }
    finally:
        db.close()


@router.get("/history")
def get_history(limit: int = 20):
    """Historique des générations Media."""
    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT id, conversation_id, media_type, prompt, result_url, status, created_at
            FROM media_jobs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        db.close()


@router.get("/jobs/{job_id}")
def get_job(job_id: int):
    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM media_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job introuvable")
        return dict(row)
    finally:
        db.close()
