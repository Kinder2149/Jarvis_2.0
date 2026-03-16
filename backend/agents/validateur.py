import logging
from backend.agents.base_agent import BaseAgent
from backend.agents.agent_config import get_agent_config

logger = logging.getLogger(__name__)


class Validateur(BaseAgent):
    """
    Agent VALIDATEUR — Spécialiste contrôle qualité multi-niveaux.

    Rôle :
    - Vérifier le code produit par CODEUR
    - Vérifier les tests produits par TESTEUR
    - Vérifier la cohérence avec l'architecture proposée par ARCHITECTE
    - Détecter bugs, erreurs syntaxiques, incohérences, violations d'architecture
    - Signaler les problèmes (ne PAS corriger)
    - Exécuter la phase Remise en Question du cycle ARRF

    Responsabilités :
    - Validation architecture (structure fichiers, responsabilités, imports)
    - Validation code (syntaxe, logique, cohérence, conventions)
    - Validation tests (couverture, cas limites, assertions)
    - Génération rapport détaillé (STATUT: VALIDE ou INVALIDE)
    - Liste problèmes bloquants avec fichier + ligne + description
    """

    def __init__(
        self,
        agent_id: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ):
        # Récupérer la config pour obtenir le prompt_file
        config = get_agent_config("VALIDATEUR")
        
        super().__init__(
            agent_id=agent_id,
            name=config["name"],
            role=config["role"],
            description=config["description"],
            permissions=config.get("permissions", ["read"]),
            temperature=temperature or config.get("temperature", 0.5),
            max_tokens=max_tokens or config.get("max_tokens", 4096),
            prompt_file=config.get("prompt_file"),
            api_key=api_key,
        )
        
        # Log pour vérifier que le prompt contient les critères de validation
        if self.system_prompt:
            logger.info(f"VALIDATEUR prompt chargé ({len(self.system_prompt)} chars)")
            
            # Vérifier présence des sections critiques
            if "VÉRIFICATIONS OBLIGATOIRES" in self.system_prompt:
                logger.info("✅ Prompt contient section VÉRIFICATIONS OBLIGATOIRES")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS section VÉRIFICATIONS OBLIGATOIRES")
            
            if "STATUT: VALIDE" in self.system_prompt or "STATUT: INVALIDE" in self.system_prompt:
                logger.info("✅ Prompt contient format STATUT (VALIDE/INVALIDE)")
            else:
                logger.warning("❌ Prompt NE CONTIENT PAS format STATUT")
