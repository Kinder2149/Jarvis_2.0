import httpx
import asyncio
import logging

logger = logging.getLogger("jarvis")

def get_model_id(model_type: str, config: dict, override: str | None = None) -> str:
    if override:
        return override
    return config.get("model_preferences", {}).get(model_type, "")

def _strip_code_fence(content: str) -> str:
    content = content.strip()
    if content.startswith("```") and content.endswith("```"):
        lines = content.split('\n')
        if len(lines) >= 3:
            return '\n'.join(lines[1:-1]).strip()
    return content

async def _post_with_retry(client: httpx.AsyncClient, url: str, headers: dict, payload: dict) -> httpx.Response:
    response = await client.post(url, headers=headers, json=payload)
    delays = [60, 120, 240]
    for attempt, delay in enumerate(delays, start=1):
        if response.status_code != 429:
            break
        logger.debug(f"[MODEL_ROUTER] 429 reçu, attente {delay}s avant retry (tentative {attempt}/{len(delays)})")
        await asyncio.sleep(delay)
        response = await client.post(url, headers=headers, json=payload)
    return response

async def call_model(
    model_id: str,
    messages: list[dict],
    api_keys: dict,
    session_id: int,
    step_name: str,
    model_type: str,
    db_conn,
    module_name: str = "unknown"
) -> str:
    openrouter_key = api_keys.get("openrouter_key", "")
    anthropic_key = api_keys.get("anthropic_key", "")

    if openrouter_key:
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                try:
                    response = await asyncio.wait_for(
                        _post_with_retry(
                            client,
                            "https://openrouter.ai/api/v1/chat/completions",
                            {
                                "Authorization": f"Bearer {openrouter_key}",
                                "HTTP-Referer": "http://localhost:8000",
                                "X-Title": "JARVIS"
                            },
                            {"model": model_id, "messages": messages, "max_tokens": 8192}
                        ),
                        timeout=60.0
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError("Timeout LLM après 60s — réessaie dans un moment.")

                if response.status_code == 200:
                    data = response.json()
                    content = _strip_code_fence(data["choices"][0]["message"]["content"])
                    input_tokens = data.get("usage", {}).get("prompt_tokens", 0)
                    output_tokens = data.get("usage", {}).get("completion_tokens", 0)
                    
                    # Logging optionnel si db_conn fourni (BUG-05/08 corrigé)
                    if db_conn is not None:
                        cursor = db_conn.cursor()
                        cursor.execute(
                            """INSERT INTO model_decision_log
                            (session_id, step_name, model_type, model_id_chosen, input_tokens, output_tokens, module_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (session_id, step_name, model_type, model_id, input_tokens, output_tokens, module_name)
                        )
                        db_conn.commit()
                    
                    return content
                elif response.status_code == 401:
                    raise Exception("Clé API invalide ou expirée. Vérifier dans Paramètres.")
                elif response.status_code == 429:
                    raise Exception("Quota dépassé après 3 tentatives. Attendre quelques minutes ou vérifier le crédit OpenRouter.")
                elif response.status_code == 404:
                    raise Exception(f"Modèle introuvable : {model_id}. Vérifier le slug dans Paramètres.")
                else:
                    try:
                        error_msg = response.json().get("error", {}).get("message", response.text[:100])
                    except Exception:
                        error_msg = response.text[:100]
                    raise Exception(f"Erreur modèle ({response.status_code}) : {error_msg}")

        except httpx.TimeoutException:
            raise Exception("Modèle injoignable (timeout 5 min dépassé). Vérifier la connexion.")
        except httpx.NetworkError:
            raise Exception("Modèle injoignable. Vérifier la connexion.")
        except Exception as e:
            if any(kw in str(e) for kw in ["Clé API", "Quota", "Modèle introuvable", "Erreur modèle", "injoignable", "timeout"]):
                raise
            raise Exception(f"Erreur appel OpenRouter : {str(e)}")

    elif "anthropic/" in model_id and anthropic_key:
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                try:
                    response = await asyncio.wait_for(
                        _post_with_retry(
                            client,
                            "https://api.anthropic.com/v1/messages",
                            {
                                "x-api-key": anthropic_key,
                                "anthropic-version": "2023-06-01",
                                "content-type": "application/json"
                            },
                            {"model": model_id.replace("anthropic/", ""), "max_tokens": 4096, "messages": messages}
                        ),
                        timeout=60.0
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError("Timeout LLM après 60s — réessaie dans un moment.")

                if response.status_code == 200:
                    data = response.json()
                    content = _strip_code_fence(data["content"][0]["text"])
                    input_tokens = data.get("usage", {}).get("input_tokens", 0)
                    output_tokens = data.get("usage", {}).get("output_tokens", 0)
                    if db_conn is not None:
                        cursor = db_conn.cursor()
                        cursor.execute(
                            """INSERT INTO model_decision_log
                            (session_id, step_name, model_type, model_id_chosen, input_tokens, output_tokens, module_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (session_id, step_name, model_type, model_id, input_tokens, output_tokens, module_name)
                        )
                        db_conn.commit()
                    return content
                elif response.status_code == 401:
                    raise Exception("Clé API invalide ou expirée. Vérifier dans Paramètres.")
                elif response.status_code == 429:
                    raise Exception("Quota dépassé après 3 tentatives. Attendre quelques minutes ou vérifier le crédit Anthropic.")
                elif response.status_code == 404:
                    raise Exception(f"Modèle introuvable : {model_id}. Vérifier le slug dans Paramètres.")
                else:
                    try:
                        error_msg = response.json().get("error", {}).get("message", response.text[:100])
                    except Exception:
                        error_msg = response.text[:100]
                    raise Exception(f"Erreur modèle ({response.status_code}) : {error_msg}")

        except httpx.TimeoutException:
            raise Exception("Modèle injoignable (timeout 5 min dépassé). Vérifier la connexion.")
        except httpx.NetworkError:
            raise Exception("Modèle injoignable. Vérifier la connexion.")
        except Exception as e:
            if any(kw in str(e) for kw in ["Clé API", "Quota", "Modèle introuvable", "Erreur modèle", "injoignable", "timeout"]):
                raise
            raise Exception(f"Erreur appel Anthropic : {str(e)}")

    else:
        raise Exception("No valid API key configured")
