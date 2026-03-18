"""
Interface abstraite pour tous les providers LLM
Définit le contrat commun que tous les providers doivent respecter
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseProvider(ABC):
    """
    Interface abstraite pour les providers LLM.
    
    Tous les providers doivent implémenter cette interface
    pour garantir une compatibilité totale avec le système d'agents JARVIS.
    """

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Initialise le provider.
        
        Args:
            api_key: Clé API du provider
            model: Nom du modèle à utiliser
            **kwargs: Paramètres additionnels spécifiques au provider
        """
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    async def send_message(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Envoie un message au LLM et retourne la réponse.
        
        Args:
            messages: Liste de messages [{"role": "user|assistant|tool", "content": "..."}]
            functions: Liste de fonctions disponibles pour tool calling (optionnel)
            temperature: Température de génération (0.0-1.0)
            max_tokens: Nombre maximum de tokens dans la réponse
            
        Returns:
            Dict contenant:
                - content: str (texte de la réponse)
                - tool_calls: List[Dict] (appels de fonctions si présents)
                - finish_reason: str (raison de fin: "stop", "tool_calls", etc.)
                
        Raises:
            Exception: Si l'appel API échoue
        """
        pass

    @abstractmethod
    def format_functions(self, functions: List[Dict]) -> Any:
        """
        Convertit les fonctions du format JARVIS vers le format du provider.
        
        Format JARVIS (standard) :
        {
            "name": "function_name",
            "description": "...",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        
        Args:
            functions: Liste de fonctions au format JARVIS
            
        Returns:
            Fonctions au format attendu par le provider
        """
        pass

    @abstractmethod
    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict]:
        """
        Extrait les tool calls de la réponse du provider.
        
        Format retourné (standard JARVIS) :
        [
            {
                "id": "call_123",
                "name": "function_name",
                "arguments": {"arg1": "value1"}
            }
        ]
        
        Args:
            response: Réponse brute du provider
            
        Returns:
            Liste des tool calls au format JARVIS
        """
        pass

    @abstractmethod
    def format_tool_result(self, tool_call_id: str, function_name: str, result: Any) -> Dict:
        """
        Formate le résultat d'un tool call pour l'envoyer au provider.
        
        Args:
            tool_call_id: ID du tool call
            function_name: Nom de la fonction exécutée
            result: Résultat de l'exécution
            
        Returns:
            Message au format attendu par le provider
        """
        pass

    def validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """
        Valide le format des messages avant envoi.
        
        Args:
            messages: Liste de messages à valider
            
        Raises:
            ValueError: Si le format est invalide
        """
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")

        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"messages[{idx}] must be a dict")

            role = msg.get("role")
            content = msg.get("content")

            if role not in ("user", "assistant", "tool", "system"):
                raise ValueError(
                    f"messages[{idx}].role must be 'user', 'assistant', 'tool', or 'system'"
                )

            if not isinstance(content, str):
                raise ValueError(f"messages[{idx}].content must be a string")
