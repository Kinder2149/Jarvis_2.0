"""
Models simplifiés pour JARVIS 2.0 - Chat Simple
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Conversation(BaseModel):
    """Conversation avec un agent"""
    id: str
    agent_id: str
    title: str
    created_at: str


class CreationConversation(BaseModel):
    """Création d'une conversation"""
    agent_id: str
    title: Optional[str] = None


class Message(BaseModel):
    """Message dans une conversation"""
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: str


class MessageChat(BaseModel):
    """Message envoyé par l'utilisateur"""
    content: str
