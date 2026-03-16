import json
import logging
from datetime import datetime
from pathlib import Path

from backend.ia.providers.provider_factory import ProviderFactory

LOG_MAX_BYTES = 5 * 1024 * 1024

logger = logging.getLogger(__name__)


class InvalidRuntimeMessageError(ValueError):
    pass


class BaseAgent:
    """
    Implémentation concrète du modèle d'agent de base.

    Responsabilités :
    - appliquer un rôle stable
    - consommer un contexte
    - produire une réponse textuelle
    - journaliser les actions en JSON Lines
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        description: str,
        permissions: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        prompt_file: str | None = None,
        api_key: str | None = None,
    ):
        self.id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.permissions = permissions or ["read", "write"]
        self.temperature = temperature or 0.7
        self.max_tokens = max_tokens or 4096
        self.state = "idle"
        self.last_finish_reason = "stop"  # Stocke le finish_reason de la dernière réponse

        self.provider = ProviderFactory.create(agent_name=name, api_key=api_key)
        self.log_file = Path("backend/logs/jarvis_audit.log")
        
        # Charger le system_prompt depuis le fichier si fourni
        self.system_prompt = self._load_system_prompt(prompt_file) if prompt_file else None

    def _load_system_prompt(self, prompt_file: str) -> str | None:
        """
        Charge le system_prompt depuis un fichier markdown.
        
        Args:
            prompt_file: Chemin relatif vers le fichier de prompt (depuis la racine du projet)
            
        Returns:
            Le contenu du prompt ou None si le fichier n'existe pas
        """
        try:
            # Résoudre le chemin depuis la racine du projet (2 niveaux au-dessus de ce fichier)
            project_root = Path(__file__).parent.parent.parent
            prompt_path = project_root / prompt_file
            if prompt_path.exists():
                content = prompt_path.read_text(encoding="utf-8")
                # Extraire le contenu après les métadonnées (après la première ligne vide)
                lines = content.split("\n")
                # Chercher la fin des métadonnées (première ligne "---" suivie d'une ligne vide)
                start_idx = 0
                for i, line in enumerate(lines):
                    if i > 0 and line.strip() == "" and i < len(lines) - 1:
                        start_idx = i + 1
                        break
                return "\n".join(lines[start_idx:]).strip()
            else:
                logger.warning(f"Fichier prompt non trouvé : {prompt_file}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors du chargement du prompt : {e}")
            return None

    def _rotate_log_if_needed(self) -> None:
        """Rotation simple : si le fichier dépasse LOG_MAX_BYTES, renommer en .old."""
        try:
            if self.log_file.exists() and self.log_file.stat().st_size > LOG_MAX_BYTES:
                old_file = self.log_file.with_suffix(".log.old")
                if old_file.exists():
                    old_file.unlink()
                self.log_file.rename(old_file)
        except Exception as e:
            print(f"Erreur lors de la rotation du log: {e}")

    def log(self, action: str, details: dict, session_id: str | None = None) -> None:
        """
        Journalise une action en format JSON Lines.

        Args:
            action: Type d'action effectuée
            details: Détails de l'action (sans données sensibles)
            session_id: Identifiant de session (optionnel)
        """
        self._rotate_log_if_needed()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.id,
            "agent_name": self.name,
            "session_id": session_id,
            "action": action,
            "state": self.state,
            "details": details,
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Erreur lors de l'écriture du log: {e}")

    async def handle(
        self, messages: list[dict], session_id: str | None = None, function_executor=None
    ) -> str:
        """
        Point d'entrée unique de l'agent.

        Args:
            messages: Liste de messages {role, content}
            session_id: Identifiant de session pour traçabilité dans les logs
            function_executor: Exécuteur de fonctions pour tool calling
            
        Returns:
            Réponse texte de l'agent (pour compatibilité ascendante)
            Note: finish_reason est stocké dans self.last_finish_reason
        """
        self.state = "working"

        try:
            if not isinstance(messages, list):
                raise InvalidRuntimeMessageError("messages must be a list")

            validated_messages: list[dict] = []
            for idx, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    raise InvalidRuntimeMessageError(f"messages[{idx}] must be an object")

                role = msg.get("role")
                content = msg.get("content")

                if role not in ("user", "assistant", "tool", "system"):
                    raise InvalidRuntimeMessageError(
                        f"messages[{idx}].role must be 'user', 'assistant', 'tool', or 'system'"
                    )
                
                # Permettre content vide pour assistant (Gemini peut retourner "" avec tool_calls)
                # Mais exiger content non vide pour user, system, tool
                if role in ("user", "system", "tool"):
                    if not isinstance(content, str) or not content.strip():
                        raise InvalidRuntimeMessageError(
                            f"messages[{idx}].content must be a non-empty string"
                        )
                else:  # role == "assistant"
                    if not isinstance(content, str):
                        raise InvalidRuntimeMessageError(
                            f"messages[{idx}].content must be a string"
                        )

                validated_messages.append({"role": role, "content": content})

            self.log(
                action="handle_request",
                details={
                    "message_count": len(messages),
                    "last_user_message": messages[-1].get("content", "")[:100] if messages else "",
                    "function_calling_enabled": function_executor is not None,
                },
                session_id=session_id,
            )

            response_data = await self._handle_with_function_calling(
                validated_messages, function_executor
            )
            
            # Extraire response et finish_reason
            if isinstance(response_data, dict):
                response_text = response_data.get("content", "")
                self.last_finish_reason = response_data.get("finish_reason", "stop")
            else:
                # Compatibilité ascendante si _handle_with_function_calling retourne string
                response_text = response_data
                self.last_finish_reason = "stop"

            self.log(
                action="handle_response",
                details={
                    "response_length": len(response_text),
                    "finish_reason": self.last_finish_reason
                },
                session_id=session_id,
            )

            self.state = "idle"
            return response_text

        except Exception as e:
            self.state = "error"
            self.log(action="handle_error", details={"error": str(e)}, session_id=session_id)
            raise

    async def _handle_with_function_calling(
        self, messages: list[dict], function_executor=None, max_iterations: int = 5
    ) -> dict:
        """
        Gère l'envoi de messages avec support du function calling.

        Args:
            messages: Messages validés
            function_executor: Exécuteur de fonctions
            max_iterations: Nombre maximum d'itérations pour function calling

        Returns:
            Dict avec {content: str, finish_reason: str}
        """
        conversation_messages = messages.copy()
        
        # Injecter le system_prompt au début si défini
        if self.system_prompt and (not conversation_messages or conversation_messages[0].get("role") != "system"):
            conversation_messages.insert(0, {"role": "system", "content": self.system_prompt})
        
        iteration = 0
        last_finish_reason = "stop"
        last_content = ""

        # Récupérer les fonctions disponibles si function_executor fourni
        functions = None
        if function_executor:
            functions = function_executor.get_available_functions()
            logger.info(f"Agent {self.name} - {len(functions)} functions available")

        while iteration < max_iterations:
            logger.info(
                f"Agent {self.name} - Iteration {iteration + 1}/{max_iterations}, "
                f"messages={len(conversation_messages)}"
            )

            # Envoyer message au provider
            response = await self.provider.send_message(
                messages=conversation_messages,
                functions=functions,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            finish_reason = response.get("finish_reason", "stop")
            last_finish_reason = finish_reason
            
            # Log détaillé pour JARVIS_Maître pour diagnostic
            if self.name == "JARVIS_Maître" and content:
                logger.info(f"Agent {self.name} - Réponse brute ({len(content)} chars)")
                
                # Vérifier présence du marqueur unique
                if "[DEMANDE_CODE_CODEUR:" in content:
                    logger.info("✅ Réponse contient [DEMANDE_CODE_CODEUR:")
                else:
                    logger.warning("❌ Réponse ne contient AUCUN marqueur de délégation")
                
                # Afficher un extrait de la réponse pour analyse
                if len(content) > 500:
                    logger.info(f"Extrait réponse: {content[:500]}...")
            
            # Conserver le dernier contenu non vide
            if content:
                last_content = content

            # Si pas de tool calls, retourner le contenu avec finish_reason
            if not tool_calls or not function_executor:
                logger.info(f"Agent {self.name} - Response: {len(content)} chars, finish_reason={finish_reason}")
                return {"content": content, "finish_reason": finish_reason}

            # Tool calls détectés
            logger.info(f"Agent {self.name} - {len(tool_calls)} tool call(s) detected")

            # Ajouter message assistant avec tool_calls
            conversation_messages.append({
                "role": "assistant",
                "content": content or "",
            })

            # Exécuter chaque tool call
            for tool_call in tool_calls:
                function_name = tool_call["name"]
                arguments = tool_call["arguments"]
                tool_call_id = tool_call["id"]

                logger.info(f"Executing function: {function_name}")

                try:
                    result = await function_executor.execute(function_name, arguments)
                    logger.info(f"Function {function_name} executed successfully")
                except Exception as e:
                    logger.error(f"Function {function_name} failed: {str(e)}")
                    result = {"success": False, "error": str(e)}

                # Ajouter résultat au format provider
                tool_result_msg = self.provider.format_tool_result(
                    tool_call_id, function_name, result
                )
                conversation_messages.append(tool_result_msg)

            iteration += 1

        # Max iterations atteintes - retourner le dernier contenu non vide
        logger.warning(f"Agent {self.name} - Max iterations ({max_iterations}) reached")
        final_content = last_content if last_content else content
        logger.info(f"Agent {self.name} - Returning final content: {len(final_content)} chars")
        return {"content": final_content, "finish_reason": last_finish_reason}
