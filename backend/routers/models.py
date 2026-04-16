from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import httpx
from backend.schemas.config import Config

router = APIRouter(prefix="/config", tags=["config"])

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"

class TestConnectionRequest(BaseModel):
    provider: str

@router.get("")
def get_config():
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
        config = json.load(f)
    
    if "api_keys" in config:
        for key in config["api_keys"]:
            value = config["api_keys"][key]
            if value and len(value) > 4:
                config["api_keys"][key] = "..." + value[-4:]
    
    return config

@router.post("")
def save_config(config: Config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    config_dict = config.model_dump()

    # Préserver les clés API masquées : si la valeur commence par "...",
    # restaurer la vraie valeur depuis le fichier existant
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)

        for key in config_dict.get("api_keys", {}):
            new_value = config_dict["api_keys"].get(key, "")
            if new_value.startswith("..."):
                config_dict["api_keys"][key] = existing.get("api_keys", {}).get(key, "")

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)

    return {"message": "Configuration sauvegardée"}

@router.post("/test")
async def test_connection(request: TestConnectionRequest):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    api_keys = config.get("api_keys", {})
    
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
