import asyncio
import json
import logging
import random
import urllib.parse
import httpx
from backend.database import get_connection
from backend.services.model_router import get_model_id, call_model

logger = logging.getLogger("jarvis")

AGENT_NAME = "MEDIA"

_CONFIRM_SIGNALS = ["oui", "ok", "go", "vas-y", "yes", "valide", "validé", "parfait", "yep", "ouais"]
_ABORT_SIGNALS = ["non", "annule", "annuler", "stop", "laisse tomber", "oublie", "abort"]

_FAL_VIDEO_MODEL = "fal-ai/kling-video/v1.6/standard/text-to-video"


def _is_confirm(message: str) -> bool:
    msg = message.lower().strip()
    return msg.startswith("oui") or any(s in msg for s in _CONFIRM_SIGNALS)


def _is_abort(message: str) -> bool:
    msg = message.lower().strip()
    return msg.startswith("non") or any(s in msg for s in _ABORT_SIGNALS)


async def handle(
    conversation_id: int,
    message: str,
    current_instance_ref: dict | None,
    db,
    config: dict
) -> tuple:
    state_type = current_instance_ref.get("type") if current_instance_ref else None

    if state_type == "media_confirm":
        return await _handle_confirmation(conversation_id, message, current_instance_ref, db, config)

    if state_type == "media_running":
        result = _handle_status_query(message, current_instance_ref)
        if result is not None:
            return result

    if _is_abort(message) and current_instance_ref:
        return ("D'accord, j'annule. Que veux-tu générer ?", AGENT_NAME, None, False, None)

    return await _handle_new_task(conversation_id, message, db, config)


async def _handle_new_task(conversation_id: int, message: str, db, config: dict) -> tuple:
    msg_lower = message.lower()

    _VIDEO_INTENT = ["génère une vidéo", "génère une video", "crée une vidéo", "crée une video",
                     "fais une vidéo", "fais une video", "faire une vidéo", "faire une video",
                     "clip vidéo", "clip video", "animation vidéo"]
    if any(w in msg_lower for w in _VIDEO_INTENT):
        media_type = "video"
        type_label = "vidéo"
    else:
        media_type = "image"
        type_label = "image"

    model_id = get_model_id("analysis", config)
    no_bg_requested = any(w in message.lower() for w in
        ["sans fond", "no background", "fond transparent", "fond blanc", "sans arrière-plan", "png", "détouré"])
    bg_instruction = (
        "The background must be plain white (#FFFFFF), clean and uniform — no shadows, no gradients. "
        "This allows easy background removal. "
    ) if no_bg_requested else ""

    prompt_llm = (
        f"L'utilisateur veut générer une {type_label} avec cette description : \"{message}\"\n\n"
        f"Reformule en anglais un prompt de génération optimisé pour le modèle Flux (max 150 mots). "
        f"Règles : commence par le style visuel, décris le sujet principal, la composition, l'éclairage, "
        f"les couleurs dominantes. {bg_instruction}"
        f"Réponds UNIQUEMENT avec le prompt anglais, aucune explication, aucun préfixe."
    )
    try:
        refined_prompt = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt_llm}],
            api_keys=config["api_keys"],
            session_id=None,
            step_name="media_prompt_refine",
            model_type="analysis",
            db_conn=db,
            module_name="media"
        )
        # Nettoyer tout artefact LLM (le modèle répète parfois le préfixe système)
        refined_prompt = refined_prompt.strip()
        if refined_prompt.lower().startswith("[media]") or refined_prompt.lower().startswith("["):
            first_newline = refined_prompt.find("\n")
            if first_newline != -1:
                refined_prompt = refined_prompt[first_newline:].strip()
    except Exception:
        refined_prompt = message

    state = {
        "type": "media_confirm",
        "media_type": media_type,
        "prompt": refined_prompt.strip(),
        "original_message": message
    }

    content = (
        f"[MEDIA] Je vais générer une **{type_label}** avec ce prompt :\n\n"
        f"> {refined_prompt.strip()}\n\n"
        f"**Tu valides ? Réponds oui pour lancer, non pour annuler ou modifier.**"
    )
    return content, AGENT_NAME, state, False, None


async def _handle_confirmation(
    conversation_id: int, message: str, state: dict, db, config: dict
) -> tuple:
    if _is_confirm(message):
        asyncio.create_task(_run_generation(conversation_id, state, config))
        media_type = state["media_type"]
        instance_ref = {"type": "media_running", "media_type": media_type}
        if media_type == "image":
            msg = "[MEDIA] Génération lancée ✨ L'image arrive dans quelques secondes…"
        else:
            msg = "[MEDIA] Génération lancée ✨ La vidéo arrive dans environ une minute…"
        return (msg, AGENT_NAME, instance_ref, False, None)

    if _is_abort(message):
        return ("D'accord, annulé. Décris-moi ce que tu veux générer.", AGENT_NAME, None, False, None)

    return (
        "[MEDIA] Je n'ai pas compris. Réponds **oui** pour lancer ou **non** pour annuler.",
        AGENT_NAME, state, False, None
    )


def _handle_status_query(message: str, current_instance_ref: dict) -> tuple:
    media_type = current_instance_ref.get("media_type", "média")
    msg_lower = message.lower().strip()
    _STATUS_QUESTIONS = ["statut", "avance", "prêt", "terminé", "fini", "ça avance", "en cours"]
    is_status_question = len(msg_lower) < 20 or any(w in msg_lower for w in _STATUS_QUESTIONS)
    if not is_status_question:
        return None
    return (
        f"[MEDIA] La génération de {media_type} est en cours… je te notifie dès que c'est prêt.",
        AGENT_NAME, current_instance_ref, False, None
    )


