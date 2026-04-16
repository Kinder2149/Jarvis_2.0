from pathlib import Path
import json
from datetime import datetime
from backend.database import get_connection
from backend.services.context_manager import build_context_envelope, inject_into_template, write_cloture_docs
from backend.services.model_router import get_model_id, call_model

PIPELINES_PATH = Path(__file__).parent.parent / "data" / "pipelines.json"
PROMPTS_PATH = Path(__file__).parent.parent / "data" / "prompts.json"

def load_pipeline_definition(workflow_type: str) -> dict:
    if not PIPELINES_PATH.exists():
        return {}
    
    with open(PIPELINES_PATH, "r", encoding="utf-8") as f:
        pipelines = json.load(f)
    
    return pipelines.get(workflow_type, {})

def load_prompt_template(prompt_key: str) -> str:
    if not PROMPTS_PATH.exists():
        return ""
    
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    return prompts.get(prompt_key, "")

def create_session(project_id: int, workflow_type: str, initial_input: str, db) -> dict:
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO sessions (project_id, workflow_type, status, current_step_index) VALUES (?, ?, ?, ?)",
        (project_id, workflow_type, "CREATED", 0)
    )
    session_id = cursor.lastrowid
    
    pipeline_def = load_pipeline_definition(workflow_type)
    steps = pipeline_def.get("steps", [])
    
    for step in steps:
        cursor.execute(
            """INSERT INTO pipeline_steps 
            (session_id, step_index, step_name, step_display_name, model_type, status, requires_validation, input_data, output_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                step["index"],
                step["name"],
                step["display_name"],
                step["model_type"],
                "PENDING",
                1 if step.get("requires_validation", False) else 0,
                initial_input if step["index"] == 0 else None,
                step.get("output_type", "text")
            )
        )
    
    db.commit()
    
    return {
        "id": session_id,
        "project_id": project_id,
        "workflow_type": workflow_type,
        "status": "CREATED",
        "current_step_index": 0
    }

def get_session_with_steps(session_id: int, db) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    
    if not session_row:
        return None
    
    cursor.execute(
        "SELECT * FROM pipeline_steps WHERE session_id = ? ORDER BY step_index",
        (session_id,)
    )
    steps_rows = cursor.fetchall()
    
    session = {
        "id": session_row["id"],
        "project_id": session_row["project_id"],
        "workflow_type": session_row["workflow_type"],
        "status": session_row["status"],
        "current_step_index": session_row["current_step_index"],
        "created_at": session_row["created_at"],
        "steps": []
    }
    
    for step_row in steps_rows:
        session["steps"].append({
            "id": step_row["id"],
            "session_id": step_row["session_id"],
            "step_index": step_row["step_index"],
            "step_name": step_row["step_name"],
            "step_display_name": step_row["step_display_name"],
            "model_type": step_row["model_type"],
            "model_used": step_row["model_used"],
            "status": step_row["status"],
            "input_data": step_row["input_data"],
            "output_data": step_row["output_data"],
            "requires_validation": bool(step_row["requires_validation"]),
            "validated_at": step_row["validated_at"],
            "created_at": step_row["created_at"],
            "output_type": dict(step_row).get("output_type", "text")
        })
    
    return session

def _extract_json_safe(text: str) -> dict:
    """Extrait un JSON même entouré de markdown (```json ... ```)."""
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        return json.loads(text[start:end])
    except Exception:
        return {}


async def execute_step(session_id: int, step_index: int, project_path: str, db, config: dict) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    
    if not session_row:
        return {"status": "error", "error": "Session not found"}
    
    cursor.execute(
        "SELECT * FROM pipeline_steps WHERE session_id = ? AND step_index = ?",
        (session_id, step_index)
    )
    step_row = cursor.fetchone()
    
    if not step_row:
        return {"status": "error", "error": "Step not found"}
    
    cursor.execute(
        "UPDATE pipeline_steps SET status = ? WHERE id = ?",
        ("RUNNING", step_row["id"])
    )
    cursor.execute(
        "UPDATE sessions SET status = ?, current_step_index = ? WHERE id = ?",
        ("RUNNING", step_index, session_id)
    )
    db.commit()
    
    try:
        pipeline_def = load_pipeline_definition(session_row["workflow_type"])
        steps_config = pipeline_def.get("steps", [])
        step_config = next((s for s in steps_config if s["index"] == step_index), None)
        
        if not step_config:
            raise Exception("Step configuration not found")
        
        cursor.execute(
            "SELECT step_name, output_data FROM pipeline_steps WHERE session_id = ? AND step_index < ? AND status = 'COMPLETED'",
            (session_id, step_index)
        )
        previous_rows = cursor.fetchall()
        previous_outputs = {row["step_name"]: row["output_data"] for row in previous_rows}
        
        cursor.execute(
            "SELECT input_data FROM pipeline_steps WHERE session_id = ? AND step_index = 0",
            (session_id,)
        )
        initial_input_row = cursor.fetchone()
        user_input = initial_input_row["input_data"] if initial_input_row else ""
        
        envelope = build_context_envelope(step_config, project_path, previous_outputs, user_input)
        
        prompt_template = load_prompt_template(step_config["prompt_key"])
        prompt = inject_into_template(prompt_template, envelope)
        
        model_id = get_model_id(step_config["model_type"], config)
        
        messages = [{"role": "user", "content": prompt}]
        
        output = await call_model(
            model_id,
            messages,
            config.get("api_keys", {}),
            session_id,
            step_config["name"],
            step_config["model_type"],
            db
        )
        
        cursor.execute(
            "UPDATE pipeline_steps SET output_data = ?, model_used = ? WHERE id = ?",
            (output, model_id, step_row["id"])
        )
        db.commit()
        
        # Si step cloture : écrire automatiquement les docs projet
        if step_config.get("name") == "cloture" and project_path:
            cloture_data = _extract_json_safe(output)
            if cloture_data:
                write_cloture_docs(cloture_data, project_path)
        
        if step_config.get("requires_validation", False):
            cursor.execute(
                "UPDATE pipeline_steps SET status = ? WHERE id = ?",
                ("WAITING_VALIDATION", step_row["id"])
            )
            cursor.execute(
                "UPDATE sessions SET status = ? WHERE id = ?",
                ("WAITING_VALIDATION", session_id)
            )
            db.commit()
            
            return {"status": "waiting_validation", "step_id": step_row["id"], "output": output}
        
        else:
            cursor.execute(
                "UPDATE pipeline_steps SET status = ? WHERE id = ?",
                ("COMPLETED", step_row["id"])
            )
            
            total_steps = len(steps_config)
            if step_index == total_steps - 1:
                cursor.execute(
                    "UPDATE sessions SET status = ? WHERE id = ?",
                    ("COMPLETED", session_id)
                )
                db.commit()
                return {"status": "completed", "output": output}
            else:
                cursor.execute(
                    "UPDATE sessions SET current_step_index = ? WHERE id = ?",
                    (step_index + 1, session_id)
                )
                db.commit()
                return {"status": "auto_completed", "next_step": step_index + 1, "output": output}
    
    except Exception as e:
        cursor.execute(
            "UPDATE pipeline_steps SET status = ?, error_message = ? WHERE id = ?",
            ("FAILED", str(e), step_row["id"])
        )
        cursor.execute(
            "UPDATE sessions SET status = ? WHERE id = ?",
            ("FAILED", session_id)
        )
        db.commit()
        
        return {"status": "failed", "error": str(e)}

def validate_step(session_id: int, step_id: int, validation: dict, db, project_path: str = None) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM pipeline_steps WHERE id = ?", (step_id,))
    step_row = cursor.fetchone()
    
    if not step_row:
        return {"status": "error", "error": "Step not found"}
    
    if not validation.get("approved", False):
        cursor.execute(
            "UPDATE sessions SET status = ? WHERE id = ?",
            ("ABORTED", session_id)
        )
        db.commit()
        return {"status": "aborted"}
    
    edited_output = validation.get("edited_output")
    if edited_output:
        cursor.execute(
            "UPDATE pipeline_steps SET output_data = ? WHERE id = ?",
            (edited_output, step_id)
        )
    
    cursor.execute(
        "UPDATE pipeline_steps SET status = ?, validated_at = ? WHERE id = ?",
        ("COMPLETED", datetime.now().isoformat(), step_id)
    )
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    
    pipeline_def = load_pipeline_definition(session_row["workflow_type"])
    total_steps = len(pipeline_def.get("steps", []))
    
    if step_row["step_name"] == "cloture" and project_path:
        _write_cloture_docs(edited_output or step_row["output_data"], project_path)
    
    if step_row["step_index"] == total_steps - 1:
        cursor.execute(
            "UPDATE sessions SET status = ? WHERE id = ?",
            ("COMPLETED", session_id)
        )
        db.commit()
        return {"status": "completed"}
    else:
        cursor.execute(
            "UPDATE sessions SET status = ?, current_step_index = ? WHERE id = ?",
            ("RUNNING", step_row["step_index"] + 1, session_id)
        )
        db.commit()
        return {"status": "validated", "next_step": step_row["step_index"] + 1}

def retry_step(session_id: int, step_id: int, db) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM pipeline_steps WHERE id = ?", (step_id,))
    step_row = cursor.fetchone()
    
    if not step_row:
        return {"status": "error", "error": "Step not found"}
    
    cursor.execute(
        "UPDATE pipeline_steps SET status = ?, output_data = NULL, error_message = NULL WHERE id = ?",
        ("PENDING", step_id)
    )
    cursor.execute(
        "UPDATE sessions SET status = ?, current_step_index = ? WHERE id = ?",
        ("RUNNING", step_row["step_index"], session_id)
    )
    db.commit()
    
    return {"status": "ready_for_retry", "step_index": step_row["step_index"]}
