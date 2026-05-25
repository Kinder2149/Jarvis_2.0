from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import get_connection

router = APIRouter(prefix="/plans", tags=["plans"])


class StepInput(BaseModel):
    agent: str         # MENTOR | FORGE | SENTINELLE | ATELIER | MEDIA | JARVIS
    title: str         # label court affiché
    input_message: str # message envoyé à l'agent
    depends_on_order: int | None = None  # step_order de l'étape dont on dépend


class CreatePlanRequest(BaseModel):
    home_conversation_id: int
    title: str
    steps: list[StepInput]


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_plan(request: CreatePlanRequest):
    """Crée un plan et ses étapes. Retourne plan_id."""
    db = get_connection()
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO jarvis_plans (home_conversation_id, title, status)
            VALUES (?, ?, 'EN_ATTENTE_CONFIRM')
        """, (request.home_conversation_id, request.title))
        plan_id = cursor.lastrowid

        step_order_to_id: dict[int, int] = {}
        for i, step in enumerate(request.steps, 1):
            dep_id = step_order_to_id.get(step.depends_on_order) \
                     if step.depends_on_order else None
            cursor.execute("""
                INSERT INTO jarvis_plan_steps
                (plan_id, step_order, agent, title, input_message, depends_on)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (plan_id, i, step.agent, step.title, step.input_message, dep_id))
            step_order_to_id[i] = cursor.lastrowid

        db.commit()
        return {"plan_id": plan_id, "status": "EN_ATTENTE_CONFIRM",
                "steps_created": len(request.steps)}
    finally:
        db.close()


@router.post("/{plan_id}/confirm")
def confirm_plan(plan_id: int):
    """Confirme un plan → passe en CONFIRMED → l'exécuteur le prend en charge."""
    db = get_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT status FROM jarvis_plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plan non trouvé")
        if row["status"] != "EN_ATTENTE_CONFIRM":
            raise HTTPException(status_code=400,
                detail=f"Plan déjà en statut '{row['status']}'")
        db.execute("""
            UPDATE jarvis_plans
            SET status = 'CONFIRMED', updated_at = datetime('now')
            WHERE id = ?
        """, (plan_id,))
        db.commit()
        return {"plan_id": plan_id, "status": "CONFIRMED"}
    finally:
        db.close()


@router.get("/{plan_id}")
def get_plan(plan_id: int):
    """Retourne un plan et ses étapes."""
    db = get_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM jarvis_plans WHERE id = ?", (plan_id,))
        plan = cursor.fetchone()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan non trouvé")
        cursor.execute("""
            SELECT * FROM jarvis_plan_steps
            WHERE plan_id = ? ORDER BY step_order
        """, (plan_id,))
        steps = [dict(s) for s in cursor.fetchall()]
        return {"plan": dict(plan), "steps": steps}
    finally:
        db.close()


@router.get("/conversation/{conv_id}")
def get_plans_by_conversation(conv_id: int):
    """Liste les plans liés à une conversation."""
    db = get_connection()
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM jarvis_plans
            WHERE home_conversation_id = ?
            ORDER BY created_at DESC
        """, (conv_id,))
        plans = [dict(p) for p in cursor.fetchall()]
        return {"plans": plans}
    finally:
        db.close()


@router.post("/{plan_id}/retry")
def retry_plan(plan_id: int):
    """Relance les étapes ECHEC/ANNULEE d'un plan bloqué."""
    db = get_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT status FROM jarvis_plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plan non trouvé")
        db.execute("""
            UPDATE jarvis_plan_steps
            SET status = 'EN_ATTENTE', error_message = NULL,
                updated_at = datetime('now')
            WHERE plan_id = ? AND status IN ('ECHEC', 'ANNULEE')
        """, (plan_id,))
        db.execute("""
            UPDATE jarvis_plans
            SET status = 'CONFIRMED', updated_at = datetime('now')
            WHERE id = ?
        """, (plan_id,))
        db.commit()
        return {"plan_id": plan_id, "status": "CONFIRMED",
                "message": "Étapes relancées"}
    finally:
        db.close()


@router.delete("/{plan_id}")
def cancel_plan(plan_id: int):
    """Annule un plan (marque ANNULE + ses étapes EN_ATTENTE → ANNULEE)."""
    db = get_connection()
    try:
        db.execute("""
            UPDATE jarvis_plan_steps
            SET status = 'ANNULEE', updated_at = datetime('now')
            WHERE plan_id = ? AND status IN ('EN_ATTENTE', 'EN_COURS')
        """, (plan_id,))
        db.execute("""
            UPDATE jarvis_plans
            SET status = 'ANNULE', updated_at = datetime('now')
            WHERE id = ?
        """, (plan_id,))
        db.commit()
        return {"plan_id": plan_id, "status": "ANNULE"}
    finally:
        db.close()
