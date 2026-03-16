import logging
from backend.agents.base_agent import BaseAgent
from backend.agents.agent_config import get_agent_config

logger = logging.getLogger(__name__)


class Testeur(BaseAgent):
    """
    Agent TESTEUR — Spécialiste génération de tests exhaustifs.

    Rôle :
    - Générer des tests exhaustifs pour le code produit par CODEUR
    - Couvrir tous les cas : nominal, limites, erreurs, edge cases
    - Viser 80%+ de couverture de code
    - Exécuter les phases Réflexion et Fixation du cycle ARRF

    Responsabilités :
    - Analyser le code source fourni
    - Identifier toutes les fonctions/méthodes publiques
    - Lister les cas de test nécessaires
    - Générer les fichiers de tests avec structure AAA (Arrange, Act, Assert)
    - Ajouter fixtures/mocks si nécessaire
    - Vérifier la couverture (80%+ visé)
    """

    def __init__(
        self,
        agent_id: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ):
        # Récupérer la config pour obtenir le prompt_file
        config = get_agent_config("TESTEUR")
        
        super().__init__(
            agent_id=agent_id,
            name="TESTEUR",
            role="Agent spécialisé tests",
            description=(
                "Agent spécialisé dans la génération de tests exhaustifs. "
                "Couvre tous les cas : nominal, limites, erreurs, edge cases. "
                "Vise 80%+ de couverture de code. Exécute les phases Réflexion et Fixation du cycle ARRF."
            ),
            permissions=["read", "write", "test"],
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_file=config.get("prompt_file"),
            api_key=api_key,
        )
        
        # Log pour vérifier que le prompt contient les instructions TESTEUR
        if self.system_prompt:
            logger.info(f"TESTEUR prompt chargé ({len(self.system_prompt)} chars)")
            
            # Vérifier présence des sections critiques
            if "80%" in self.system_prompt or "couverture" in self.system_prompt:
                logger.info("✅ Prompt contient objectif couverture 80%")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS objectif couverture")
            
            if "AAA" in self.system_prompt or "Arrange" in self.system_prompt:
                logger.info("✅ Prompt contient structure AAA (Arrange, Act, Assert)")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS structure AAA")
