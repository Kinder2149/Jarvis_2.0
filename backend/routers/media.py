from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

from backend.database import get_connection, load_config
from backend.services import media_service

router = APIRouter(prefix="/media", tags=["media"])


class ImageRequest(BaseModel):
    prompt: str
    style: str = ""


class VideoRequest(BaseModel):
    prompt: str
    duration: str = "5"
    aspect_ratio: str = "16:9"


class ImageToVideoRequest(BaseModel):
    image_url: str
    prompt: str = ""
    duration: str = "5"
    aspect_ratio: str = "16:9"


class SocialContentRequest(BaseModel):
    topic: str
    platforms: List[str] = ["linkedin", "twitter"]
    tone: str = "professionnel"


def _now() -> str:
    return datetime.utcnow().isoformat()


@router.post("/generate/image")
async def generate_image(data: ImageRequest):
    config = load_config()
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO media_generations (type, prompt, status, created_at, updated_at) VALUES (?, ?, 'processing', ?, ?)",
        ("image", data.prompt, _now(), _now())
    )
    gen_id = cursor.lastrowid
    db.commit()

    try:
        result = await media_service.generate_image(data.prompt, data.style, config)
        cursor.execute(
            "UPDATE media_generations SET status='completed', result_url=?, updated_at=? WHERE id=?",
            (result["url"], _now(), gen_id)
        )
        db.commit()
        db.close()
        return {"id": gen_id, "status": "completed", **result}
    except Exception as e:
        cursor.execute(
            "UPDATE media_generations SET status='failed', error_message=?, updated_at=? WHERE id=?",
            (str(e), _now(), gen_id)
        )
        db.commit()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/video")
async def generate_video(data: VideoRequest):
    config = load_config()
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO media_generations (type, prompt, status, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)",
        ("video", data.prompt, _now(), _now())
    )
    gen_id = cursor.lastrowid
    db.commit()

    try:
        result = await media_service.submit_video(data.prompt, data.duration, data.aspect_ratio, config)
        cursor.execute(
            "UPDATE media_generations SET status='processing', fal_request_id=?, fal_endpoint=?, updated_at=? WHERE id=?",
            (result["request_id"], result["endpoint"], _now(), gen_id)
        )
        db.commit()
        db.close()
        return {"id": gen_id, "status": "processing", **result}
    except Exception as e:
        cursor.execute(
            "UPDATE media_generations SET status='failed', error_message=?, updated_at=? WHERE id=?",
            (str(e), _now(), gen_id)
        )
        db.commit()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/image-to-video")
async def generate_image_to_video(data: ImageToVideoRequest):
    config = load_config()
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO media_generations (type, prompt, result_url, status, created_at, updated_at) VALUES (?, ?, ?, 'pending', ?, ?)",
        ("image_to_video", data.prompt, data.image_url, _now(), _now())
    )
    gen_id = cursor.lastrowid
    db.commit()

    try:
        result = await media_service.submit_image_to_video(
            data.image_url, data.prompt, data.duration, data.aspect_ratio, config
        )
        cursor.execute(
            "UPDATE media_generations SET status='processing', fal_request_id=?, fal_endpoint=?, updated_at=? WHERE id=?",
            (result["request_id"], result["endpoint"], _now(), gen_id)
        )
        db.commit()
        db.close()
        return {"id": gen_id, "status": "processing", **result}
    except Exception as e:
        cursor.execute(
            "UPDATE media_generations SET status='failed', error_message=?, updated_at=? WHERE id=?",
            (str(e), _now(), gen_id)
        )
        db.commit()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/social-content")
async def generate_social_content(data: SocialContentRequest):
    import json as json_lib
    config = load_config()
    db = get_connection()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO media_generations (type, prompt, status, created_at, updated_at) VALUES (?, ?, 'processing', ?, ?)",
        ("social", data.topic, _now(), _now())
    )
    gen_id = cursor.lastrowid
    db.commit()

    try:
        result = await media_service.generate_social_content(data.topic, data.platforms, data.tone, config)
        cursor.execute(
            "UPDATE media_generations SET status='completed', result_content=?, updated_at=? WHERE id=?",
            (json_lib.dumps(result, ensure_ascii=False), _now(), gen_id)
        )
        db.commit()
        db.close()
        return {"id": gen_id, "status": "completed", "content": result}
    except Exception as e:
        cursor.execute(
            "UPDATE media_generations SET status='failed', error_message=?, updated_at=? WHERE id=?",
            (str(e), _now(), gen_id)
        )
        db.commit()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{request_id}")
async def check_job(request_id: str, endpoint: str):
    config = load_config()
    try:
        result = await media_service.check_job_status(request_id, endpoint, config)
        if result["status"] == "completed":
            db = get_connection()
            cursor = db.cursor()
            cursor.execute(
                "UPDATE media_generations SET status='completed', result_url=?, updated_at=? WHERE fal_request_id=?",
                (result.get("video_url", ""), _now(), request_id)
            )
            db.commit()
            db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_history(limit: int = 20):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, type, prompt, status, result_url, result_content, fal_request_id, fal_endpoint, error_message, created_at FROM media_generations ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    db.close()
    return [dict(row) for row in rows]
