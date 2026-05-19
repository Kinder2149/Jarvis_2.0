from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.database import get_connection
from backend.services.pipeline_engine import create_session, get_session_with_steps
from backend.services.atelier_service import export_as_zip
from pathlib import Path
import io
import time
import sqlite3

router = APIRouter(prefix="/atelier", tags=["atelier"])


class ProspectCreate(BaseModel):
    nom: str
    categorie: str = "restauration"
    url: str | None = None


class ProspectUpdate(BaseModel):
    statut: str | None = None
    demo_url: str | None = None
    notes: str | None = None
    score: str | None = None
    proposition: str | None = None
    fiche: str | None = None
    form_data: str | None = None


@router.get("/prospects")
def list_prospects():
    """Liste tous les prospects avec leur session_status si une session existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*,
               s.status AS session_status
        FROM prospects p
        LEFT JOIN sessions s ON s.id = p.session_id
        ORDER BY p.updated_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    prospects = []
    for row in rows:
        prospects.append({
            "id": row["id"],
            "session_id": row["session_id"],
            "session_status": row["session_status"],
            "nom": row["nom"],
            "categorie": row["categorie"],
            "url": row["url"],
            "statut": row["statut"],
            "score": row["score"],
            "form_data": row["form_data"],
            "fiche": row["fiche"],
            "proposition": row["proposition"],
            "demo_path": row["demo_path"],
            "demo_url": row["demo_url"],
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })
    
    return prospects


@router.post("/prospects", status_code=201)
def create_prospect(data: ProspectCreate):
    """Crée un nouveau prospect."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO prospects (nom, categorie, url) VALUES (?, ?, ?)",
        (data.nom, data.categorie, data.url)
    )
    conn.commit()
    prospect_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,))
    row = cursor.fetchone()
    conn.close()
    
    return {
        "id": row["id"],
        "nom": row["nom"],
        "categorie": row["categorie"],
        "url": row["url"],
        "statut": row["statut"],
        "created_at": row["created_at"]
    }


@router.get("/prospects/{prospect_id}")
def get_prospect(prospect_id: int):
    """Récupère un prospect avec sa session si elle existe."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    prospect = {
        "id": row["id"],
        "session_id": row["session_id"],
        "nom": row["nom"],
        "categorie": row["categorie"],
        "url": row["url"],
        "statut": row["statut"],
        "score": row["score"],
        "form_data": row["form_data"],
        "fiche": row["fiche"],
        "proposition": row["proposition"],
        "demo_path": row["demo_path"],
        "demo_url": row["demo_url"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }
    
    session = None
    if row["session_id"]:
        session = get_session_with_steps(row["session_id"], conn)
    
    conn.close()
    
    return {
        "prospect": prospect,
        "session": session
    }


@router.patch("/prospects/{prospect_id}")
def update_prospect(prospect_id: int, data: ProspectUpdate):
    """Met à jour un prospect."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    # Construire la requête UPDATE dynamiquement
    updates = []
    values = []
    
    if data.statut is not None:
        updates.append("statut = ?")
        values.append(data.statut)
    if data.demo_url is not None:
        updates.append("demo_url = ?")
        values.append(data.demo_url)
    if data.notes is not None:
        updates.append("notes = ?")
        values.append(data.notes)
    if data.score is not None:
        updates.append("score = ?")
        values.append(data.score)
    if data.proposition is not None:
        updates.append("proposition = ?")
        values.append(data.proposition)
    if data.fiche is not None:
        updates.append("fiche = ?")
        values.append(data.fiche)
    if data.form_data is not None:
        updates.append("form_data = ?")
        values.append(data.form_data)
    
    if updates:
        updates.append("updated_at = datetime('now')")
        values.append(prospect_id)
        
        query = f"UPDATE prospects SET {', '.join(updates)} WHERE id = ?"
        
        # Retry avec timeout pour gérer database locked
        max_retries = 3
        for attempt in range(max_retries):
            try:
                cursor.execute(query, values)
                conn.commit()
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    conn.close()
                    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    cursor.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,))
    updated_row = cursor.fetchone()
    conn.close()
    
    return {
        "id": updated_row["id"],
        "nom": updated_row["nom"],
        "categorie": updated_row["categorie"],
        "url": updated_row["url"],
        "statut": updated_row["statut"],
        "score": updated_row["score"],
        "form_data": updated_row["form_data"],
        "fiche": updated_row["fiche"],
        "proposition": updated_row["proposition"],
        "demo_path": updated_row["demo_path"],
        "demo_url": updated_row["demo_url"],
        "notes": updated_row["notes"],
        "updated_at": updated_row["updated_at"]
    }


