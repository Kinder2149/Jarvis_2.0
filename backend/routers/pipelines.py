from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import json
from backend.schemas.pipeline import StartPipeline, StepValidation
from backend.database import get_connection
from backend.services.pipeline_engine import (
    create_session,
    get_session_with_steps,
    execute_step,
    validate_step as validate_step_service,
    retry_step as retry_step_service
)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"
LOG_PATH = Path(__file__).parent.parent / "data" / "jarvis.log"

def load_config():
    if not CONFIG_PATH.exists():
        return {
            "api_keys": {"openrouter_key": "", "anthropic_key": "", "google_key": ""},
            "model_preferences": {
                "routing": "google/gemini-flash-2.0",
                "structuring": "anthropic/claude-haiku-4-5",
                "code": "anthropic/claude-sonnet-4-5",
                "analysis": "anthropic/claude-opus-4"
            }
        }
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@router.post("/start")
async def start_pipeline(request: StartPipeline):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT path FROM projects WHERE id = ?", (request.project_id,))
    project_row = cursor.fetchone()
    
    if not project_row:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_path = project_row["path"]
    
    session = create_session(
        request.project_id,
        request.workflow_type,
        request.initial_input or "",
        db
    )
    
    config = load_config()
    
    result = await execute_step(session["id"], 0, project_path, db, config)
    
    while result.get("status") == "auto_completed":
        result = await execute_step(session["id"], result["next_step"], project_path, db, config)
    
    session_with_steps = get_session_with_steps(session["id"], db)
    db.close()
    
    return {
        "session": session_with_steps,
        "execution_result": result
    }

@router.get("/{session_id}")
def get_pipeline(session_id: int):
    db = get_connection()
    session = get_session_with_steps(session_id, db)
    db.close()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@router.post("/{session_id}/next")
async def execute_next_step(session_id: int):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    
    if not session_row:
        db.close()
        raise HTTPException(status_code=404, detail="Session not found")
    
    cursor.execute("SELECT path FROM projects WHERE id = ?", (session_row["project_id"],))
    project_row = cursor.fetchone()
    
    if not project_row:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_path = project_row["path"]
    next_step_index = session_row["current_step_index"]
    
    config = load_config()
    
    result = await execute_step(session_id, next_step_index, project_path, db, config)
    
    while result.get("status") == "auto_completed":
        result = await execute_step(session_id, result["next_step"], project_path, db, config)
    
    session_with_steps = get_session_with_steps(session_id, db)
    db.close()
    
    return {
        "session": session_with_steps,
        "execution_result": result
    }

@router.post("/{session_id}/validate/{step_id}")
async def validate_pipeline_step(session_id: int, step_id: int, validation: StepValidation):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT p.path FROM sessions s JOIN projects p ON s.project_id = p.id WHERE s.id = ?", (session_id,))
    project_row = cursor.fetchone()
    project_path = project_row["path"] if project_row else None
    
    result = validate_step_service(session_id, step_id, validation.model_dump(), db, project_path)
    
    if result.get("status") == "validated" and result.get("next_step") is not None:
        if project_path:
            config = load_config()
            exec_result = await execute_step(session_id, result["next_step"], project_path, db, config)
            
            while exec_result.get("status") == "auto_completed":
                exec_result = await execute_step(session_id, exec_result["next_step"], project_path, db, config)
    
    session_with_steps = get_session_with_steps(session_id, db)
    db.close()
    
    return {
        "session": session_with_steps,
        "validation_result": result
    }

@router.post("/{session_id}/retry/{step_id}")
async def retry_pipeline_step(session_id: int, step_id: int):
    db = get_connection()
    
    result = retry_step_service(session_id, step_id, db)
    
    if result.get("status") == "ready_for_retry":
        cursor = db.cursor()
        cursor.execute("SELECT path FROM sessions s JOIN projects p ON s.project_id = p.id WHERE s.id = ?", (session_id,))
        project_row = cursor.fetchone()
        
        if project_row:
            config = load_config()
            exec_result = await execute_step(session_id, result["step_index"], project_row["path"], db, config)
            
            while exec_result.get("status") == "auto_completed":
                exec_result = await execute_step(session_id, exec_result["next_step"], project_row["path"], db, config)
    
    session_with_steps = get_session_with_steps(session_id, db)
    db.close()
    
    return {
        "session": session_with_steps,
        "retry_result": result
    }

@router.post("/{session_id}/abort")
def abort_pipeline(session_id: int):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("UPDATE sessions SET status = ? WHERE id = ?", ("ABORTED", session_id))
    db.commit()
    
    session_with_steps = get_session_with_steps(session_id, db)
    db.close()
    
    return session_with_steps

@router.get("/{session_id}/costs")
def get_pipeline_costs(session_id: int):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT step_name, model_id_chosen, input_tokens, output_tokens
        FROM model_decision_log
        WHERE session_id = ?
    """, (session_id,))
    
    rows = cursor.fetchall()
    db.close()
    
    model_prices = {
        "google/gemini-2.0-flash-001": 0.10,
        "google/gemini-flash-2.0": 0.10,
        "anthropic/claude-haiku-4.5": 1.00,
        "anthropic/claude-haiku-4-5": 1.00,
        "anthropic/claude-sonnet-4.5": 3.00,
        "anthropic/claude-sonnet-4-5": 3.00,
        "anthropic/claude-opus-4": 5.00,
        "anthropic/claude-opus-4.5": 5.00
    }
    
    costs = []
    for row in rows:
        model_id = row["model_id_chosen"]
        price = model_prices.get(model_id, 1.00)
        input_tokens = row["input_tokens"] or 0
        output_tokens = row["output_tokens"] or 0
        cost_usd = (input_tokens / 1e6 * price) + (output_tokens / 1e6 * price)
        
        costs.append({
            "step_name": row["step_name"],
            "model": model_id.split('/')[-1] if '/' in model_id else model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd
        })
    
    return costs

@router.get("/logs")
def get_logs(lines: int = Query(default=100), project_id: int | None = None):
    if not LOG_PATH.exists():
        return {"lines": []}
    
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        
        # Filtrage par project_id si fourni
        if project_id is not None:
            # Récupérer les session_id du projet
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE project_id = ?", (project_id,))
            session_ids = [str(row["id"]) for row in cursor.fetchall()]
            conn.close()
            
            if not session_ids:
                return {"lines": []}
            
            # Filtrer les lignes contenant ces session_id
            filtered_lines = []
            for line in all_lines:
                for session_id in session_ids:
                    if f"session {session_id}" in line.lower() or f"session_id={session_id}" in line.lower():
                        filtered_lines.append(line)
                        break
            
            last_lines = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
        else:
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {"lines": [line.rstrip() for line in last_lines]}
    
    except Exception:
        return {"lines": []}
