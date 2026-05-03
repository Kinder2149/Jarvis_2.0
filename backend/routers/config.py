from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import httpx
from backend.schemas.config import Config
from backend.database import get_connection

router = APIRouter(prefix="/config", tags=["config"])

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"
CONTEXTS_DIR = Path(__file__).parent.parent / "data" / "contexts"

class ConfigValue(BaseModel):
    value: str

class TestConnectionRequest(BaseModel):
    provider: str

@router.get("")
def get_full_config():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_config WHERE category = 'api_keys'")
    rows = cursor.fetchall()
    conn.close()
    
    api_keys = {}
    for row in rows:
        key_name = row["key"]
        value = row["value"]
        if value and len(value) > 4:
            api_keys[key_name] = "..." + value[-4:]
        else:
            api_keys[key_name] = value
    
    if not api_keys:
        api_keys = {"openrouter_key": "", "anthropic_key": "", "google_key": ""}
    
    from pathlib import Path as _Path
    _env_file = _Path(__file__).parent.parent / ".env"
    if _env_file.exists():
        _env_map = {
            "OPENROUTER_KEY": "openrouter_key",
            "ANTHROPIC_KEY": "anthropic_key",
            "GOOGLE_KEY": "google_key",
            "WEB_SEARCH_KEY": "web_search_key",
        }
        for line in _env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            env_k, env_v = line.split("=", 1)
            db_k = _env_map.get(env_k.strip())
            if db_k and env_v.strip() and not api_keys.get(db_k):
                v = env_v.strip()
                api_keys[db_k] = "..." + v[-4:] if len(v) > 4 else v
    
    model_preferences = {
        "routing": "google/gemini-2.5-flash",
        "structuring": "google/gemini-2.5-flash",
        "code": "anthropic/claude-haiku-4.5",
        "analysis": "anthropic/claude-sonnet-4.5"
    }
    
    chat_config = {
        "model": "anthropic/claude-sonnet-4.5",
        "methodo_path": "C:\\DEV\\METHODO",
        "session_note": "",
        "system_prompt_preset": ""
    }
    
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_file = json.load(f)
            if "model_preferences" in config_file:
                model_preferences = config_file["model_preferences"]
            if "chat" in config_file:
                chat_config = config_file["chat"]
    
    return {
        "api_keys": api_keys,
        "model_preferences": model_preferences,
        "chat": chat_config
    }

