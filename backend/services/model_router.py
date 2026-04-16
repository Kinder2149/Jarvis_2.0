import httpx
from pathlib import Path
import json
import asyncio

def get_model_id(model_type: str, config: dict) -> str:
    return config.get("model_preferences", {}).get(model_type, "")

async def call_model(
    model_id: str,
    messages: list[dict],
    api_keys: dict,
    session_id: int,
    step_name: str,
    model_type: str,
    db_conn
) -> str:
    openrouter_key = api_keys.get("openrouter_key", "")
    anthropic_key = api_keys.get("anthropic_key", "")
    google_key = api_keys.get("google_key", "")
    
    if openrouter_key:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "JARVIS"
                    },
                    json={
                        "model": model_id,
                        "messages": messages
                    }
                )
                
                if response.status_code == 429:
                    await asyncio.sleep(2)
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {openrouter_key}",
                            "HTTP-Referer": "http://localhost:8000",
                            "X-Title": "JARVIS"
                        },
                        json={
                            "model": model_id,
                            "messages": messages
                        }
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    input_tokens = data.get("usage", {}).get("prompt_tokens", 0)
                    output_tokens = data.get("usage", {}).get("completion_tokens", 0)
                    
                    cursor = db_conn.cursor()
                    cursor.execute(
                        """INSERT INTO model_decision_log 
                        (session_id, step_name, model_type, model_id_chosen, input_tokens, output_tokens)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (session_id, step_name, model_type, model_id, input_tokens, output_tokens)
                    )
                    db_conn.commit()
                    
                    return content
                elif response.status_code == 401:
                    raise Exception("Clé API invalide ou expirée. Vérifier dans Paramètres.")
                elif response.status_code == 429:
                    raise Exception("Quota dépassé sur ce modèle. Réessayer dans quelques minutes.")
                elif response.status_code == 404:
                    raise Exception(f"Modèle introuvable : {model_id}. Vérifier le slug dans Paramètres.")
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", response.text[:100])
                    except Exception:
                        error_msg = response.text[:100]
                    raise Exception(f"Erreur modèle ({response.status_code}) : {error_msg}")
        
        except httpx.TimeoutException:
            raise Exception("Modèle injoignable. Vérifier la connexion.")
        except httpx.NetworkError:
            raise Exception("Modèle injoignable. Vérifier la connexion.")
        except Exception as e:
            if "Clé API" in str(e) or "Quota" in str(e) or "Modèle introuvable" in str(e) or "Erreur modèle" in str(e) or "injoignable" in str(e):
                raise
            raise Exception(f"Erreur appel OpenRouter : {str(e)}")
    
    elif "anthropic/" in model_id and anthropic_key:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": model_id.replace("anthropic/", ""),
                        "max_tokens": 4096,
                        "messages": messages
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    
                    input_tokens = data.get("usage", {}).get("input_tokens", 0)
                    output_tokens = data.get("usage", {}).get("output_tokens", 0)
                    
                    cursor = db_conn.cursor()
                    cursor.execute(
                        """INSERT INTO model_decision_log 
                        (session_id, step_name, model_type, model_id_chosen, input_tokens, output_tokens)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (session_id, step_name, model_type, model_id, input_tokens, output_tokens)
                    )
                    db_conn.commit()
                    
                    return content
                elif response.status_code == 401:
                    raise Exception("Clé API invalide ou expirée. Vérifier dans Paramètres.")
                elif response.status_code == 429:
                    raise Exception("Quota dépassé sur ce modèle. Réessayer dans quelques minutes.")
                elif response.status_code == 404:
                    raise Exception(f"Modèle introuvable : {model_id}. Vérifier le slug dans Paramètres.")
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", response.text[:100])
                    except Exception:
                        error_msg = response.text[:100]
                    raise Exception(f"Erreur modèle ({response.status_code}) : {error_msg}")
        
        except httpx.TimeoutException:
            raise Exception("Modèle injoignable. Vérifier la connexion.")
        except httpx.NetworkError:
            raise Exception("Modèle injoignable. Vérifier la connexion.")
        except Exception as e:
            if "Clé API" in str(e) or "Quota" in str(e) or "Modèle introuvable" in str(e) or "Erreur modèle" in str(e) or "injoignable" in str(e):
                raise
            raise Exception(f"Erreur appel Anthropic : {str(e)}")
    
    else:
        raise Exception("No valid API key configured")
