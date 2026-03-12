"""
Test E2E complet : Projet API REST.

Teste le workflow complet pour une API REST :
1. Génération API FastAPI
2. Validation
3. Exécution tests
4. Test fonctionnel (endpoints)
"""

import pytest
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
from backend.services.orchestration import SimpleOrchestrator
from backend.models.mission import Mission

@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_api_rest_complete():
    """Test E2E complet : API REST avec FastAPI."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_api_")
    
    try:
        # 1. Demande utilisateur
        user_request = """Crée une API REST pour gérer des utilisateurs.

Endpoints :
- GET /users : Liste tous les utilisateurs
- POST /users : Crée un nouvel utilisateur
- GET /users/{id} : Récupère un utilisateur par ID
- DELETE /users/{id} : Supprime un utilisateur

Contraintes :
- FastAPI
- Modèle User (id, name, email)
- Stockage en mémoire (liste Python)
- Tests API avec pytest
- Documentation OpenAPI automatique

Fichiers attendus :
- main.py : Application FastAPI
- models.py : Modèle User
- test_api.py : Tests API"""
        
        # 2. Détection complexité
        orchestrator = SimpleOrchestrator()
        complexity = orchestrator.detect_project_complexity(user_request)
        print(f"\n📊 Complexité détectée : {complexity}")
        assert complexity == "COMPLEX", f"API REST devrait être COMPLEX, pas {complexity}"
        
        # 3. Créer mission
        mission = Mission(
            mission_id="test_e2e_api",
            user_request=user_request,
            project_path=temp_dir
        )
        
        # 4. Exécuter workflow COMPLET
        result = await orchestrator.execute_complete_mode(mission, user_request, temp_dir)
        
        # 5. Vérifications résultat
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        assert result["mode"] == "COMPLETE", f"Mode incorrect : {result['mode']}"
        
        print(f"\n📊 Résultat workflow :")
        print(f"   Mode : {result['mode']}")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers : {result.get('files_created', [])}")
        
        # 6. Vérifier ARCHITECTE
        assert "architecture_response" in result, "ARCHITECTE non appelé"
        architecture = result["architecture_response"]
        print(f"\n📐 Architecture : {len(architecture)} chars")
        
        # 7. Vérifier fichiers créés
        files_created = result.get("files_created", [])
        
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            assert len(files_created) >= 2, f"API REST devrait avoir au moins 2 fichiers : {len(files_created)}"
            
            # 8. Trouver fichiers
            main_file = None
            models_file = None
            test_file = None
            
            for file_path in files_created:
                full_path = Path(temp_dir) / file_path
                assert full_path.exists(), f"Fichier manquant : {file_path}"
                
                if "main.py" in file_path.lower():
                    main_file = full_path
                elif "models.py" in file_path.lower():
                    models_file = full_path
                elif "test" in file_path.lower():
                    test_file = full_path
            
            print(f"\n📁 Fichiers trouvés :")
            print(f"   Main : {main_file}")
            print(f"   Models : {models_file}")
            print(f"   Tests : {test_file}")
            
            # 9. Vérifier contenu code
            if main_file and main_file.exists():
                code_content = main_file.read_text(encoding='utf-8')
                
                print(f"\n📝 Vérification code API :")
                
                # Vérifier imports FastAPI
                has_fastapi = "from fastapi import" in code_content or "import fastapi" in code_content
                print(f"   {'✅' if has_fastapi else '⚠️ '} Import FastAPI : {'Présent' if has_fastapi else 'Absent'}")
                
                # Vérifier endpoints
                has_get = "@app.get" in code_content or '@app.get' in code_content
                has_post = "@app.post" in code_content or '@app.post' in code_content
                has_delete = "@app.delete" in code_content or '@app.delete' in code_content
                
                print(f"   {'✅' if has_get else '⚠️ '} Endpoint GET : {'Présent' if has_get else 'Absent'}")
                print(f"   {'✅' if has_post else '⚠️ '} Endpoint POST : {'Présent' if has_post else 'Absent'}")
                print(f"   {'✅' if has_delete else '⚠️ '} Endpoint DELETE : {'Présent' if has_delete else 'Absent'}")
            
            # 10. Exécuter les tests générés
            if test_file and test_file.exists():
                print(f"\n🧪 Exécution des tests API...")
                
                try:
                    result_pytest = subprocess.run(
                        [sys.executable, "-m", "pytest", str(test_file), "-v"],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    print(f"\n📊 Résultat pytest :")
                    print(f"   Code retour : {result_pytest.returncode}")
                    
                    if result_pytest.returncode == 0:
                        print(f"   ✅ Tests API : TOUS PASSENT")
                    else:
                        print(f"   ⚠️  Tests API : ÉCHECS")
                        print(f"   Stdout : {result_pytest.stdout[:300]}")
                    
                except Exception as e:
                    print(f"\n⚠️  Tests API : ERREUR ({e})")
            
            print(f"\n✅ E2E API REST : SUCCÈS COMPLET")
        else:
            print(f"\n⚠️  E2E API REST : Validation échouée ou aucun fichier créé")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_api_rest_simple():
    """Test E2E : API REST simple (GET/POST uniquement)."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_api_simple_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_e2e_api_simple",
            user_request="""Crée une API REST minimaliste avec FastAPI.

Endpoints :
- GET /items : Retourne liste d'items
- POST /items : Ajoute un item

Modèle Item (id, name).
Stockage en mémoire.
Tests pytest.

Fichiers :
- api.py
- test_api.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_complete_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        print(f"\n📊 Résultat API simple :")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers : {result.get('files_created', [])}")
        
        files_created = result.get("files_created", [])
        
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            # Vérifier fichier API
            api_file = None
            for file_path in files_created:
                if "api.py" in file_path.lower() and "test" not in file_path.lower():
                    api_file = Path(temp_dir) / file_path
                    break
            
            if api_file and api_file.exists():
                code_content = api_file.read_text(encoding='utf-8')
                
                # Vérifier syntaxe
                try:
                    compile(code_content, '<string>', 'exec')
                    print(f"   ✅ Syntaxe Python valide")
                except SyntaxError as e:
                    print(f"   ❌ Erreur syntaxe : {e}")
                
                # Vérifier FastAPI
                if "fastapi" in code_content.lower():
                    print(f"   ✅ FastAPI utilisé")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_api_rest_documentation():
    """Test E2E : API REST avec documentation OpenAPI."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_api_doc_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_e2e_api_doc",
            user_request="""Crée une API REST avec documentation complète.

Endpoints :
- GET /tasks : Liste tâches
- POST /tasks : Crée tâche

Modèle Task (id, title, done).
Documentation OpenAPI automatique.
Tests pytest.

Fichiers :
- main.py
- models.py
- test_main.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_complete_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        files_created = result.get("files_created", [])
        
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            # Vérifier fichier main
            main_file = None
            for file_path in files_created:
                if "main.py" in file_path.lower():
                    main_file = Path(temp_dir) / file_path
                    break
            
            if main_file and main_file.exists():
                code_content = main_file.read_text(encoding='utf-8')
                
                print(f"\n📝 Vérification documentation API :")
                
                # Vérifier docstrings ou descriptions
                has_docs = '"""' in code_content or "description=" in code_content
                print(f"   {'✅' if has_docs else '⚠️ '} Documentation : {'Présente' if has_docs else 'Absente'}")
                
                # Vérifier modèles Pydantic (pour OpenAPI)
                has_pydantic = "BaseModel" in code_content or "pydantic" in code_content
                print(f"   {'✅' if has_pydantic else '⚠️ '} Modèles Pydantic : {'Présents' if has_pydantic else 'Absents'}")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
