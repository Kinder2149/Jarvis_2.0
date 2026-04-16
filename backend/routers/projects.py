from fastapi import APIRouter, HTTPException
from pathlib import Path
from backend.schemas.project import Project, ProjectCreate
from backend.database import get_connection
from backend.services.file_service import parse_projet_contexte

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("")
def list_projects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    projects = []
    for row in rows:
        local_path = row["local_path"] if "local_path" in row.keys() else None
        projects.append({
            "id": row["id"],
            "name": row["name"],
            "path": row["path"],
            "type": row["type"],
            "local_path": local_path,
            "has_projet_contexte": Path(row["path"]).joinpath("PROJET_CONTEXTE.md").exists(),
            "created_at": row["created_at"]
        })
    
    return projects

@router.post("")
def create_project(project: ProjectCreate):
    path = Path(project.path)
    if not path.exists():
        raise HTTPException(status_code=400, detail="Le chemin spécifié n'existe pas")
    
    name = project.name
    type_project = project.type
    has_projet_contexte = path.joinpath("PROJET_CONTEXTE.md").exists()
    
    if has_projet_contexte:
        sections = parse_projet_contexte(str(path))
        if "1" in sections:
            content = sections["1"]
            for line in content.split("\n"):
                if "Nom" in line and "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        name = parts[2].strip()
                elif "Type" in line and "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        type_project = parts[2].strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        local_path = project.local_path
        cursor.execute(
            "INSERT INTO projects (name, path, type, local_path) VALUES (?, ?, ?, ?)",
            (name, str(path), type_project, local_path)
        )
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": project_id,
            "name": name,
            "path": str(path),
            "type": type_project,
            "local_path": local_path,
            "has_projet_contexte": has_projet_contexte,
            "created_at": ""
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Erreur lors de la création: {str(e)}")

@router.get("/{project_id}")
def get_project(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    cursor.execute(
        "SELECT * FROM sessions WHERE project_id = ? AND status NOT IN ('COMPLETED', 'ABORTED') ORDER BY created_at DESC LIMIT 1",
        (project_id,)
    )
    session_row = cursor.fetchone()
    conn.close()
    
    local_path = row["local_path"] if "local_path" in row.keys() else None
    project_data = {
        "id": row["id"],
        "name": row["name"],
        "path": row["path"],
        "type": row["type"],
        "local_path": local_path,
        "has_projet_contexte": Path(row["path"]).joinpath("PROJET_CONTEXTE.md").exists(),
        "created_at": row["created_at"]
    }
    
    if session_row:
        project_data["active_session"] = {
            "id": session_row["id"],
            "workflow_type": session_row["workflow_type"],
            "status": session_row["status"],
            "current_step_index": session_row["current_step_index"]
        }
    
    return project_data

@router.delete("/{project_id}")
def delete_project(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Projet supprimé"}

@router.get("/{project_id}/active-session")
def get_active_session(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sessions WHERE project_id = ? AND status NOT IN ('COMPLETED', 'ABORTED') ORDER BY created_at DESC LIMIT 1",
        (project_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "workflow_type": row["workflow_type"],
        "status": row["status"],
        "current_step_index": row["current_step_index"],
        "created_at": row["created_at"]
    }

@router.get("/{project_id}/sessions")
def get_project_sessions(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT s.*, COUNT(ps.id) as total_steps FROM sessions s LEFT JOIN pipeline_steps ps ON s.id = ps.session_id WHERE s.project_id = ? GROUP BY s.id ORDER BY s.created_at DESC",
        (project_id,)
    )
    rows = cursor.fetchall()
    
    # Table de prix modèles ($/M tokens)
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
    
    sessions = []
    for row in rows:
        session_id = row["id"]
        
        # Calculer coût total pour cette session
        cursor.execute(
            "SELECT model_id_chosen, input_tokens, output_tokens FROM model_decision_log WHERE session_id = ?",
            (session_id,)
        )
        log_rows = cursor.fetchall()
        
        total_cost_usd = 0.0
        for log_row in log_rows:
            model_id = log_row["model_id_chosen"]
            price = model_prices.get(model_id, 1.00)
            input_tokens = log_row["input_tokens"] or 0
            output_tokens = log_row["output_tokens"] or 0
            total_cost_usd += (input_tokens + output_tokens) / 1_000_000 * price
        
        sessions.append({
            "id": row["id"],
            "project_id": row["project_id"],
            "workflow_type": row["workflow_type"],
            "status": row["status"],
            "current_step_index": row["current_step_index"],
            "total_steps": row["total_steps"],
            "created_at": row["created_at"],
            "total_cost_usd": round(total_cost_usd, 4)
        })
    
    conn.close()
    return sessions

@router.patch("/{project_id}")
def update_project(project_id: int, local_path: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    cursor.execute(
        "UPDATE projects SET local_path = ? WHERE id = ?",
        (local_path, project_id)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Projet mis à jour", "local_path": local_path}
