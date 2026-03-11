"""
Provider Google Gemini pour JARVIS 2.0
Utilisé pour JARVIS_Maître (orchestrateur)
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

from backend.ia.providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """
    Provider pour Google Gemini API.
    
    Caractéristiques :
    - Contexte large (1M-2M tokens selon modèle)
    - Tool calling natif
    - Multimodal (texte + vision)
    - Délai adaptatif pour respecter quotas RPM
    """

    # Dictionnaire pour gérer le délai entre requêtes par clé API (chaque agent a son quota)
    _last_request_times: Dict[str, datetime] = {}

    def __init__(self, api_key: str, model: str, **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        # Stocker la clé API pour le rate limiting par clé
        self.api_key = api_key
        
        # Stocker le nom du modèle pour recréation
        self.model_name = model
        
        # Délai adaptatif selon l'agent (depuis agent_config.py)
        self._min_delay_seconds = kwargs.get('min_delay_seconds', 4.0)
        
        genai.configure(api_key=api_key)
        
        logger.info(f"GeminiProvider initialized: model={model}, min_delay={self._min_delay_seconds}s")

    async def send_message(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Envoie un message à Gemini avec délai adaptatif pour respecter quotas RPM.
        
        Note : Gemini utilise un format de conversation différent.
        Le premier message "system" est converti en contexte.
        """
        self.validate_messages(messages)

        # Délai adaptatif pour respecter quota RPM
        await self._apply_rate_limit_delay()

        # Convertir messages au format Gemini
        gemini_messages = self._convert_messages(messages)
        
        # Préparer configuration génération
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Préparer tools si fonctions fournies
        tools = None
        if functions:
            tools = [Tool(function_declarations=self.format_functions(functions))]

        try:
            # Reconfigurer genai pour chaque requête (évite event loop fermé)
            genai.configure(api_key=self.api_key)
            
            # Créer un nouveau GenerativeModel pour chaque requête
            # Évite problème "Event loop is closed" en tests batch
            client = genai.GenerativeModel(self.model_name)
            
            # Gemini utilise generate_content avec historique
            chat = client.start_chat(history=gemini_messages[:-1])
            
            response = await chat.send_message_async(
                gemini_messages[-1]["parts"],
                generation_config=generation_config,
                tools=tools,
            )

            # Extraire contenu et tool calls
            content = ""
            tool_calls = []
            finish_reason = "stop"

            if response.candidates:
                candidate = response.candidates[0]
                
                # Extraire finish_reason réel de Gemini
                if hasattr(candidate, "finish_reason"):
                    gemini_finish_reason = str(candidate.finish_reason)
                    # Gemini retourne "FinishReason.MAX_TOKENS" ou "FinishReason.STOP"
                    if "MAX_TOKENS" in gemini_finish_reason:
                        finish_reason = "MAX_TOKENS"
                    elif "STOP" in gemini_finish_reason:
                        finish_reason = "stop"
                
                # Extraire texte
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "text"):
                            content += part.text
                        elif hasattr(part, "function_call"):
                            # Tool call détecté
                            fc = part.function_call
                            tool_calls.append({
                                "id": f"call_{len(tool_calls)}",
                                "name": fc.name,
                                "arguments": dict(fc.args),
                            })
                            finish_reason = "tool_calls"

            logger.info(
                f"Gemini response: {len(content)} chars, {len(tool_calls)} tool_calls, finish_reason={finish_reason}"
            )
            
            # Log détaillé si réponse vide
            if not content and not tool_calls:
                logger.warning(f"Gemini returned empty response! Response object: {response}")
                if response.candidates:
                    logger.warning(f"Candidate finish_reason: {response.candidates[0].finish_reason}")
                    logger.warning(f"Candidate content parts: {response.candidates[0].content.parts}")

            return {
                "content": content,
                "tool_calls": tool_calls,
                "finish_reason": finish_reason,
            }

        except Exception as e:
            logger.error(f"Gemini API error: {type(e).__name__} - {str(e)}")
            raise

    def format_functions(self, functions: List[Dict]) -> List[FunctionDeclaration]:
        """
        Convertit fonctions JARVIS → format Gemini FunctionDeclaration.
        
        Gemini utilise des FunctionDeclaration avec types en MAJUSCULES.
        """
        gemini_functions = []
        
        for func in functions:
            # Convertir types JSON → types Gemini
            parameters = self._convert_schema_to_gemini(func.get("parameters", {}))
            
            gemini_func = FunctionDeclaration(
                name=func["name"],
                description=func.get("description", ""),
                parameters=parameters,
            )
            gemini_functions.append(gemini_func)

        logger.debug(f"Formatted {len(gemini_functions)} functions for Gemini")
        return gemini_functions

    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict]:
        """
        Extrait tool calls de la réponse Gemini.
        
        Note : Déjà fait dans send_message, cette méthode est pour compatibilité.
        """
        return response.get("tool_calls", [])

    def format_tool_result(self, tool_call_id: str, function_name: str, result: Any) -> Dict:
        """
        Formate résultat tool call pour Gemini.
        
        Gemini attend un message avec role="function".
        """
        return {
            "role": "function",
            "parts": [{"function_response": {"name": function_name, "response": result}}],
        }

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """
        Convertit messages JARVIS → format Gemini.
        
        Gemini utilise :
        - role: "user" ou "model" (pas "assistant")
        - parts: [{"text": "..."}] au lieu de content
        """
        gemini_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # Mapper rôles
            if role == "assistant":
                role = "model"
            elif role == "system":
                # Gemini n'a pas de role "system", on l'ajoute comme premier message user
                role = "user"
            elif role == "tool":
                # Tool results sont gérés différemment
                continue

            gemini_messages.append({
                "role": role,
                "parts": [{"text": content}],
            })

        return gemini_messages

    def _convert_schema_to_gemini(self, schema: Dict) -> Dict:
        """
        Convertit JSON Schema → Gemini Schema.
        
        Différences :
        - Types en MAJUSCULES (STRING, INTEGER, OBJECT, ARRAY)
        - Format légèrement différent
        """
        if not schema:
            return {}

        gemini_schema = {"type": schema.get("type", "object").upper()}

        if "properties" in schema:
            gemini_schema["properties"] = {}
            for prop_name, prop_schema in schema["properties"].items():
                gemini_schema["properties"][prop_name] = self._convert_schema_to_gemini(
                    prop_schema
                )

        if "description" in schema:
            gemini_schema["description"] = schema["description"]

        if "required" in schema:
            gemini_schema["required"] = schema["required"]

        if "items" in schema:
            gemini_schema["items"] = self._convert_schema_to_gemini(schema["items"])

        return gemini_schema

    async def _apply_rate_limit_delay(self) -> None:
        """
        Applique un délai adaptatif pour respecter le quota RPM de Gemini.
        
        Calcul : 60s / 15 RPM = 4s entre requêtes minimum
        Si dernière requête < 4s, attend le temps restant.
        
        Note : Désactivé pendant les tests pytest pour éviter problèmes d'event loop.
        Utilise la clé API comme identifiant unique (chaque agent a son propre quota).
        """
        import sys
        
        # Désactiver rate limiting si pytest est chargé (mode test)
        if 'pytest' in sys.modules:
            logger.debug("Rate limiting désactivé (pytest détecté)")
            return
        
        # Utiliser la clé API comme identifiant unique pour le rate limiting
        if self.api_key in GeminiProvider._last_request_times:
            elapsed = (datetime.now() - GeminiProvider._last_request_times[self.api_key]).total_seconds()
            
            if elapsed < self._min_delay_seconds:
                wait_time = self._min_delay_seconds - elapsed
                logger.info(
                    f"GeminiProvider: attente {wait_time:.1f}s pour respecter quota RPM "
                    f"(15 req/min = {self._min_delay_seconds}s entre requêtes)"
                )
                await asyncio.sleep(wait_time)
        
        # Enregistrer timestamp de cette requête pour cette clé API
        GeminiProvider._last_request_times[self.api_key] = datetime.now()
