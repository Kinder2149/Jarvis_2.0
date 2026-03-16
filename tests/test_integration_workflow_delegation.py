"""
Tests d'intégration end-to-end pour le workflow complet de délégation.

Teste le flux complet :
1. JARVIS_Maître reçoit demande utilisateur
2. JARVIS_Maître génère [DEMANDE_CODE_CODEUR: ...]
3. process_response détecte le marqueur
4. start_mission est appelé
5. Workflow 5 agents démarre
6. Fichiers créés dans le projet
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.orchestration import SimpleOrchestrator
from backend.agents.jarvis_maitre import JarvisMaitre


@pytest.mark.asyncio
async def test_integration_delegation_complete_mock():
    """
    Test d'intégration complet avec mock de JARVIS_Maître.
    
    Vérifie que si JARVIS_Maître génère le marqueur,
    alors le workflow se déclenche correctement.
    """
    
    orchestrator = SimpleOrchestrator()
    
    # Simuler réponse de JARVIS_Maître avec marqueur
    jarvis_response = """Parfait. Je délègue au CODEUR.

[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour une calculatrice Python :
- calculator.py : classe Calculator avec méthodes add, subtract, multiply, divide
- test_calculator.py : tests pytest pour toutes les méthodes
Utilise Python 3, pytest]"""
    
    conversation_history = [
        {"role": "user", "content": "Crée une calculatrice Python"}
    ]
    
    session_id = "test_integration_123"
    project_path = "C:\\TEST\\test_calculator"
    
    # Mock start_mission pour vérifier qu'il est appelé
    with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock_start:
        mock_start.return_value = {
            "success": True,
            "mission_id": "mission_integration_123",
            "status": "IN_PROGRESS"
        }
        
        # Appeler process_response (comme le ferait l'API)
        final_response, delegation_results = await orchestrator.process_response(
            response=jarvis_response,
            conversation_history=conversation_history,
            session_id=session_id,
            project_path=project_path,
            function_executor=None,
            session_state=None
        )
        
        # VÉRIFICATIONS
        assert mock_start.called, \
            "❌ ÉCHEC : start_mission n'a pas été appelé malgré le marqueur [DEMANDE_CODE_CODEUR: ...]"
        
        assert mock_start.call_count == 1, \
            f"start_mission appelé {mock_start.call_count} fois au lieu de 1"
        
        # Vérifier les arguments
        call_kwargs = mock_start.call_args.kwargs
        user_request = call_kwargs["user_request"]
        project_path_arg = call_kwargs["project_path"]
        
        assert "calculator.py" in user_request, "Détails du fichier calculator.py manquants"
        assert "test_calculator.py" in user_request, "Détails du fichier test_calculator.py manquants"
        assert project_path_arg == project_path, f"project_path incorrect : {project_path_arg}"
        
        print("\n✅ SUCCÈS : Workflow déclenché correctement après détection du marqueur")


@pytest.mark.asyncio
async def test_integration_pas_de_delegation_sans_marqueur():
    """
    Test que le workflow NE se déclenche PAS si JARVIS_Maître ne génère pas le marqueur.
    """
    
    orchestrator = SimpleOrchestrator()
    
    # Simuler réponse de JARVIS_Maître SANS marqueur (génération directe - ERREUR)
    jarvis_response = """Parfait. Je génère le projet complet.

Fichier : calculator.py
```python
class Calculator:
    def add(self, a, b):
        return a + b
```

Fichier : test_calculator.py
```python
def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5
```"""
    
    conversation_history = [
        {"role": "user", "content": "Crée une calculatrice Python"}
    ]
    
    session_id = "test_integration_no_marker"
    project_path = "C:\\TEST\\test_calculator_2"
    
    # Mock start_mission
    with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock_start:
        
        # Appeler process_response
        final_response, delegation_results = await orchestrator.process_response(
            response=jarvis_response,
            conversation_history=conversation_history,
            session_id=session_id,
            project_path=project_path,
            function_executor=None,
            session_state=None
        )
        
        # VÉRIFICATIONS
        assert not mock_start.called, \
            "❌ ÉCHEC : start_mission appelé alors que JARVIS_Maître a généré du code directement"
        
        assert delegation_results == [], "delegation_results devrait être vide"
        
        print("\n✅ SUCCÈS : Workflow non déclenché (comportement attendu sans marqueur)")
        print("⚠️ MAIS : JARVIS_Maître ne devrait PAS générer du code directement")


@pytest.mark.live
@pytest.mark.asyncio
async def test_integration_live_jarvis_maitre_vers_workflow():
    """
    Test LIVE end-to-end complet :
    1. Appel réel à JARVIS_Maître
    2. Vérification de la réponse
    3. Appel à process_response
    4. Vérification du déclenchement du workflow
    
    Ce test utilise vraiment l'API Gemini.
    """
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_integration_live_")
    
    try:
        # Étape 1 : Appeler JARVIS_Maître
        agent = JarvisMaitre()
        
        messages = [
            {
                "role": "user",
                "content": """Crée une fonction Python simple hello_world() qui retourne 'Hello, World!' avec un test pytest.

