"""
Tests unitaires pour l'agent ARCHITECTE.

Teste l'agent ARCHITECTE isolément pour vérifier :
- Capacité à proposer une architecture
- Qualité des justifications
- Format de la réponse
"""

import pytest
from backend.agents.agent_factory import get_agent

@pytest.mark.live
@pytest.mark.asyncio
async def test_architecte_projet_simple():
    """Test ARCHITECTE sur un projet simple (calculatrice)."""
    
    # Récupérer l'agent
    architecte = get_agent("ARCHITECTE")
    
    # Préparer le message
    messages = [
        {"role": "system", "content": architecte.system_prompt},
        {"role": "user", "content": """Propose une architecture pour une calculatrice Python simple.

Fonctionnalités :
- Addition
- Soustraction
- Multiplication
- Division

Contraintes :
- Code simple et clair
- Tests unitaires
- Gestion erreurs (division par zéro)"""}
    ]
    
    # Appeler l'agent
    response = await architecte.handle(messages, session_id="test_architecte_simple")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    assert len(response) > 200, f"Réponse trop courte ({len(response)} chars)"
    
    # Vérifier mentions de fichiers
    response_lower = response.lower()
    assert "calculatrice" in response_lower or "calculator" in response_lower, "Fichier principal non mentionné"
    assert "test" in response_lower, "Tests non mentionnés"
    
    # Vérifier structure
    assert "fichier" in response_lower or "file" in response_lower, "Structure fichiers non mentionnée"
    
    print(f"\n✅ ARCHITECTE - Projet simple : {len(response)} chars")
    print(f"Extrait : {response[:300]}...")


@pytest.mark.live
@pytest.mark.asyncio
async def test_architecte_projet_complexe():
    """Test ARCHITECTE sur un projet complexe (API REST)."""
    
    # Récupérer l'agent
    architecte = get_agent("ARCHITECTE")
    
    # Préparer le message
    messages = [
        {"role": "system", "content": architecte.system_prompt},
        {"role": "user", "content": """Propose une architecture pour une API REST de gestion de tâches (TODO).

Fonctionnalités :
- CRUD tâches (Create, Read, Update, Delete)
- Persistance JSON
- Validation données
- Endpoints REST

Contraintes :
- FastAPI
- Tests API
- Documentation OpenAPI"""}
    ]
    
    # Appeler l'agent
    response = await architecte.handle(messages, session_id="test_architecte_complexe")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    assert len(response) > 300, f"Réponse trop courte ({len(response)} chars)"
    
    # Vérifier mentions techniques
    response_lower = response.lower()
    assert "api" in response_lower or "rest" in response_lower, "API non mentionnée"
    assert "endpoint" in response_lower or "route" in response_lower, "Endpoints non mentionnés"
    assert "test" in response_lower, "Tests non mentionnés"
    
    # Vérifier architecture multi-fichiers
    assert "fichier" in response_lower or "file" in response_lower, "Structure fichiers non mentionnée"
    
    print(f"\n✅ ARCHITECTE - Projet complexe : {len(response)} chars")
    print(f"Extrait : {response[:300]}...")


@pytest.mark.live
@pytest.mark.asyncio
async def test_architecte_justifications():
    """Test que ARCHITECTE justifie ses choix architecturaux."""
    
    # Récupérer l'agent
    architecte = get_agent("ARCHITECTE")
    
    # Préparer le message
    messages = [
        {"role": "system", "content": architecte.system_prompt},
        {"role": "user", "content": "Propose une architecture pour un système de blog minimaliste avec articles et commentaires."}
    ]
    
    # Appeler l'agent
    response = await architecte.handle(messages, session_id="test_architecte_justifications")
    
    # Vérifications
    assert response is not None, "Réponse vide"
    
    # Vérifier présence de justifications
    response_lower = response.lower()
    justification_keywords = [
        "parce que", "car", "afin de", "pour", "permet",
        "raison", "justification", "choix", "avantage"
    ]
    
    found_justifications = [kw for kw in justification_keywords if kw in response_lower]
    assert len(found_justifications) > 0, f"Aucune justification trouvée. Mots-clés cherchés : {justification_keywords}"
    
    print(f"\n✅ ARCHITECTE - Justifications : {len(found_justifications)} mots-clés trouvés")
    print(f"Mots-clés : {found_justifications}")
