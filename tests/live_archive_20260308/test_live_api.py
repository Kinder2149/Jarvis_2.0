"""
Test live : Projet API REST
Nécessite API Gemini active
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from backend.services.orchestration import SimpleOrchestrator


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_api_rest():
    """
    Test live : Génération d'une API REST simple avec FastAPI
    
    Ce test appelle réellement les agents Gemini pour générer une API.
    Il vérifie que le workflow COMPLET fonctionne avec validation architecture.
    """
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir) / "todo_api"
    project_path.mkdir()
    
    try:
        orchestrator = SimpleOrchestrator()
        
        # Exécuter mission (devrait déclencher mode COMPLET)
        result = await orchestrator.start_mission(
            user_request=(
                "Crée une API REST simple avec FastAPI pour gérer des tâches (TODO). "
                "Endpoints : GET /tasks (liste), POST /tasks (créer), "
                "GET /tasks/{id} (détail), PUT /tasks/{id} (modifier), "
                "DELETE /tasks/{id} (supprimer). "
                "Utilise un stockage en mémoire (liste Python)."
            ),
            project_name="todo_api",
            project_path=str(project_path)
        )
        
        # Vérifications de base
        assert result["success"] is True or result.get("requires_user_validation") is True, \
            f"Mission échouée : {result.get('error')}"
        
        # Si validation architecture requise
        if result.get("requires_user_validation"):
            assert result["mode"] == "COMPLETE", "Devrait utiliser mode COMPLET"
            assert "architecture" in result, "Architecture manquante"
            
            print(f"\n⚠️ Test API REST : Validation architecture requise")
            print(f"   Mode : {result['mode']}")
            print(f"   Architecture proposée : Oui")
            
            # Dans un test réel, on validerait l'architecture et continuerait
            # Pour ce test, on vérifie juste que le workflow s'est arrêté correctement
            
        else:
            # Si le workflow a continué sans validation (mode FAST détecté)
            assert result["mode"] in ["FAST", "COMPLETE"], f"Mode inattendu : {result['mode']}"
            
            files_created = result.get("files_created", [])
            assert len(files_created) > 0, "Aucun fichier créé"
            
            # Vérifier fichiers Python
            python_files = [f for f in files_created if f.endswith('.py')]
            assert len(python_files) > 0, "Aucun fichier Python créé"
            
            # Vérifier présence de fichiers API
            api_file = None
            for f in python_files:
                if "api" in f.lower() or "main" in f.lower():
                    api_file = project_path / f
                    break
            
            if api_file and api_file.exists():
                content = api_file.read_text(encoding='utf-8')
                
                # Vérifier imports FastAPI
                assert "fastapi" in content.lower() or "from fastapi" in content.lower(), \
                    "FastAPI non importé"
                
                # Vérifier présence de routes
                routes_found = sum([
                    "get" in content.lower() or "@app.get" in content.lower(),
                    "post" in content.lower() or "@app.post" in content.lower(),
                ])
                assert routes_found >= 1, "Aucune route trouvée"
            
            print(f"\n✅ Test live API REST réussi !")
            print(f"   Mode : {result['mode']}")
            print(f"   Fichiers créés : {len(files_created)}")
            print(f"   Fichiers Python : {len(python_files)}")
        
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_api_complexity_detection():
    """
    Test live : Vérification détection de complexité
    """
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir) / "api_complex"
    project_path.mkdir()
    
    try:
        orchestrator = SimpleOrchestrator()
        
        # Requête explicitement complexe
        result = await orchestrator.start_mission(
            user_request=(
                "Crée une API REST complète avec authentification JWT, "
                "gestion utilisateurs, permissions, base de données SQLite, "
                "migrations, tests complets, documentation OpenAPI."
            ),
            project_name="api_complex",
            project_path=str(project_path)
        )
        
        # Devrait déclencher mode COMPLET
        assert result.get("mode") == "COMPLETE" or result.get("requires_user_validation") is True, \
            "Projet complexe devrait déclencher mode COMPLET"
        
        if result.get("requires_user_validation"):
            assert "architecture" in result, "Architecture devrait être proposée"
        
        print(f"\n✅ Test détection complexité réussi !")
        print(f"   Mode détecté : {result.get('mode', 'VALIDATION_REQUISE')}")
        
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_api_with_tests():
    """
    Test live : Vérification génération de tests pour API
    """
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir) / "api_with_tests"
    project_path.mkdir()
    
    try:
        orchestrator = SimpleOrchestrator()
        
        result = await orchestrator.start_mission(
            user_request=(
                "Crée une API FastAPI simple avec un endpoint GET /health "
                "qui retourne {'status': 'ok'}. Ajoute des tests pytest."
            ),
            project_name="api_health",
            project_path=str(project_path)
        )
        
        # Si validation requise, skip ce test
        if result.get("requires_user_validation"):
            pytest.skip("Validation architecture requise")
        
        assert result["success"] is True
        
        files_created = result.get("files_created", [])
        
        # Vérifier présence de tests
        test_files = [f for f in files_created if "test" in f.lower()]
        assert len(test_files) > 0, "Aucun fichier de test créé"
        
        # Vérifier contenu des tests
        for test_file in test_files:
            full_path = project_path / test_file
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                
                # Vérifier imports pytest
                assert "pytest" in content.lower() or "import pytest" in content.lower() or \
                       "def test_" in content.lower(), \
                    f"Fichier {test_file} ne semble pas être un test pytest valide"
        
        print(f"\n✅ Test génération tests API réussi !")
        print(f"   Fichiers tests : {test_files}")
        
    finally:
        shutil.rmtree(temp_dir)
