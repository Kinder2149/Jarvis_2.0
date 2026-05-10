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

@router.get("/{project_id}/local-list")
def list_local_files(project_id: int):
    """Liste les fichiers du dossier local du projet (récursif, profondeur max 3)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    project_path = row["path"]
    
    if not project_path:
        return {"files": [], "error": "Aucun dossier défini"}
    
    project_dir = Path(project_path)
    if not project_dir.exists() or not project_dir.is_dir():
        return {"files": [], "error": "Le dossier n'existe pas"}
    
    # Exclusions
    exclude_names = {"__pycache__", ".git", "node_modules", ".env"}
    exclude_extensions = {".pyc"}
    
    files = []
    
    def scan_directory(directory: Path, current_depth: int = 0, max_depth: int = 3):
        if current_depth > max_depth:
            return
        
        try:
            for item in directory.iterdir():
                # Exclure
                if item.name in exclude_names:
                    continue
                if item.suffix in exclude_extensions:
                    continue
                
                relative_path = item.relative_to(local_dir)
                
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(relative_path),
                        "size": item.stat().st_size,
                        "type": "file"
                    })
                elif item.is_dir():
                    files.append({
                        "name": item.name,
                        "path": str(relative_path),
                        "size": 0,
                        "type": "dir"
                    })
                    scan_directory(item, current_depth + 1, max_depth)
        except PermissionError:
            pass
    
    scan_directory(project_dir)
    
    return {"files": files}
