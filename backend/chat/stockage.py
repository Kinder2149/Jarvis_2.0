"""
ConversationStore - JARVIS 2.0
Gestion des conversations et messages avec stockage JSON unique
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class StockageConversations:
    """
    Gestionnaire de conversations avec stockage JSON unique
    
    Structure JSON :
    {
        "conversations": {
            "conv_id": {
                "id": "conv_id",
                "agent_id": "JARVIS_MAITRE",
                "title": "Ma conversation",
                "created_at": "2026-03-18T20:00:00"
            }
        },
        "messages": {
            "msg_id": {
                "id": "msg_id",
                "conversation_id": "conv_id",
                "role": "user",
                "content": "Hello",
                "timestamp": "2026-03-18T20:00:00"
            }
        }
    }
    """
    
    def __init__(self, chemin_stockage: str = "backend/data/conversations.json"):
        self.chemin_stockage = Path(chemin_stockage)
        self.chemin_stockage.parent.mkdir(parents=True, exist_ok=True)
        self.donnees = self._charger_donnees()
    
    def _charger_donnees(self) -> Dict:
        """Charge les données depuis le fichier JSON"""
        if not self.chemin_stockage.exists():
            return {"conversations": {}, "messages": {}}
        
        try:
            with open(self.chemin_stockage, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur chargement conversations: {e}")
            return {"conversations": {}, "messages": {}}
    
    def _sauvegarder_donnees(self):
        """Sauvegarde les données dans le fichier JSON"""
        try:
            with open(self.chemin_stockage, 'w', encoding='utf-8') as f:
                json.dump(self.donnees, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde conversations: {e}")
    
    def create_conversation(
        self,
        agent_id: str,
        title: Optional[str] = None
    ) -> Dict:
        """
        Crée une nouvelle conversation
        
        Args:
            agent_id: ID de l'agent (JARVIS_MAITRE, ARCHITECTE, etc.)
            title: Titre optionnel de la conversation
        
        Returns:
            Conversation créée
        """
        conversation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conversation = {
            "id": conversation_id,
            "agent_id": agent_id,
            "title": title or f"Conversation avec {agent_id}",
            "created_at": now
        }
        
        self.donnees["conversations"][conversation_id] = conversation
        self._sauvegarder_donnees()
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Récupère une conversation par ID
        
        Args:
            conversation_id: ID de la conversation
        
        Returns:
            Conversation si trouvée, None sinon
        """
        return self.donnees["conversations"].get(conversation_id)
    
    def list_conversations(self) -> List[Dict]:
        """
        Liste toutes les conversations
        
        Returns:
            Liste des conversations triées par date (plus récente en premier)
        """
        conversations = list(self.donnees["conversations"].values())
        conversations.sort(key=lambda c: c["created_at"], reverse=True)
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Supprime une conversation et tous ses messages
        
        Args:
            conversation_id: ID de la conversation
        
        Returns:
            True si supprimée, False si non trouvée
        """
        if conversation_id not in self.donnees["conversations"]:
            return False
        
        # Supprimer la conversation
        del self.donnees["conversations"][conversation_id]
        
        # Supprimer tous les messages associés
        message_ids_to_delete = [
            msg_id for msg_id, msg in self.donnees["messages"].items()
            if msg["conversation_id"] == conversation_id
        ]
        
        for msg_id in message_ids_to_delete:
            del self.donnees["messages"][msg_id]
        
        self._sauvegarder_donnees()
        return True
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> Dict:
        """
        Ajoute un message à une conversation
        
        Args:
            conversation_id: ID de la conversation
            role: Rôle (user ou assistant)
            content: Contenu du message
        
        Returns:
            Message créé
        """
        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        message = {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "timestamp": now
        }
        
        self.donnees["messages"][message_id] = message
        self._sauvegarder_donnees()
        
        return message
    
    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Récupère les messages d'une conversation
        
        Args:
            conversation_id: ID de la conversation
            limit: Nombre maximum de messages (None = tous)
        
        Returns:
            Liste des messages triés par timestamp (plus ancien en premier)
        """
        messages = [
            msg for msg in self.donnees["messages"].values()
            if msg["conversation_id"] == conversation_id
        ]
        
        messages.sort(key=lambda m: m["timestamp"])
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """
        Récupère l'historique de conversation au format API (role + content)
        
        Args:
            conversation_id: ID de la conversation
        
        Returns:
            Liste de messages au format {"role": "user/assistant", "content": "..."}
        """
        messages = self.get_messages(conversation_id)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