def _build_pollinations_url(prompt: str, no_background: bool = False) -> str:
    prompt_lower = prompt.lower()

    if any(w in prompt_lower for w in ["anime", "manga", "illustration", "cartoon", "concept art"]):
        model = "flux-anime"
    elif any(w in prompt_lower for w in ["photo", "realistic", "portrait", "photorealistic"]):
        model = "flux-realism"
    else:
        model = "flux"

    is_character = any(w in prompt_lower for w in
        ["character", "portrait", "figure", "half-body", "full-body", "person"])
    width, height = (768, 1024) if is_character else (1024, 768)

    # Prompt enrichi selon le contexte
    final_prompt = prompt
    if no_background and is_character:
        final_prompt = (
            "centered composition, waist-up shot, plain white background, clean cutout edges, "
            + prompt
        )

    negative = ""
    if no_background:
        negative = urllib.parse.quote(
            "dark background, black background, atmospheric background, gradient, moody, fog, "
            "smoke, bokeh background, environmental lighting, scene, landscape", safe=""
        )

    seed = random.randint(1, 999999)
    encoded = urllib.parse.quote(final_prompt, safe="")
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&seed={seed}&nologo=true&enhance=true&model={model}"
    )
    if negative:
        url += f"&negative={negative}"
    return url


async def _run_generation(conversation_id: int, state: dict, config: dict) -> None:
    db = get_connection()
    try:
        media_type = state["media_type"]
        prompt = state["prompt"]

        if media_type == "image":
            no_bg = any(w in prompt.lower() for w in
                ["white background", "plain white", "no background", "sans fond", "détouré"])
            result_url = _build_pollinations_url(prompt, no_background=no_bg)
            
            prefetch_ok = False
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.get(result_url, follow_redirects=True)
                    prefetch_ok = resp.status_code < 400
            except Exception as poll_err:
                logger.warning(f"[MEDIA] Pollinations prefetch warning: {poll_err}")
            
            if not prefetch_ok:
                db.execute("""
                    INSERT INTO media_jobs (conversation_id, media_type, prompt, result_url, status, created_at)
                    VALUES (?, ?, ?, ?, 'error', datetime('now'))
                """, (conversation_id, media_type, prompt, result_url))
                db.commit()
                _inject_message(
                    conversation_id, db,
                    "[MEDIA] ⚠️ Pollinations est inaccessible ou la génération a échoué.\n\n"
                    "Réessaie dans quelques instants ou décris une image différente."
                )
                return
            
            db.execute("""
                INSERT INTO media_jobs (conversation_id, media_type, prompt, result_url, status, created_at)
                VALUES (?, ?, ?, ?, 'done', datetime('now'))
            """, (conversation_id, media_type, prompt, result_url))
            db.commit()
            bg_tip = (
                "\n\n💡 Fond blanc généré — supprime-le gratuitement sur [remove.bg](https://www.remove.bg) pour obtenir un PNG transparent."
            ) if no_bg else ""
            content = (
                f"[MEDIA] Image générée ✅\n\n"
                f"![Image générée]({result_url})\n\n"
                f"[Télécharger / ouvrir en plein écran]({result_url}){bg_tip}\n\n"
                f"Dis-moi si tu veux en générer une autre ou modifier quelque chose."
            )
            _inject_message(conversation_id, db, content)

        else:
            await _run_fal_video(conversation_id, prompt, config, db)

    except Exception as e:
        logger.error(f"[MEDIA] Erreur génération (conv={conversation_id}): {e}")
        _inject_message(conversation_id, db, f"[MEDIA] Erreur inattendue : {e}")
    finally:
        db.close()


async def _run_fal_video(conversation_id: int, prompt: str, config: dict, db) -> None:
    fal_key = config.get("api_keys", {}).get("fal_key", "")
    if not fal_key:
        _inject_message(
            conversation_id, db,
            "[MEDIA] ⚠️ Clé fal.ai non configurée. Va dans **Paramètres → Clés API** pour l'ajouter."
        )
        return

    url = f"https://fal.run/{_FAL_VIDEO_MODEL}"
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "duration": "5", "aspect_ratio": "16:9"}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        result_url = (
            data.get("video", {}).get("url")
            or (data.get("videos") or [{}])[0].get("url")
        )

        db.execute("""
            INSERT INTO media_jobs (conversation_id, media_type, prompt, result_url, status, created_at)
            VALUES (?, ?, ?, ?, 'done', datetime('now'))
        """, (conversation_id, "video", prompt, result_url))
        db.commit()

        if result_url:
            content = (
                f"[MEDIA] Vidéo générée ✅\n\n"
                f"[Ouvrir la vidéo]({result_url})\n\n"
                f"Dis-moi si tu veux en générer une autre ou modifier quelque chose."
            )
        else:
            content = (
                f"[MEDIA] Génération terminée mais aucune URL reçue.\n\n"
                f"Réponse brute : {json.dumps(data, ensure_ascii=False)[:500]}"
            )
        _inject_message(conversation_id, db, content)

    except httpx.HTTPStatusError as e:
        logger.error(f"[MEDIA] fal.ai HTTP error {e.response.status_code}: {e.response.text}")
        _inject_message(
            conversation_id, db,
            f"[MEDIA] Erreur vidéo fal.ai ({e.response.status_code}). Vérifie ta clé fal.ai dans Paramètres."
        )


def _inject_message(conversation_id: int, db, content: str) -> None:
    try:
        db.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, ?, NULL, datetime('now'))
        """, (conversation_id, content, AGENT_NAME))
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"[MEDIA] _inject_message échoué: {e}")
