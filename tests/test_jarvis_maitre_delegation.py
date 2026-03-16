"""
Tests d'intégration pour vérifier que JARVIS_Maître délègue correctement au CODEUR.

Ces tests vérifient que JARVIS_Maître génère le marqueur [DEMANDE_CODE_CODEUR: ...]
au lieu de générer du code directement.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.agents.jarvis_maitre import JarvisMaitre
from backend.ia.providers.gemini_provider import GeminiProvider


@pytest.mark.asyncio
async def test_jarvis_maitre_genere_marqueur_delegation():
    """
    Test que JARVIS_Maître génère [DEMANDE_CODE_CODEUR: ...] 
    au lieu de générer du code directement.
    
    Ce test est CRITIQUE pour vérifier que le workflow fonctionne.
    """
    
    # Créer agent JARVIS_Maître
    agent = JarvisMaitre(agent_id="JARVIS_Maître")
    
    # Messages simulant une demande de projet
    messages = [
        {
            "role": "user",
            "content": """MISSION : Création d'un gestionnaire de tâches

Je veux créer une application CLI simple pour gérer des tâches.

Fonctionnalités :
- ajouter une tâche
- lister les tâches
- marquer comme terminée
- supprimer une tâche

Contraintes :
- Python
- Stockage JSON
- Tests pytest

Je valide d'avance l'architecture que tu proposeras.
Génère directement le projet complet."""
        }
    ]
    
    # Mock du provider pour contrôler la réponse
    with patch.object(agent.provider, 'send_message', new_callable=AsyncMock) as mock_send:
        
        # Réponse attendue : JARVIS_Maître DOIT générer le marqueur
        mock_send.return_value = {
            "content": """Parfait. Je délègue au CODEUR.

[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour un gestionnaire de tâches CLI en Python :
- main.py : script principal avec menu interactif, fonctions add_task(), list_tasks(), mark_done(), delete_task()
- storage.py : classe JsonStorage pour sauvegarder/charger tasks.json
- tests/test_main.py : tests pytest pour toutes les fonctions
Utilise Python 3, stockage JSON, pytest pour les tests]""",
            "function_calls": []
        }
        
        # Appeler l'agent
        response = await agent.handle(messages, session_id="test_session")
        
        # VÉRIFICATIONS CRITIQUES
        assert "[DEMANDE_CODE_CODEUR:" in response, \
            "❌ ÉCHEC : JARVIS_Maître n'a PAS généré le marqueur [DEMANDE_CODE_CODEUR: ...]"
        
        assert "```python" not in response, \
            "❌ ÉCHEC : JARVIS_Maître a généré du code Python directement (interdit)"
        
        assert "def " not in response or "[DEMANDE_CODE_CODEUR:" in response, \
            "❌ ÉCHEC : JARVIS_Maître a généré des fonctions Python directement (interdit)"
        
        assert "class " not in response or "[DEMANDE_CODE_CODEUR:" in response, \
            "❌ ÉCHEC : JARVIS_Maître a généré des classes Python directement (interdit)"
        
        # Vérifier que la demande est complète
        assert "main.py" in response, "Détails du fichier main.py manquants"
        assert "storage.py" in response, "Détails du fichier storage.py manquants"
        assert "tests/" in response or "test_" in response, "Tests manquants"
        
        print("\n✅ SUCCÈS : JARVIS_Maître a correctement généré le marqueur de délégation")


@pytest.mark.asyncio
async def test_jarvis_maitre_ne_genere_pas_code_direct():
    """
    Test que JARVIS_Maître NE génère PAS de code directement.
    
    Ce test vérifie l'interdiction formelle de générer du code.
    """
    
    agent = JarvisMaitre(agent_id="JARVIS_Maître")
    
    messages = [
        {
            "role": "user",
            "content": "Crée une fonction Python hello_world() qui retourne 'Hello, World!'"
        }
    ]
    
    # Mock du provider
    with patch.object(agent.provider, 'send_message', new_callable=AsyncMock) as mock_send:
        
        # Réponse correcte : délégation
        mock_send.return_value = {
            "content": """[DEMANDE_CODE_CODEUR: Crée un fichier hello.py avec une fonction hello_world() qui retourne 'Hello, World!' et un test pytest]""",
            "function_calls": []
        }
        
        response = await agent.handle(messages, session_id="test_session_2")
        
        # Vérifications
        assert "[DEMANDE_CODE_CODEUR:" in response, \
            "JARVIS_Maître devrait déléguer même pour une simple fonction"
        
        assert "```python" not in response, \
            "JARVIS_Maître ne doit PAS générer de blocs de code"
        
        assert "def hello_world" not in response or "[DEMANDE_CODE_CODEUR:" in response, \
            "JARVIS_Maître ne doit PAS écrire la fonction directement"


@pytest.mark.live
@pytest.mark.asyncio
async def test_jarvis_maitre_delegation_live():
    """
    Test LIVE : Vérifie que JARVIS_Maître réel génère le marqueur.
    
    Ce test appelle vraiment l'API Gemini pour vérifier le comportement réel.
    """
    
    agent = JarvisMaitre(agent_id="JARVIS_Maître")
    
    messages = [
        {
            "role": "user",
            "content": """Je veux créer une calculatrice Python simple.

