"""
Tests pour le workflow unique JARVIS 2.0

Teste que toutes les missions suivent le même workflow :
ARCHITECTE → Validation USER → CODEUR → TESTEUR → VALIDATEUR
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.services.orchestration import SimpleOrchestrator


@pytest.mark.asyncio
async def test_workflow_unique_demarre_avec_marqueur():
    """Test que le workflow unique démarre avec [DEMANDE_CODE_CODEUR:]"""
    orchestrator = SimpleOrchestrator()
    
    response = """[DEMANDE_CODE_CODEUR: Crée une app de gestion de tâches :
- main.py : classe TaskManager avec add_task(), list_tasks(), mark_done()
- storage.py : classe JsonStorage pour sauvegarder dans tasks.json
- tests/test_main.py : tests pytest
Utilise Python 3, stockage JSON, pytest]"""
    
    with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock:
        mock.return_value = {"success": True, "mission_id": "test_123", "mode": "COMPLETE"}
        
        final_response, delegation_results = await orchestrator.process_response(
            response=response,
            conversation_history=[],
            session_id="test",
            project_path="C:\\TEST\\app"
        )
        
        # Vérifier que start_mission a été appelé
        assert mock.called, "start_mission devrait être appelé"
        
        # Vérifier qu'on n'envoie plus workflow_type
        call_kwargs = mock.call_args.kwargs
        assert "workflow_type" not in call_kwargs, "workflow_type ne devrait plus exister"
        
        # Vérifier que la demande a été extraite
        assert "user_request" in call_kwargs
        assert "TaskManager" in call_kwargs["user_request"]


@pytest.mark.asyncio
async def test_workflow_unique_sans_marqueur():
    """Test que le workflow ne démarre pas sans marqueur"""
    orchestrator = SimpleOrchestrator()
    
    response = """Voici ce que je propose :
    
Architecture :
- main.py : classe TaskManager
- storage.py : classe JsonStorage

Validez-vous cette architecture ?"""
    
    with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock:
        final_response, delegation_results = await orchestrator.process_response(
            response=response,
            conversation_history=[],
            session_id="test",
            project_path="C:\\TEST\\app"
        )
        
        # Vérifier que start_mission n'a PAS été appelé
        assert not mock.called, "start_mission ne devrait PAS être appelé sans marqueur"
        assert delegation_results == [], "delegation_results devrait être vide"


@pytest.mark.asyncio
async def test_workflow_unique_genere_code_interdit():
    """Test détection quand JARVIS_Maître génère du code directement (ERREUR)"""
    orchestrator = SimpleOrchestrator()
    
    # Réponse INCORRECTE : JARVIS_Maître génère du code directement
    response = """Parfait. Je génère le projet complet.

Fichier : main.py
```python
def hello():
    return "Hello, World!"
```

Le projet est créé."""
    
    with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock:
        final_response, delegation_results = await orchestrator.process_response(
            response=response,
            conversation_history=[],
            session_id="test",
            project_path="C:\\TEST\\app"
        )
        
        # Vérifier que workflow NE se déclenche PAS
        assert not mock.called, "start_mission ne devrait PAS être appelé si code généré directement"
        assert "```python" in final_response, "Réponse devrait contenir le code (erreur)"
        assert delegation_results == [], "delegation_results devrait être vide"


@pytest.mark.asyncio
async def test_start_mission_toujours_workflow_complet():
    """Test que start_mission utilise toujours execute_complete_mode"""
    orchestrator = SimpleOrchestrator()
    
    with patch.object(orchestrator, 'execute_complete_mode', new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = {
            "success": True,
            "mode": "COMPLETE",
            "architecture_doc": "Architecture test",
            "validation_result": "AWAITING_USER_VALIDATION",
            "requires_user_validation": True,
            "mission_id": "mission_test"
        }
        
        result = await orchestrator.start_mission(
            user_request="Crée une app de gestion de tâches",
            project_name="test_app",
            project_path="C:\\TEST\\test_app"
        )
        
        # Vérifier que execute_complete_mode a été appelé
        assert mock_complete.called, "execute_complete_mode devrait toujours être appelé"
        
        # Vérifier le résultat
        assert result["success"] == True
        assert result["mode"] == "COMPLETE"


@pytest.mark.asyncio
async def test_process_response_extraction_demande():
    """Test extraction correcte de la demande depuis le marqueur"""
    orchestrator = SimpleOrchestrator()
    
    response = """[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour une API REST :
- src/main.py : application FastAPI avec routes GET/POST/DELETE
- src/models.py : modèles Pydantic
- tests/test_api.py : tests pytest
Utilise FastAPI, pytest]"""
    
    with patch.object(orchestrator, 'start_mission', new_callable=AsyncMock) as mock:
        mock.return_value = {"success": True, "mission_id": "test"}
        
        await orchestrator.process_response(
            response=response,
            conversation_history=[],
            session_id="test",
            project_path="C:\\TEST\\api"
        )
        
        # Vérifier extraction complète
        call_kwargs = mock.call_args.kwargs
        user_request = call_kwargs["user_request"]
        
        assert "src/main.py" in user_request
        assert "FastAPI" in user_request
        assert "pytest" in user_request


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
