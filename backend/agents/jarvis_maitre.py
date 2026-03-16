import logging
from backend.agents.base_agent import BaseAgent
from backend.agents.agent_config import get_agent_config

logger = logging.getLogger(__name__)


class JarvisMaitre(BaseAgent):
    """
    Agent JARVIS_Maître — Assistant personnel principal de Val C.

    Rôle actuel (local/perso) :
    - Interface centrale entre l'utilisateur et le système JARVIS
    - Réponses claires, structurées, en français
    - Traducteur : reformule le technique en langage accessible
    - Rigoureux : méthodologie Audit → Plan → Validation → Exécution → Documentation

    Responsabilités futures (non activées) :
    - Orchestration réelle des agents spécialisés
    - Routage intelligent des requêtes
    - Gestion des conflits entre agents
    """

    def __init__(
        self,
        agent_id: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ):
        # Récupérer la config pour obtenir le prompt_file
        config = get_agent_config("JARVIS_Maître")
        
        super().__init__(
            agent_id=agent_id,
            name="JARVIS_Maître",
            role="Assistant personnel principal",
            description=(
                "Assistant IA personnel de Val C. Interface centrale du système JARVIS. "
                "Répond de manière claire et structurée, traduit le technique en langage accessible."
            ),
            permissions=["read", "write", "orchestrate"],
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_file=config.get("prompt_file"),
            api_key=api_key,
        )
        
        # Log pour vérifier que le prompt contient les nouvelles instructions
        if self.system_prompt:
            prompt_preview = self.system_prompt[:800] if len(self.system_prompt) > 800 else self.system_prompt
            logger.info(f"JARVIS_Maître prompt chargé ({len(self.system_prompt)} chars)")
            
            # Vérifier présence du marqueur unique
            if "[DEMANDE_CODE_CODEUR:" in self.system_prompt:
                logger.info("✅ Prompt contient [DEMANDE_CODE_CODEUR:")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS [DEMANDE_CODE_CODEUR:")
            
            # Vérifier présence section workflow unique
            if "WORKFLOW UNIQUE" in self.system_prompt:
                logger.info("✅ Prompt contient section 'WORKFLOW UNIQUE'")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS la section 'WORKFLOW UNIQUE'")
