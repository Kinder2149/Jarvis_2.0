from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import get_connection
from backend.services.file_service import read_file, compute_diff, apply_files, list_project_files
from pathlib import Path

router = APIRouter(prefix="/files", tags=["files"])

class ReadFileRequest(BaseModel):
    filepath: str

class DiffRequest(BaseModel):
    filepath: str
    new_content: str

class ApplyFilesRequest(BaseModel):
    changes: list[dict]

@router.get("/{project_id}/list")
def list_files(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    project_path = row["path"]
    files = list_project_files(project_path)
    
    return {"files": files}

@router.post("/{project_id}/read")
def read_project_file(project_id: int, request: ReadFileRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    project_path = Path(row["path"])
    file_path = project_path / request.filepath
    
    content = read_file(str(file_path))
    return {"content": content}

@router.post("/{project_id}/diff")
def get_file_diff(project_id: int, request: DiffRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    project_path = Path(row["path"])
    file_path = project_path / request.filepath
    
    original = read_file(str(file_path))
    diff = compute_diff(original, request.new_content, request.filepath)
    
    return {"diff": diff}

@router.post("/{project_id}/apply")
def apply_file_changes(project_id: int, request: ApplyFilesRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    project_path = Path(row["path"])
    
    changes_with_full_paths = []
    for change in request.changes:
        full_path = project_path / change["path"]
        changes_with_full_paths.append({
            "path": str(full_path),
            "content": change["content"]
        })
    
    success = apply_files(changes_with_full_paths)
    
    if not success:
        raise HTTPException(status_code=500, detail="Échec de l'application des modifications")
    
    return {"success": True}
