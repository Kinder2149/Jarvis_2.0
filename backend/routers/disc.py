import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.database import get_connection, load_config

router = APIRouter(prefix="/disc", tags=["disc"])
logger = logging.getLogger("jarvis")


class SituationRequest(BaseModel):
    message: str


# ─── GET /api/disc/stats ──────────────────────────────────────────────────────

@router.get("/stats")
def get_stats():
    db = get_connection()
    try:
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) as total FROM disc_sessions")
        total_questions = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) as total FROM disc_rules")
        rules_loaded = cur.fetchone()["total"]

        cur.execute("SELECT MAX(created_at) as last_at FROM disc_sessions")
        row = cur.fetchone()
        last_at = row["last_at"] if row else None

        return {
            "total_questions": total_questions,
            "rules_loaded": rules_loaded,
            "last_at": last_at
        }
    finally:
        db.close()


# ─── GET /api/disc/rules ──────────────────────────────────────────────────────

@router.get("/rules")
def list_rules(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    db = get_connection()
    try:
        cur = db.cursor()
        offset = (page - 1) * per_page

        cur.execute("SELECT COUNT(*) as total FROM disc_rules")
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT id, article, parent_article, titre, categorie, mots_cles, cross_refs, created_at
            FROM disc_rules
            ORDER BY article
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        rules = [dict(r) for r in cur.fetchall()]

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "rules": rules
        }
    finally:
        db.close()


# ─── GET /api/disc/rules/{article} ───────────────────────────────────────────

@router.get("/rules/{article:path}")
def get_rule(article: str):
    db = get_connection()
    try:
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM disc_rules WHERE article = ?",
            (article,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Article {article} non trouvé")
        return dict(row)
    finally:
        db.close()


# ─── GET /api/disc/search?q= ──────────────────────────────────────────────────

@router.get("/search")
def search_rules(q: str = Query(..., min_length=2)):
    db = get_connection()
    try:
        cur = db.cursor()
        like = f"%{q.lower()}%"
        cur.execute("""
            SELECT id, article, titre, categorie, contenu, mots_cles
            FROM disc_rules
            WHERE LOWER(titre) LIKE ?
               OR LOWER(contenu) LIKE ?
               OR LOWER(mots_cles) LIKE ?
               OR article LIKE ?
            ORDER BY article
            LIMIT 20
        """, (like, like, like, f"%{q}%"))
        results = [dict(r) for r in cur.fetchall()]
        return {"query": q, "results": results, "total": len(results)}
    finally:
        db.close()


# ─── POST /api/disc/situation ─────────────────────────────────────────────────

@router.post("/situation")
async def resolve_situation(body: SituationRequest):
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")

    db = get_connection()
    try:
        from backend.services.disc_handler import handle as disc_handle
        config = load_config()
        content, agent_used, _, _, _ = await disc_handle(
            conversation_id=0,
            message=body.message,
            current_instance_ref=None,
            db=db,
            config=config
        )
        return {"response": content, "agent": agent_used}
    except Exception as e:
        logger.error(f"[DISC] /situation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
