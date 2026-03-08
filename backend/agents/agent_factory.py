"""
Factory pour instanciation des agents JARVIS 2.0
Architecture provider unique : Gemini (Google AI)
"""

from backend.agents.agent_config import get_agent_config
from backend.agents.base_agent import BaseAgent
from backend.agents.jarvis_maitre import JarvisMaitre
from backend.agents.architecte import Architecte
from backend.agents.testeur import Testeur

_AGENTS_CACHE: dict[str, BaseAgent] = {}


def get_agent(agent_name: str) -> BaseAgent:
    """
    Fournit une instance d'agent selon son nom.
    Le provider est sélectionné automatiquement via ProviderFactory.

    Args:
        agent_name: "BASE", "CODEUR", "VALIDATEUR", ou "JARVIS_Maître"

    Returns:
        Instance de l'agent demandé

    Raises:
        ValueError: Si l'agent demandé n'existe pas
        RuntimeError: Si la configuration provider est manquante
    """
    global _AGENTS_CACHE

    # Retourner depuis cache si existe
    if agent_name in _AGENTS_CACHE:
        return _AGENTS_CACHE[agent_name]

    # Récupérer configuration
    config = get_agent_config(agent_name)

    # Instancier agent selon type
    # Note: agent_id n'est plus utilisé, les providers gèrent leur propre authentification
    if agent_name == "JARVIS_Maître":
        agent = JarvisMaitre(
            agent_id=f"provider_{agent_name}",  # ID symbolique
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
        )
    elif agent_name == "ARCHITECTE":
        agent = Architecte(
            agent_id=f"provider_{agent_name}",
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
        )
    elif agent_name == "TESTEUR":
        agent = Testeur(
            agent_id=f"provider_{agent_name}",
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
        )
    else:
        agent = BaseAgent(
            agent_id=f"provider_{agent_name}",
            name=config["name"],
            role=config["role"],
            description=config["description"],
            permissions=config.get("permissions", ["read", "write"]),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4096),
            prompt_file=config.get("prompt_file"),
        )

    # Mettre en cache
    _AGENTS_CACHE[agent_name] = agent
    return agent


def clear_cache():
    """Vide le cache des agents (utile pour tests)"""
    global _AGENTS_CACHE
    _AGENTS_CACHE.clear()
