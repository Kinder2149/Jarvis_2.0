# backend/routers/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import json

from backend.database import get_connection
from backend.services.chat_service import send_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Schémas Pydantic ──────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    project_id: int | None = None
    title: str | None = None
    folder_path: str | None = None


class MessageCreate(BaseModel):
    content: str


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/conversations")
def create_conversation(data: ConversationCreate):
    """Crée une nouvelle conversation."""
    db = get_connection()
    cursor = db.cursor()
    
    title = data.title if data.title else "Nouvelle conversation"
    now = datetime.utcnow().isoformat()
    
    # Hériter du local_path du projet si project_id défini et folder_path non fourni
    folder_path = data.folder_path
    if data.project_id and not folder_path:
        cursor.execute("SELECT local_path FROM projects WHERE id = ?", (data.project_id,))
        project_row = cursor.fetchone()
        if project_row and "local_path" in project_row.keys():
            folder_path = project_row["local_path"]
    
    cursor.execute(
        "INSERT INTO conversations (project_id, title, folder_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (data.project_id, title, folder_path, now, now)
    )
    conversation_id = cursor.lastrowid
    db.commit()
    
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    row = cursor.fetchone()
    db.close()
    
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "title": row["title"],
        "folder_path": row["folder_path"],
        "created_at": row["created_at"]
    }


@router.get("/conversations")
def list_conversations(project_id: int | None = None):
    """Liste les conversations, optionnellement filtrées par projet."""
    db = get_connection()
    cursor = db.cursor()
    
    if project_id is not None:
        cursor.execute(
            "SELECT * FROM conversations WHERE project_id = ? ORDER BY updated_at DESC",
            (project_id,)
        )
    else:
        cursor.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
    
    conversations = []
    for row in cursor.fetchall():
        conv_id = row["id"]
        
        # Compter les messages
        cursor.execute("SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?", (conv_id,))
        message_count = cursor.fetchone()["count"]
        
        conversations.append({
            "id": row["id"],
            "title": row["title"],
            "project_id": row["project_id"],
            "folder_path": row["folder_path"],
            "updated_at": row["updated_at"],
            "message_count": message_count
        })
    
    db.close()
    return conversations


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: int):
    """Récupère une conversation avec tous ses messages."""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    conv_row = cursor.fetchone()
    
    if not conv_row:
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    
    # Récupérer les messages
    cursor.execute(
        "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,)
    )
    messages = [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"]
        }
        for row in cursor.fetchall()
    ]
    
    db.close()
    
    return {
        "id": conv_row["id"],
        "title": conv_row["title"],
        "project_id": conv_row["project_id"],
        "folder_path": conv_row["folder_path"],
        "created_at": conv_row["created_at"],
        "messages": messages
    }


@router.post("/conversations/{conv_id}/messages")
async def send_message(conv_id: int, data: MessageCreate):
    """Envoie un message dans une conversation et retourne la réponse."""
    db = get_connection()
    config = load_config()
    
    try:
        result = await send_chat_message(conv_id, data.content, db, config)
        
        # Récupérer les messages créés
        cursor = db.cursor()
        cursor.execute("SELECT * FROM messages WHERE id = ?", (result["user_message_id"],))
        user_msg = cursor.fetchone()
        
        cursor.execute("SELECT * FROM messages WHERE id = ?", (result["assistant_message_id"],))
        assistant_msg = cursor.fetchone()
        
        db.close()
        
        return {
            "user_message": {
                "id": user_msg["id"],
                "role": user_msg["role"],
                "content": user_msg["content"]
            },
            "assistant_message": {
                "id": assistant_msg["id"],
                "role": assistant_msg["role"],
                "content": assistant_msg["content"]
            }
        }
    
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/conversations/{conv_id}/folder")
def update_conversation_folder(conv_id: int, folder_path: str | None = None):
    """Définit ou modifie le folder_path d'une conversation."""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    
    cursor.execute("UPDATE conversations SET folder_path = ? WHERE id = ?", (folder_path, conv_id))
    db.commit()
    db.close()
    
    return {"updated": True, "folder_path": folder_path}


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int):
    """Supprime une conversation et tous ses messages."""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    db.commit()
    db.close()
    
    return {"deleted": True}
