from backend.agents.base_agent import BaseAgent
from backend.agents.agent_config import get_agent_config


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
        )
