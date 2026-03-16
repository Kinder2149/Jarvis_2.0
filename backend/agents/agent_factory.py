"""
Factory pour instanciation des agents JARVIS 2.0
Architecture provider unique : Gemini (Google AI)
"""

import logging
import os

from backend.agents.agent_config import get_agent_config
from backend.agents.base_agent import BaseAgent
from backend.agents.jarvis_maitre import JarvisMaitre
from backend.agents.architecte import Architecte
from backend.agents.codeur import Codeur
from backend.agents.testeur import Testeur
from backend.agents.validateur import Validateur

logger = logging.getLogger(__name__)

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

    # Récupérer clé API spécifique pour cet agent (avec fallback sur GEMINI_API_KEY)
    api_key_env = config.get("api_key_env", "GEMINI_API_KEY")
    api_key = os.getenv(api_key_env) or os.getenv("GEMINI_API_KEY")
    
    # Log diagnostic clé API (avant vérification pour tracer même en cas d'erreur)
    print(f"🔑 [AGENT_FACTORY] Agent {agent_name}: variable={api_key_env}, clé={'présente' if api_key else 'MANQUANTE'}")
    
    if not api_key:
        raise RuntimeError(f"Aucune clé API trouvée pour {agent_name} (variable {api_key_env} ou GEMINI_API_KEY)")
    
    logger.info(f"Agent {agent_name}: utilise clé API depuis {api_key_env}")
    
    # Instancier agent selon type avec clé API spécifique
    if agent_name == "JARVIS_Maître":
        agent = JarvisMaitre(
            agent_id=f"provider_{agent_name}",
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
            api_key=api_key,
        )
    elif agent_name == "ARCHITECTE":
        agent = Architecte(
            agent_id=f"provider_{agent_name}",
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
            api_key=api_key,
        )
    elif agent_name == "CODEUR":
        agent = Codeur(
            agent_id=f"provider_{agent_name}",
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
            api_key=api_key,
        )
    elif agent_name == "TESTEUR":
        agent = Testeur(
            agent_id=f"provider_{agent_name}",
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
            api_key=api_key,
        )
    elif agent_name == "VALIDATEUR":
        agent = Validateur(
            agent_id=f"provider_{agent_name}",
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
            api_key=api_key,
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
            api_key=api_key,
        )

    # Mettre en cache
    _AGENTS_CACHE[agent_name] = agent
    return agent


def clear_cache():
    """Vide le cache des agents (utile pour tests)"""
    global _AGENTS_CACHE
    _AGENTS_CACHE.clear()
