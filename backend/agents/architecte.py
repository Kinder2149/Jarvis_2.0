import logging
from backend.agents.base_agent import BaseAgent
from backend.agents.agent_config import get_agent_config

logger = logging.getLogger(__name__)


class Architecte(BaseAgent):
    """
    Agent ARCHITECTE — Spécialiste conception architecture logicielle.

    Rôle :
    - Concevoir l'architecture AVANT la génération de code
    - Proposer une structure de fichiers claire et justifiée
    - Exécuter les phases Analyse et Réflexion du cycle ARRF
    - Communiquer en langage simple pour un non-codeur

    Responsabilités :
    - Analyser le besoin utilisateur
    - Identifier les composants nécessaires
    - Proposer une structure de fichiers avec responsabilités claires
    - Créer un document architecture.md détaillé
    - Lister les fichiers à créer avec leur rôle
    - Justifier les choix architecturaux
    """

    def __init__(
        self,
        agent_id: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ):
        # Récupérer la config pour obtenir le prompt_file
        config = get_agent_config("ARCHITECTE")
        
        super().__init__(
            agent_id=agent_id,
            name="ARCHITECTE",
            role="Agent de conception architecture",
            description=(
                "Agent spécialisé dans la conception d'architecture logicielle. "
                "Propose une structure de fichiers claire et justifiée AVANT la génération de code. "
                "Exécute les phases Analyse et Réflexion du cycle ARRF."
            ),
            permissions=["read"],
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_file=config.get("prompt_file"),
            api_key=api_key,
        )
        
        # Log pour vérifier que le prompt contient les instructions ARCHITECTE
        if self.system_prompt:
            logger.info(f"ARCHITECTE prompt chargé ({len(self.system_prompt)} chars)")
            
            # Vérifier présence des sections critiques
            if "ANALYSE" in self.system_prompt and "RÉFLEXION" in self.system_prompt:
                logger.info("✅ Prompt contient sections ANALYSE et RÉFLEXION")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS sections ANALYSE/RÉFLEXION")
            
            if "STRUCTURE FICHIERS" in self.system_prompt or "structure de fichiers" in self.system_prompt:
                logger.info("✅ Prompt contient instructions structure fichiers")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS instructions structure fichiers")
