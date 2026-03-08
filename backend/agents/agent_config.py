"""
Configuration des agents JARVIS 2.0
Mapping agent_name → variable .env + métadonnées
"""

AGENT_CONFIGS = {
    "BASE": {
        "name": "BASE",
        "role": "Assistant générique",
        "description": "Agent neutre servant de worker pour tâches génériques. Template uniquement.",
        "permissions": ["read", "write"],
        "type": "worker",
        "temperature": 0.7,
        "max_tokens": 4096,
        "prompt_file": "config_agents/BASE.md",
        "min_delay_seconds": 6.0,
    },
    "ARCHITECTE": {
        "name": "ARCHITECTE",
        "role": "Agent de conception architecture",
        "description": (
            "Agent spécialisé dans la conception d'architecture logicielle. "
            "Propose une structure de fichiers claire et justifiée AVANT la génération de code. "
            "Exécute les phases Analyse et Réflexion du cycle ARRF."
        ),
        "permissions": ["read"],
        "type": "architect",
        "temperature": 0.3,
        "max_tokens": 8192,
        "prompt_file": "config_agents/ARCHITECTE.md",
        "min_delay_seconds": 8.0,
    },
    "CODEUR": {
        "name": "CODEUR",
        "role": "Agent spécialisé code",
        "description": (
            "Agent spécialisé dans l'écriture de code source uniquement. "
            "Exécute des instructions précises, produit du code propre et fonctionnel. "
            "Ne génère PAS les tests (délégué à TESTEUR). Ne prend aucune décision architecturale."
        ),
        "permissions": ["read", "write", "code"],
        "type": "worker",
        "temperature": 0.3,
        "max_tokens": 16384,
        "prompt_file": "config_agents/CODEUR.md",
        "min_delay_seconds": 10.0,
    },
    "TESTEUR": {
        "name": "TESTEUR",
        "role": "Agent spécialisé tests",
        "description": (
            "Agent spécialisé dans la génération de tests exhaustifs. "
            "Couvre tous les cas : nominal, limites, erreurs, edge cases. "
            "Vise 80%+ de couverture de code. Exécute les phases Réflexion et Fixation du cycle ARRF."
        ),
        "permissions": ["read", "write", "test"],
        "type": "tester",
        "temperature": 0.5,
        "max_tokens": 8192,
        "prompt_file": "config_agents/TESTEUR.md",
        "min_delay_seconds": 8.0,
    },
    "VALIDATEUR": {
        "name": "VALIDATEUR",
        "role": "Agent de contrôle qualité multi-niveaux",
        "description": (
            "Agent spécialisé dans la vérification de la qualité du code, des tests, et de l'architecture. "
            "Détecte les bugs, erreurs syntaxiques, incohérences, et violations d'architecture. "
            "Signale les problèmes sans corriger le code. Exécute la phase Remise en Question du cycle ARRF."
        ),
        "permissions": ["read"],
        "type": "validator",
        "temperature": 0.5,
        "max_tokens": 4096,
        "prompt_file": "config_agents/VALIDATEUR.md",
        "min_delay_seconds": 6.0,
    },
    "JARVIS_Maître": {
        "name": "JARVIS_Maître",
        "role": "Assistant personnel principal",
        "description": (
            "Assistant IA personnel de Val C. Interface centrale du système JARVIS. "
            "Orchestre le workflow des 5 agents spécialisés. "
            "Répond de manière claire et structurée, traduit le technique en langage accessible. "
            "Exécute le cycle ARRF complet."
        ),
        "permissions": ["read", "write", "orchestrate"],
        "type": "orchestrator",
        "temperature": 0.3,
        "max_tokens": 4096,
        "prompt_file": "config_agents/JARVIS_MAITRE.md",
        "min_delay_seconds": 4.0,
    },
}


def get_agent_config(agent_name: str) -> dict:
    """
    Récupère la configuration d'un agent.

    Args:
        agent_name: Nom de l'agent ("BASE" ou "JARVIS_Maître")

    Returns:
        Configuration de l'agent

    Raises:
        ValueError: Si l'agent n'existe pas
    """
    if agent_name not in AGENT_CONFIGS:
        available = ", ".join(AGENT_CONFIGS.keys())
        raise ValueError(f"Agent inconnu: {agent_name}. Agents disponibles: {available}")
    return AGENT_CONFIGS[agent_name]


def list_available_agents() -> list[dict]:
    """
    Liste tous les agents disponibles avec leurs métadonnées.

    Returns:
        Liste des agents avec id, name, role, description
    """
    return [
        {
            "id": name,
            "name": config["name"],
            "role": config["role"],
            "description": config["description"],
        }
        for name, config in AGENT_CONFIGS.items()
    ]


def list_agents_detailed() -> list[dict]:
    """
    Liste tous les agents avec toutes leurs couches de configuration.

    Returns:
        Liste complète : config locale, permissions, paramètres, provider, modèle
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    # Mapping des modèles par agent depuis .env
    model_mapping = {
        "JARVIS_Maître": os.getenv("JARVIS_MAITRE_MODEL", "gemini-2.5-pro"),
        "ARCHITECTE": os.getenv("ARCHITECTE_MODEL", "gemini-2.5-pro"),
        "CODEUR": os.getenv("CODEUR_MODEL", "gemini-2.5-pro"),
        "TESTEUR": os.getenv("TESTEUR_MODEL", "gemini-2.0-flash"),
        "VALIDATEUR": os.getenv("VALIDATEUR_MODEL", "gemini-3.1-pro-preview"),
        "BASE": os.getenv("BASE_MODEL", "gemini-2.5-pro"),
    }
    
    agents = []
    for name, config in AGENT_CONFIGS.items():
        agents.append(
            {
                "id": name,
                "name": config["name"],
                "role": config["role"],
                "description": config["description"],
                "type": config["type"],
                "permissions": config["permissions"],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"],
                "provider": "gemini",
                "model": model_mapping.get(name, "gemini-2.5-pro"),
                "env_var": f"{name.upper().replace('Î', 'I').replace('È', 'E')}_MODEL" if name != "JARVIS_Maître" else "JARVIS_MAITRE_MODEL",
            }
        )

    return agents
