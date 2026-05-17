import httpx
import json
import logging
from backend.services.model_router import call_model, get_model_id

logger = logging.getLogger("jarvis")

FAL_BASE = "https://fal.run"
FAL_QUEUE_BASE = "https://queue.fal.run"

TEXT_TO_VIDEO_ENDPOINT = "fal-ai/kling-video/v1.6/standard/text-to-video"
IMAGE_TO_VIDEO_ENDPOINT = "fal-ai/kling-video/v1.6/standard/image-to-video"


def _fal_headers(fal_key: str) -> dict:
    return {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }


def _require_fal_key(config: dict) -> str:
    key = config.get("api_keys", {}).get("fal_key", "")
    if not key:
        raise Exception("Clé fal.ai manquante. Configurer FAL_KEY dans Paramètres.")
    return key


async def generate_image(prompt: str, style: str, config: dict) -> dict:
    fal_key = _require_fal_key(config)
    full_prompt = f"{prompt}. Style: {style}" if style else prompt

    payload = {
        "prompt": full_prompt,
        "image_size": "landscape_16_9",
        "num_images": 1,
        "enable_safety_checker": True,
        "output_format": "jpeg"
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{FAL_BASE}/fal-ai/flux-pro/v1.1",
            headers=_fal_headers(fal_key),
            json=payload
        )

    if response.status_code != 200:
        try:
            error = response.json().get("detail", response.text[:200])
        except Exception:
            error = response.text[:200]
        raise Exception(f"fal.ai erreur {response.status_code}: {error}")

    data = response.json()
    images = data.get("images", [])
    if not images:
        raise Exception("Aucune image retournée par fal.ai")

    return {
        "url": images[0]["url"],
        "width": images[0].get("width", 0),
        "height": images[0].get("height", 0),
        "prompt": full_prompt
    }


async def submit_video(prompt: str, duration: str, aspect_ratio: str, config: dict) -> dict:
    fal_key = _require_fal_key(config)

    payload = {
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "cfg_scale": 0.5
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{FAL_QUEUE_BASE}/{TEXT_TO_VIDEO_ENDPOINT}",
            headers=_fal_headers(fal_key),
            json=payload
        )

    if response.status_code not in (200, 202):
        try:
            error = response.json().get("detail", response.text[:200])
        except Exception:
            error = response.text[:200]
        raise Exception(f"fal.ai erreur {response.status_code}: {error}")

    data = response.json()
    return {
        "request_id": data.get("request_id", ""),
        "endpoint": TEXT_TO_VIDEO_ENDPOINT
    }


async def submit_image_to_video(image_url: str, prompt: str, duration: str, aspect_ratio: str, config: dict) -> dict:
    fal_key = _require_fal_key(config)

    payload = {
        "image_url": image_url,
        "prompt": prompt or "Animate this image naturally",
        "duration": duration,
        "aspect_ratio": aspect_ratio
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{FAL_QUEUE_BASE}/{IMAGE_TO_VIDEO_ENDPOINT}",
            headers=_fal_headers(fal_key),
            json=payload
        )

    if response.status_code not in (200, 202):
        try:
            error = response.json().get("detail", response.text[:200])
        except Exception:
            error = response.text[:200]
        raise Exception(f"fal.ai erreur {response.status_code}: {error}")

    data = response.json()
    return {
        "request_id": data.get("request_id", ""),
        "endpoint": IMAGE_TO_VIDEO_ENDPOINT
    }


async def check_job_status(request_id: str, endpoint: str, config: dict) -> dict:
    fal_key = _require_fal_key(config)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{FAL_QUEUE_BASE}/{endpoint}/requests/{request_id}/status",
            headers=_fal_headers(fal_key)
        )

    if response.status_code != 200:
        raise Exception(f"Erreur vérification statut: {response.status_code}")

    data = response.json()
    status = data.get("status", "IN_QUEUE")

    if status == "COMPLETED":
        async with httpx.AsyncClient(timeout=30.0) as client:
            result_response = await client.get(
                f"{FAL_QUEUE_BASE}/{endpoint}/requests/{request_id}",
                headers=_fal_headers(fal_key)
            )
        if result_response.status_code == 200:
            result = result_response.json()
            video = result.get("video", {})
            return {
                "status": "completed",
                "video_url": video.get("url", ""),
                "request_id": request_id
            }

    if status == "FAILED":
        return {
            "status": "failed",
            "error": data.get("error", "Génération échouée"),
            "request_id": request_id
        }

    return {
        "status": "processing",
        "queue_position": data.get("queue_position"),
        "request_id": request_id
    }


async def generate_social_content(topic: str, platforms: list, tone: str, config: dict) -> dict:
    model_id = get_model_id("analysis", config)
    api_keys = config.get("api_keys", {})

    platforms_str = ", ".join(platforms)
    prompt = f"""Tu es un expert en marketing digital et copywriting.

Génère du contenu optimisé pour les réseaux sociaux sur :
Sujet : {topic}
Ton : {tone}
Plateformes : {platforms_str}

Retourne UNIQUEMENT un JSON valide (sans balises de code) avec ces clés :
{{
  "linkedin": "texte LinkedIn (max 3000 chars, professionnel avec emojis) ou null si non demandé",
  "twitter": "tweet (max 280 chars, accrocheur) ou null si non demandé",
  "instagram": "légende Instagram (engageante + 10-15 hashtags pertinents) ou null si non demandé",
  "youtube": "description YouTube (SEO-optimisée, inclure mots-clés et appel à l'action) ou null si non demandé"
}}"""

    result = await call_model(
        model_id,
        [{"role": "user", "content": prompt}],
        api_keys,
        None,
        "social_content",
        "analysis",
        None,
        module_name="media"
    )

    result = result.strip()
    if result.startswith("```"):
        lines = result.split('\n')
        result = '\n'.join(lines[1:-1])

    try:
        return json.loads(result)
    except Exception:
        return {"raw": result}
