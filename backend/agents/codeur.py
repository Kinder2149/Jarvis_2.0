import logging
from backend.agents.base_agent import BaseAgent
from backend.agents.agent_config import get_agent_config

logger = logging.getLogger(__name__)


class Codeur(BaseAgent):
    """
    Agent CODEUR — Spécialiste génération de code source.

    Rôle :
    - Générer du code source propre et fonctionnel
    - Exécuter les instructions précises de l'ARCHITECTE
    - Ne PAS générer les tests (délégué à TESTEUR)
    - Ne PAS prendre de décisions architecturales
    - Exécuter la phase Réalisation du cycle ARRF

    Responsabilités :
    - Implémenter l'architecture définie
    - Respecter les patterns RAG fournis
    - Générer du code avec imports corrects
    - Utiliser Pydantic v2 API
    - Valider les types d'entrée
    - Code minimal et fonctionnel
    """

    def __init__(
        self,
        agent_id: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ):
        # Récupérer la config pour obtenir le prompt_file
        config = get_agent_config("CODEUR")
        
        super().__init__(
            agent_id=agent_id,
            name=config["name"],
            role=config["role"],
            description=config["description"],
            permissions=config.get("permissions", ["read", "write", "code"]),
            temperature=temperature or config.get("temperature", 0.3),
            max_tokens=max_tokens or config.get("max_tokens", 16384),
            prompt_file=config.get("prompt_file"),
            api_key=api_key,
        )
        
        # Log pour vérifier que le prompt contient les règles CODEUR
        if self.system_prompt:
            logger.info(f"CODEUR prompt chargé ({len(self.system_prompt)} chars)")
            
            # Vérifier présence des règles critiques
            if "RÈGLE 1" in self.system_prompt and "Storage JSON" in self.system_prompt:
                logger.info("✅ Prompt contient RÈGLE 1 (Storage JSON)")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS RÈGLE 1 (Storage JSON)")
            
            if "Pydantic v2" in self.system_prompt:
                logger.info("✅ Prompt contient règles Pydantic v2")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS règles Pydantic v2")
