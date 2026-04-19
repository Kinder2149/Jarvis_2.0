from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import httpx
from backend.schemas.config import Config
from backend.database import get_connection

router = APIRouter(prefix="/config", tags=["config"])

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"

class TestConnectionRequest(BaseModel):
    provider: str

@router.get("")
def get_config():
    # Lire api_keys depuis SQLite
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM app_config WHERE category = 'api_keys'")
    rows = cursor.fetchall()
    conn.close()
    
    api_keys = {}
    for row in rows:
        key_name = row["key"]
        value = row["value"]
        # Masquer les clés (garder 4 derniers caractères)
        if value and len(value) > 4:
            api_keys[key_name] = "..." + value[-4:]
        else:
            api_keys[key_name] = value
    
    # Si aucune clé en DB, retourner valeurs vides par défaut
    if not api_keys:
        api_keys = {"openrouter_key": "", "anthropic_key": "", "google_key": ""}
    
    # Fallback .env si une clé est encore vide après lecture DB
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
                # Masquer comme les autres valeurs
                v = env_v.strip()
                api_keys[db_k] = "..." + v[-4:] if len(v) > 4 else v
    
    # Lire model_preferences depuis config.json
    model_preferences = {
        "routing": "google/gemini-2.0-flash-001",
        "structuring": "google/gemini-2.0-flash-001",
        "code": "anthropic/claude-haiku-4.5",
        "analysis": "anthropic/claude-sonnet-4.5"
    }
    
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_file = json.load(f)
            if "model_preferences" in config_file:
                model_preferences = config_file["model_preferences"]
    
    return {
        "api_keys": api_keys,
        "model_preferences": model_preferences
    }

@router.post("")
def save_config(config: Config):
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"📥 [SAVE_CONFIG] Payload reçu: {config.model_dump()}")
    
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config_dict = config.model_dump()
    
    # Sauvegarder api_keys dans SQLite
    conn = get_connection()
    cursor = conn.cursor()
    
    for key_name, value in config_dict.get("api_keys", {}).items():
        # Si valeur masquée (commence par "..."), ne pas modifier
        if value.startswith("..."):
            continue
        
        # Upsert dans app_config
        cursor.execute("""
            INSERT INTO app_config (key, value, category, updated_at)
            VALUES (?, ?, 'api_keys', datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key_name, value))
    
    conn.commit()
    conn.close()
    
    # Sauvegarder model_preferences dans config.json
    config_file = {"model_preferences": config_dict.get("model_preferences", {})}
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_file, f, indent=2)
    
    return {"message": "Configuration sauvegardée"}

@router.post("/test")
async def test_connection(request: TestConnectionRequest):
    # Lire api_keys depuis SQLite
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
            "google/gemini-2.0-flash-001",
            "google/gemini-2.5-flash",
            "meta-llama/llama-3.3-70b-instruct:free"
        ],
        "structuring": [
            "google/gemini-2.0-flash-001",
            "anthropic/claude-haiku-4.5",
            "google/gemini-2.5-flash"
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

@router.get("/global_context")
def get_global_context():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT value FROM app_config WHERE key = 'global_context'")
        row = cursor.fetchone()
        value = row["value"] if row else ""
    except Exception:
        value = ""
    conn.close()
    return {"value": value}

@router.post("/global_context")
def save_global_context(body: dict):
    value = body.get("value", "")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO app_config (key, value, category, updated_at) VALUES ('global_context', ?, 'context', datetime('now'))",
        (value,)
    )
    conn.commit()
    conn.close()
    return {"ok": True}