Je valide. Génère le projet."""
            }
        ]
        
        print("\n📞 Appel à JARVIS_Maître (API Gemini)...")
        jarvis_response = await agent.handle(messages, session_id="test_live_integration")
        
        print(f"\n📝 Réponse JARVIS_Maître :\n{jarvis_response[:500]}...\n")
        
        # Étape 2 : Vérifier la réponse
        has_marker = "[DEMANDE_CODE_CODEUR:" in jarvis_response
        has_code = "```python" in jarvis_response or "def hello_world" in jarvis_response
        
        if has_marker:
            print("✅ JARVIS_Maître a généré le marqueur [DEMANDE_CODE_CODEUR: ...]")
        else:
            print("❌ JARVIS_Maître n'a PAS généré le marqueur")
        
        if has_code and not has_marker:
            print("❌ JARVIS_Maître a généré du code directement (interdit)")
        
        # Étape 3 : Appeler process_response
        orchestrator = SimpleOrchestrator()
        
        conversation_history = messages
        session_id = "test_live_integration"
        project_path = temp_dir
        
        # Mock start_mission pour éviter l'exécution réelle du workflow
        with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock_start:
            mock_start.return_value = {
                "success": True,
                "mission_id": "mission_live_test",
                "status": "IN_PROGRESS"
            }
            
            final_response, delegation_results = await orchestrator.process_response(
                response=jarvis_response,
                conversation_history=conversation_history,
                session_id=session_id,
                project_path=project_path,
                function_executor=None,
                session_state=None
            )
            
            # Étape 4 : Vérifications finales
            if has_marker:
                assert mock_start.called, \
                    "❌ ÉCHEC : Marqueur détecté mais start_mission non appelé"
                print("✅ SUCCÈS : Workflow déclenché correctement")
            else:
                assert not mock_start.called, \
                    "start_mission ne devrait pas être appelé sans marqueur"
                print("⚠️ Workflow non déclenché (JARVIS_Maître n'a pas délégué)")
                
                # Si JARVIS_Maître ne délègue pas, c'est un échec du test
                pytest.fail(
                    "JARVIS_Maître n'a pas généré le marqueur [DEMANDE_CODE_CODEUR: ...]. "
                    "Le prompt JARVIS_Maître doit être corrigé ou le modèle ne respecte pas les instructions."
                )
    
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_integration_extraction_demande_correcte():
    """
    Test que la demande extraite du marqueur est correcte et complète.
    """
    
    orchestrator = SimpleOrchestrator()
    
    # Réponse avec marqueur détaillé
    jarvis_response = """Parfait. Je délègue au CODEUR.

[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour une API REST FastAPI :
- src/main.py : application FastAPI avec routes GET /items, POST /items, DELETE /items/{id}
- src/models.py : classe Item avec Pydantic (id: int, name: str, description: str)
- src/database.py : liste en mémoire pour stocker les items
- tests/test_api.py : tests pytest avec TestClient pour toutes les routes
- requirements.txt : fastapi, uvicorn, pytest
Utilise FastAPI, Pydantic, pytest. Structure src/ pour le code, tests/ pour les tests]"""
    
    conversation_history = []
    session_id = "test_extraction"
    project_path = "C:\\TEST\\api_rest"
    
    # Mock start_mission
    with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock_start:
        mock_start.return_value = {"success": True}
        
        await orchestrator.process_response(
            response=jarvis_response,
            conversation_history=conversation_history,
            session_id=session_id,
            project_path=project_path,
            function_executor=None,
            session_state=None
        )
        
        # Vérifier extraction
        call_kwargs = mock_start.call_args.kwargs
        user_request = call_kwargs["user_request"]
        
        # Vérifier que TOUS les détails sont présents
        assert "src/main.py" in user_request, "Fichier main.py manquant"
        assert "GET /items" in user_request, "Route GET manquante"
        assert "POST /items" in user_request, "Route POST manquante"
        assert "DELETE /items" in user_request, "Route DELETE manquante"
        assert "src/models.py" in user_request, "Fichier models.py manquant"
        assert "Pydantic" in user_request, "Framework Pydantic manquant"
        assert "tests/test_api.py" in user_request, "Fichier test manquant"
        assert "requirements.txt" in user_request, "Fichier requirements.txt manquant"
        assert "FastAPI" in user_request, "Framework FastAPI manquant"
        
        print("\n✅ SUCCÈS : Demande extraite complète et correcte")
        print(f"\n📄 Demande extraite ({len(user_request)} chars) :\n{user_request[:300]}...\n")


if __name__ == "__main__":
    # Exécuter seulement les tests non-live par défaut
    pytest.main([__file__, "-v", "-s", "-m", "not live"])
