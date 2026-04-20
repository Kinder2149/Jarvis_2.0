from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import get_connection

router = APIRouter(prefix="/config", tags=["config"])

class ConfigValue(BaseModel):
    value: str

@router.get("/{key}")
def get_config(key: str):
    """Récupère une valeur de configuration depuis app_config"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value, category FROM app_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Configuration '{key}' non trouvée")
    
    return {
        "key": key,
        "value": row["value"] or "",
        "category": row["category"]
    }

@router.post("/{key}")
def update_config(key: str, data: ConfigValue):
    """Met à jour une valeur de configuration dans app_config"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Vérifier si la clé existe
    cursor.execute("SELECT key FROM app_config WHERE key = ?", (key,))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute(
            "UPDATE app_config SET value = ?, updated_at = datetime('now') WHERE key = ?",
            (data.value, key)
        )
    else:
        cursor.execute(
            "INSERT INTO app_config (key, value, category) VALUES (?, ?, 'general')",
            (key, data.value)
        )
    
    conn.commit()
    conn.close()
    
    return {"message": f"Configuration '{key}' mise à jour", "value": data.value}


@router.get("/profil_utilisateur")
def get_profil_utilisateur():
    """Lit le contenu de PROFIL_UTILISATEUR.md depuis le dossier METHODO."""
    from pathlib import Path
    
    # Lire methodo_path depuis la DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = 'methodo_path'")
    row = cursor.fetchone()
    conn.close()
    
    methodo_path = (row["value"] if row and row["value"] else "") or "C:\\DEV\\METHODO"
    profil_path = Path(methodo_path) / "informations utilisateur" / "PROFIL_UTILISATEUR.md"
    
    if not profil_path.exists():
        return {"content": "", "path": str(profil_path), "exists": False}
    
    try:
        content = profil_path.read_text(encoding="utf-8")
        return {"content": content, "path": str(profil_path), "exists": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture profil : {e}")


@router.post("/profil_utilisateur")
def save_profil_utilisateur(data: ConfigValue):
    """Écrit le contenu dans PROFIL_UTILISATEUR.md."""
    from pathlib import Path
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = 'methodo_path'")
    row = cursor.fetchone()
    conn.close()
    
    methodo_path = (row["value"] if row and row["value"] else "") or "C:\\DEV\\METHODO"
    profil_path = Path(methodo_path) / "informations utilisateur" / "PROFIL_UTILISATEUR.md"
    
    try:
        profil_path.parent.mkdir(parents=True, exist_ok=True)
        profil_path.write_text(data.value, encoding="utf-8")
        return {"message": "Profil sauvegardé", "path": str(profil_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur écriture profil : {e}")