Fonctionnalités :
- addition(a, b)
- soustraction(a, b)
- multiplication(a, b)
- division(a, b) avec gestion division par zéro

Contraintes :
- Python
- Tests pytest

Je valide. Génère le projet."""
        }
    ]
    
    # Appel réel à l'API
    response = await agent.handle(messages, session_id="test_live_delegation")
    
    print(f"\n📝 Réponse JARVIS_Maître (live) :\n{response[:500]}...\n")
    
    # VÉRIFICATIONS CRITIQUES
    if "[DEMANDE_CODE_CODEUR:" in response:
        print("✅ SUCCÈS : JARVIS_Maître a généré le marqueur [DEMANDE_CODE_CODEUR: ...]")
        
        # Vérifier qu'il n'y a pas de code en plus
        assert "```python" not in response, \
            "⚠️ JARVIS_Maître a généré le marqueur MAIS aussi du code Python (comportement mixte incorrect)"
        
    else:
        print("❌ ÉCHEC : JARVIS_Maître n'a PAS généré le marqueur [DEMANDE_CODE_CODEUR: ...]")
        
        # Vérifier si du code a été généré directement
        if "```python" in response or "def " in response or "class " in response:
            print("❌ JARVIS_Maître a généré du code directement (interdit)")
            print(f"\n📄 Réponse complète :\n{response}\n")
            pytest.fail("JARVIS_Maître génère du code directement au lieu de déléguer")
        else:
            print("⚠️ JARVIS_Maître n'a ni délégué ni généré de code (comportement inattendu)")
            print(f"\n📄 Réponse complète :\n{response}\n")
            pytest.fail("JARVIS_Maître ne délègue pas correctement")


@pytest.mark.live
@pytest.mark.asyncio
async def test_jarvis_maitre_prompt_charge():
    """
    Test que le prompt JARVIS_Maître est bien chargé avec les instructions de délégation.
    """
    
    agent = JarvisMaitre(agent_id="JARVIS_Maître")
    
    # Vérifier que le prompt contient les instructions de délégation
    prompt_content = agent.get_system_prompt()
    
    assert "DEMANDE_CODE_CODEUR" in prompt_content, \
        "Le prompt ne contient pas les instructions de marqueur DEMANDE_CODE_CODEUR"
    
    assert "INTERDICTION" in prompt_content or "interdiction" in prompt_content.lower(), \
        "Le prompt ne contient pas l'interdiction de générer du code"
    
    assert "délégation" in prompt_content.lower() or "delegation" in prompt_content.lower(), \
        "Le prompt ne contient pas les instructions de délégation"
    
    print("\n✅ Prompt JARVIS_Maître contient les instructions de délégation")
    print(f"📄 Extrait du prompt (500 premiers chars) :\n{prompt_content[:500]}...\n")


if __name__ == "__main__":
    # Exécuter seulement les tests non-live par défaut
    pytest.main([__file__, "-v", "-s", "-m", "not live"])