@router.post("")
def save_config(config: Config):
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"📥 [SAVE_CONFIG] Payload reçu: {config.model_dump()}")
    
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config_dict = config.model_dump()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for key_name, value in config_dict.get("api_keys", {}).items():
        if value.startswith("..."):
            continue
        
        cursor.execute("""
            INSERT INTO app_config (key, value, category, updated_at)
            VALUES (?, ?, 'api_keys', datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key_name, value))
    
    conn.commit()
    conn.close()
    
    existing_chat = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            existing_config = json.load(f)
            existing_chat = existing_config.get("chat", {})
    
    chat_to_save = config_dict.get("chat") if config_dict.get("chat") is not None else existing_chat
    
    config_file = {
        "model_preferences": config_dict.get("model_preferences", {}),
        "chat": chat_to_save
    }
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_file, f, indent=2)
    
    return {"message": "Configuration sauvegardée"}

@router.post("/test")
async def test_connection(request: TestConnectionRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_config WHERE category = 'api_keys'")
    rows = cursor.fetchall()
    conn.close()
    
    api_keys = {row["key"]: row["value"] for row in rows}
    
    if request.provider == "openrouter":
        key = api_keys.get("openrouter_key", "")
        if not key:
            raise HTTPException(status_code=400, detail="Clé OpenRouter manquante")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "JARVIS"
                    },
                    json={
                        "model": "anthropic/claude-haiku-4-5",
                        "messages": [{"role": "user", "content": "Réponds ok"}]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"status": "success", "message": "Connexion réussie"}
                else:
                    return {"status": "error", "message": f"Erreur {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    elif request.provider == "anthropic":
        key = api_keys.get("anthropic_key", "")
        if not key:
            raise HTTPException(status_code=400, detail="Clé Anthropic manquante")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-haiku-4-5",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "ok"}]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"status": "success", "message": "Connexion réussie"}
                else:
                    return {"status": "error", "message": f"Erreur {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    elif request.provider == "google":
        key = api_keys.get("google_key", "")
        if not key:
            raise HTTPException(status_code=400, detail="Clé Google manquante")
        
        return {"status": "success", "message": "Test Google non implémenté (Phase 2)"}
    
    else:
        raise HTTPException(status_code=400, detail="Provider inconnu")

@router.get("/models/available")
def get_available_models():
    return {
        "routing": [
            "google/gemini-2.5-flash",
            "meta-llama/llama-3.3-70b-instruct:free"
        ],
        "structuring": [
            "google/gemini-2.5-flash",
            "anthropic/claude-haiku-4.5"
        ],
        "code": [
            "anthropic/claude-haiku-4.5",
            "anthropic/claude-sonnet-4.5",
            "deepseek/deepseek-r1-0528"
        ],
        "analysis": [
            "anthropic/claude-sonnet-4.5",
            "anthropic/claude-opus-4.5",
            "google/gemini-2.5-pro"
        ]
    }

@router.get("/regles_globales")
def get_regles_globales():
    """Lit les règles globales depuis le fichier .md."""
    regles_file = CONTEXTS_DIR / "regles_globales.md"
    value = regles_file.read_text(encoding="utf-8") if regles_file.exists() else ""
    return {"value": value}

@router.post("/regles_globales")
def save_regles_globales(body: dict):
    """Sauvegarde les règles globales dans le fichier .md."""
    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)
    regles_file = CONTEXTS_DIR / "regles_globales.md"
    regles_file.write_text(body.get("value", ""), encoding="utf-8")
    return {"ok": True}

@router.get("/global_context")
def get_global_context():
    """Lit le contexte global depuis le fichier .md."""
    context_file = CONTEXTS_DIR / "global_context.md"
    value = context_file.read_text(encoding="utf-8") if context_file.exists() else ""
    return {"value": value}

@router.post("/global_context")
def save_global_context(body: dict):
    """Sauvegarde le contexte global dans le fichier .md."""
    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)
    context_file = CONTEXTS_DIR / "global_context.md"
    context_file.write_text(body.get("value", ""), encoding="utf-8")
    return {"ok": True}

@router.post("/backup")
def backup_database():
    import shutil
    from datetime import datetime
    
    db_path = Path(__file__).parent.parent / "data" / "jarvis.db"
    backup_dir = Path(__file__).parent.parent / "data" / "backups"
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Base de données introuvable")
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"jarvis_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    
    shutil.copy2(db_path, backup_path)
    
    backups = sorted(backup_dir.glob("jarvis_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    for old_backup in backups[5:]:
        old_backup.unlink()
    
    return {"success": True, "filename": backup_filename}

@router.get("/clients_export_path")
def get_clients_export_path():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = 'clients_export_path'")
    row = cursor.fetchone()
    conn.close()
    return {"value": row["value"] if row else "C:/DEV/PROJETS/Clients"}

@router.post("/clients_export_path")
def save_clients_export_path(body: dict):
    value = body.get("value", "")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO app_config (key, value, category, updated_at) VALUES ('clients_export_path', ?, 'paths', datetime('now'))",
        (value,)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@router.get("/profil_utilisateur")
def get_profil_utilisateur():
    """Lit le profil utilisateur depuis le fichier .md."""
    profil_file = CONTEXTS_DIR / "profil_utilisateur.md"
    if profil_file.exists():
        content = profil_file.read_text(encoding="utf-8")
        return {"content": content, "exists": True}
    return {"content": "", "exists": False}

@router.post("/profil_utilisateur")
def save_profil_utilisateur(data: ConfigValue):
    """Sauvegarde le profil utilisateur dans le fichier .md."""
    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)
    profil_file = CONTEXTS_DIR / "profil_utilisateur.md"
    profil_file.write_text(data.value, encoding="utf-8")
    return {"message": "Profil sauvegardé"}

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
