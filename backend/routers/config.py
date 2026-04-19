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
