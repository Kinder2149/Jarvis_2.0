# backend/routers/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import json

from backend.database import get_connection, load_config
from backend.services.chat_service import send_chat_message, generate_conversation_summary

router = APIRouter(prefix="/chat", tags=["chat"])


# ─── Schémas Pydantic ──────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    project_id: int | None = None
    title: str | None = None
    folder_path: str | None = None
    internet_access: bool = False
    model: str = ""


class MessageCreate(BaseModel):
    content: str
    model: str | None = None
    attachment_base64: str | None = None
    attachment_filename: str | None = None


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/conversations")
def create_conversation(data: ConversationCreate):
    """Crée une nouvelle conversation."""
    db = get_connection()
    cursor = db.cursor()
    
    title = data.title if data.title else "Nouvelle conversation"
    now = datetime.utcnow().isoformat()
    
    # Hériter du path du projet si project_id défini et folder_path non fourni
    folder_path = data.folder_path
    if data.project_id and not folder_path:
        cursor.execute("SELECT path FROM projects WHERE id = ?", (data.project_id,))
        project_row = cursor.fetchone()
        if project_row and "path" in project_row.keys():
            folder_path = project_row["path"]
    
    cursor.execute(
        "INSERT INTO conversations (project_id, title, folder_path, internet_access, context_summary, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (data.project_id, title, folder_path, 1 if data.internet_access else 0, "", data.model or "", now, now)
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
        "internet_access": bool(row["internet_access"]) if "internet_access" in row.keys() else False,
        "context_summary": row["context_summary"] if "context_summary" in row.keys() else "",
        "model": row["model"] if "model" in row.keys() else "",
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
        
        # Récupérer le dernier message assistant
        cursor.execute(
            "SELECT content, created_at FROM messages WHERE conversation_id = ? AND role = 'assistant' ORDER BY created_at DESC LIMIT 1",
            (conv_id,)
        )
        last_msg = cursor.fetchone()
        
        last_message_preview = None
        last_message_at = None
        if last_msg:
            content = last_msg["content"] or ""
            last_message_preview = content[:80]
            last_message_at = last_msg["created_at"]
        
        conversations.append({
            "id": row["id"],
            "title": row["title"],
            "project_id": row["project_id"],
            "folder_path": row["folder_path"],
            "internet_access": bool(row["internet_access"]) if "internet_access" in row.keys() else False,
            "context_summary": row["context_summary"] if "context_summary" in row.keys() else "",
            "model": row["model"] if "model" in row.keys() else "",
            "updated_at": row["updated_at"],
            "message_count": message_count,
            "last_message_preview": last_message_preview,
            "last_message_at": last_message_at
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
        "SELECT id, role, content, created_at, attachment_filename FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,)
    )
    messages = [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
            "attachment_filename": row["attachment_filename"] if "attachment_filename" in row.keys() else None
        }
        for row in cursor.fetchall()
    ]
    
    db.close()
    
    return {
        "id": conv_row["id"],
        "title": conv_row["title"],
        "project_id": conv_row["project_id"],
        "folder_path": conv_row["folder_path"],
        "internet_access": bool(conv_row["internet_access"]) if "internet_access" in conv_row.keys() else False,
        "context_summary": conv_row["context_summary"] if "context_summary" in conv_row.keys() else "",
        "model": conv_row["model"] if "model" in conv_row.keys() else "",
        "created_at": conv_row["created_at"],
        "messages": messages
    }


@router.post("/conversations/{conv_id}/messages")
async def send_message(conv_id: int, data: MessageCreate):
    """Envoie un message dans une conversation et retourne la réponse."""
    import logging
    logger = logging.getLogger("uvicorn")
    
    db = get_connection()
    config = load_config()
    
    logger.info(f"📥 [CHAT] Config chargée: api_keys={list(config.get('api_keys', {}).keys())}, chat={config.get('chat', {})}")
    
    # Override du modèle si fourni
    if data.model:
        if "chat" not in config:
            config["chat"] = {}
        config["chat"]["model"] = data.model
    
    try:
        result = await send_chat_message(
            conv_id, 
            data.content, 
            db, 
            config,
            attachment_base64=data.attachment_base64,
            attachment_filename=data.attachment_filename
        )
        
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


class ConversationUpdate(BaseModel):
    folder_path: str | None = None
    internet_access: bool | None = None
    model: str | None = None
    context_summary: str | None = None


@router.patch("/conversations/{conv_id}")
def update_conversation(conv_id: int, data: ConversationUpdate):
    """Met à jour les champs d'une conversation (folder_path, internet_access, model, context_summary)."""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    conv_row = cursor.fetchone()
    if not conv_row:
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    
    # Construire la requête UPDATE dynamiquement
    updates = []
    params = []
    
    if data.folder_path is not None:
        updates.append("folder_path = ?")
        params.append(data.folder_path)
    
    if data.internet_access is not None:
        updates.append("internet_access = ?")
        params.append(1 if data.internet_access else 0)
    
    if data.model is not None:
        updates.append("model = ?")
        params.append(data.model)
    
    if data.context_summary is not None:
        updates.append("context_summary = ?")
        params.append(data.context_summary)
    
    if not updates:
        db.close()
        return {"updated": False, "message": "Aucun champ à mettre à jour"}
    
    params.append(conv_id)
    query = f"UPDATE conversations SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    db.commit()
    
    # Récupérer la conversation mise à jour
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    updated_row = cursor.fetchone()
    db.close()
    
    return {
        "id": updated_row["id"],
        "title": updated_row["title"],
        "project_id": updated_row["project_id"],
        "folder_path": updated_row["folder_path"],
        "internet_access": bool(updated_row["internet_access"]) if "internet_access" in updated_row.keys() else False,
        "context_summary": updated_row["context_summary"] if "context_summary" in updated_row.keys() else "",
        "model": updated_row["model"] if "model" in updated_row.keys() else "",
        "updated_at": updated_row["updated_at"]
    }


class FolderUpdate(BaseModel):
    folder_path: str | None = None

@router.patch("/conversations/{conv_id}/folder")
def update_conversation_folder(conv_id: int, data: FolderUpdate):
    """Définit ou modifie le folder_path d'une conversation."""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    cursor.execute(
        "UPDATE conversations SET folder_path = ?, updated_at = ? WHERE id = ?",
        (data.folder_path, datetime.now().isoformat(), conv_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    updated = dict(cursor.fetchone())
    db.close()
    
    return updated


@router.post("/conversations/{conversation_id}/update-summary")
async def update_conversation_summary(conversation_id: int):
    """Génère et met à jour le résumé de la conversation via LLM."""
    result = await generate_conversation_summary(conversation_id)
    if not result["ok"]:
        if result.get("message") == "Conversation introuvable":
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        raise HTTPException(status_code=500, detail=result.get("message", "Erreur inconnue"))
    return result


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
