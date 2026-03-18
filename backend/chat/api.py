"""
API simplifiée JARVIS 2.0 - Chat Simple Multi-Agents
Routes minimalistes : conversations + messages + agents
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException

from backend.agents.agent_config import list_available_agents
from backend.agents.agent_factory import get_agent
from backend.chat.modeles import MessageChat, Conversation, CreationConversation, Message
from backend.chat.stockage import StockageConversations

logger = logging.getLogger(__name__)
router = APIRouter()

# Instance globale du stockage (sera initialisée dans app.py)
stockage_conversations: StockageConversations = None


def initialiser_stockage_conversations(stockage: StockageConversations):
    """Initialise le stockage de conversations"""
    global stockage_conversations
    stockage_conversations = stockage


@router.post("/api/conversations", response_model=Conversation)
async def create_conversation(conv: CreationConversation):
    """
    Crée une nouvelle conversation avec un agent
    """
    try:
        conversation = stockage_conversations.create_conversation(
            agent_id=conv.agent_id,
            title=conv.title
        )
        return conversation
    except Exception as e:
        logger.exception(f"Erreur création conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversations", response_model=list[Conversation])
async def list_conversations():
    """
    Liste toutes les conversations
    """
    try:
        conversations = stockage_conversations.list_conversations()
        return conversations
    except Exception as e:
        logger.exception(f"Erreur liste conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """
    Récupère une conversation par ID
    """
    try:
        conversation = stockage_conversations.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except Exception as e:
        logger.exception(f"Erreur récupération conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Supprime une conversation et tous ses messages
    """
    try:
        success = stockage_conversations.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        logger.exception(f"Erreur suppression conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversations/{conversation_id}/messages", response_model=list[Message])
async def get_messages(conversation_id: str, limit: Optional[int] = None):
    """
    Récupère les messages d'une conversation
    """
    try:
        messages = stockage_conversations.get_messages(conversation_id, limit)
        return messages
    except Exception as e:
        logger.exception(f"Erreur récupération messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, msg: MessageChat):
    """
    Envoie un message à l'agent et récupère sa réponse
    
    Args:
        conversation_id: ID de la conversation
        msg: Message à envoyer
    
    Returns:
        Réponse de l'agent avec l'historique
    """
    try:
        # Vérifier que la conversation existe
        conversation = stockage_conversations.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Ajouter message utilisateur
        stockage_conversations.add_message(conversation_id, "user", msg.content)
        
        # Récupérer historique conversation
        messages_history = stockage_conversations.get_conversation_history(conversation_id)
        
        # Récupérer agent
        agent = get_agent(conversation["agent_id"])
        
        # Envoyer à l'agent
        response = await agent.handle(messages_history, session_id=conversation_id)
        
        # Sauvegarder réponse assistant
        stockage_conversations.add_message(conversation_id, "assistant", response)
        
        return {
            "response": response,
            "conversation_id": conversation_id,
            "agent_id": conversation["agent_id"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur envoi message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents")
def get_agents():
    """
    Liste tous les agents disponibles
    """
    try:
        return {"agents": list_available_agents()}
    except Exception as e:
        logger.exception(f"Erreur liste agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