@router.delete("/prospects/{prospect_id}", status_code=204)
def delete_prospect(prospect_id: int):
    """Supprime un prospect et sa session pipeline associée en cascade."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT session_id FROM prospects WHERE id = ?", (prospect_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    session_id = row["session_id"]
    
    # Supprimer en cascade : steps → session → prospect
    if session_id:
        cursor.execute("DELETE FROM pipeline_steps WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    
    cursor.execute("DELETE FROM prospects WHERE id = ?", (prospect_id,))
    conn.commit()
    conn.close()
    
    return None


@router.delete("/prospects", status_code=200)
def delete_all_prospects():
    """Supprime TOUS les prospects et leurs sessions en cascade."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Récupérer tous les prospects avec leurs sessions
    cursor.execute("SELECT id, session_id FROM prospects")
    prospects = cursor.fetchall()
    
    deleted_count = 0
    session_ids = set()
    
    for prospect in prospects:
        if prospect["session_id"]:
            session_ids.add(prospect["session_id"])
    
    # Supprimer en cascade : steps → sessions → prospects
    for session_id in session_ids:
        cursor.execute("DELETE FROM pipeline_steps WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    
    cursor.execute("DELETE FROM prospects")
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {"deleted": deleted_count, "message": f"{deleted_count} prospect(s) supprimé(s)"}


@router.post("/prospects/{prospect_id}/start")
async def start_prospect_pipeline(prospect_id: int):
    """Lance le pipeline atelier pour un prospect."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Vérifier que le prospect existe
    cursor.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,))
    prospect_row = cursor.fetchone()
    
    if not prospect_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    # Vérifier qu'il n'a pas déjà de session active
    if prospect_row["session_id"]:
        cursor.execute(
            "SELECT status FROM sessions WHERE id = ?",
            (prospect_row["session_id"],)
        )
        session_row = cursor.fetchone()
        if session_row and session_row["status"] not in ("COMPLETED", "ABORTED", "FAILED"):
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Ce prospect a déjà une session active"
            )
    
    # Récupérer ou créer le projet système Atelier
    cursor.execute("SELECT id FROM projects WHERE path = ?", ("__atelier__",))
    project_row = cursor.fetchone()
    
    if not project_row:
        cursor.execute(
            "INSERT INTO projects (name, path, module_type) VALUES (?, ?, ?)",
            ("Atelier Connecté", "__atelier__", "code")
        )
        conn.commit()
        project_id = cursor.lastrowid
    else:
        project_id = project_row["id"]
    
    # Créer la session
    form_data_json = prospect_row["form_data"] or "{}"
    session = create_session(
        project_id,
        "atelier_restauration",
        form_data_json,
        conn
    )
    
    # Mettre à jour le prospect
    cursor.execute(
        "UPDATE prospects SET session_id = ?, statut = ?, updated_at = datetime('now') WHERE id = ?",
        (session["id"], "en_analyse", prospect_id)
    )
    conn.commit()
    
    # Charger config et exécuter le premier step
    from backend.database import load_config
    from backend.services.pipeline_engine import execute_step
    
    config = load_config()
    project_path = "__atelier__"
    
    result = await execute_step(session["id"], 0, project_path, conn, config)
    
    # Boucle auto-completion si nécessaire (max 15 steps pour éviter boucle infinie)
    MAX_AUTO_STEPS = 15
    auto_count = 0
    while result.get("status") == "auto_completed" and auto_count < MAX_AUTO_STEPS:
        auto_count += 1
        result = await execute_step(session["id"], result["next_step"], project_path, conn, config)
    
    conn.close()
    
    return {
        "session_id": session["id"],
        "prospect_id": prospect_id,
        "execution_result": result
    }


@router.get("/prospects/{prospect_id}/files")
def list_prospect_files(prospect_id: int):
    """Liste les fichiers de la démo générée."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT demo_path FROM prospects WHERE id = ?", (prospect_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    if not row["demo_path"]:
        return {"files": []}
    
    demo_dir = Path(row["demo_path"])
    if not demo_dir.exists():
        return {"files": []}
    
    files = []
    for file_path in demo_dir.iterdir():
        if file_path.is_file():
            size_kb = file_path.stat().st_size / 1024
            files.append({
                "name": file_path.name,
                "size_kb": round(size_kb, 2)
            })
    
    return {"files": files}


@router.get("/prospects/{prospect_id}/export")
def export_prospect_demo(prospect_id: int):
    """Exporte la démo en ZIP."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT demo_path FROM prospects WHERE id = ?", (prospect_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    if not row["demo_path"]:
        raise HTTPException(status_code=404, detail="Aucune démo générée pour ce prospect")
    
    # Extraire le slug du demo_path
    demo_path = Path(row["demo_path"])
    slug = demo_path.name
    
    try:
        zip_bytes = export_as_zip(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dossier démo introuvable")
    
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=demo-{slug}.zip"}
    )
