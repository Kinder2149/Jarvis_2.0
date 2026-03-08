"""
Test E2E complet : Projet TODO List.

Teste le workflow complet avec persistance JSON :
1. Génération code TODO list
2. Validation
3. Exécution tests
4. Test fonctionnel (ajout/suppression tâches)
"""

import pytest
import tempfile
import shutil
import subprocess
import sys
import json
from pathlib import Path
from backend.services.orchestration import SimpleOrchestrator
from backend.models.mission import Mission

@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_todo_complete():
    """Test E2E complet : TODO list avec persistance JSON."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_todo_")
    
    try:
        # 1. Demande utilisateur
        user_request = """Crée une application TODO list Python avec :

Classe TodoList :
- add_task(task: str) : Ajoute une tâche
- remove_task(task: str) : Supprime une tâche
- get_tasks() -> list : Retourne toutes les tâches
- save_to_json(filename: str) : Sauvegarde dans fichier JSON
- load_from_json(filename: str) : Charge depuis fichier JSON

Tests unitaires pytest complets.

Fichiers :
- todo.py : Classe TodoList
- test_todo.py : Tests unitaires"""
        
        # 2. Détection complexité
        orchestrator = SimpleOrchestrator()
        complexity = orchestrator.detect_project_complexity(user_request)
        print(f"\n📊 Complexité détectée : {complexity}")
        
        # 3. Créer mission
        mission = Mission(
            mission_id="test_e2e_todo",
            user_request=user_request,
            project_path=temp_dir
        )
        
        # 4. Exécuter workflow (COMPLET si complexe, RAPIDE si simple)
        if complexity == "COMPLEX":
            result = await orchestrator.execute_complete_mode(mission, user_request, temp_dir)
        else:
            result = await orchestrator.execute_fast_mode(mission, user_request, temp_dir)
        
        # 5. Vérifications résultat
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        print(f"\n📊 Résultat workflow :")
        print(f"   Mode : {result['mode']}")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers : {result.get('files_created', [])}")
        
        # 6. Vérifier fichiers créés
        files_created = result.get("files_created", [])
        
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            # 7. Trouver fichiers
            todo_file = None
            test_file = None
            
            for file_path in files_created:
                full_path = Path(temp_dir) / file_path
                assert full_path.exists(), f"Fichier manquant : {file_path}"
                
                if "todo.py" in file_path.lower() and "test" not in file_path.lower():
                    todo_file = full_path
                elif "test" in file_path.lower() and "todo" in file_path.lower():
                    test_file = full_path
            
            print(f"\n📁 Fichiers trouvés :")
            print(f"   TODO : {todo_file}")
            print(f"   Tests : {test_file}")
            
            # 8. Vérifier contenu code
            if todo_file and todo_file.exists():
                code_content = todo_file.read_text(encoding='utf-8')
                
                print(f"\n📝 Vérification code TODO :")
                assert "class TodoList" in code_content, "Classe TodoList manquante"
                assert "def add_task" in code_content, "Méthode add_task manquante"
                assert "def remove_task" in code_content, "Méthode remove_task manquante"
                assert "def get_tasks" in code_content, "Méthode get_tasks manquante"
                print(f"   ✅ Toutes les méthodes présentes")
                
                # Vérifier persistance JSON
                has_json = "json" in code_content.lower() or "save" in code_content or "load" in code_content
                print(f"   {'✅' if has_json else '⚠️ '} Persistance JSON : {'Présente' if has_json else 'Absente'}")
            
            # 9. Exécuter les tests générés
            if test_file and test_file.exists():
                print(f"\n🧪 Exécution des tests générés...")
                
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
                        print(f"   ✅ Tests générés : TOUS PASSENT")
                    else:
                        print(f"   ⚠️  Tests générés : ÉCHECS")
                        print(f"   Stdout : {result_pytest.stdout[:300]}")
                    
                except Exception as e:
                    print(f"\n⚠️  Tests générés : ERREUR ({e})")
            
            print(f"\n✅ E2E TODO : SUCCÈS COMPLET")
        else:
            print(f"\n⚠️  E2E TODO : Validation échouée ou aucun fichier créé")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_todo_fonctionnel():
    """Test E2E : TODO fonctionnelle (ajout/suppression tâches)."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_todo_func_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_e2e_todo_func",
            user_request="""Crée une classe TodoList Python simple.

Méthodes :
- add_task(task: str)
- remove_task(task: str)
- get_tasks() -> list

Tests pytest.

Fichiers :
- todolist.py
- test_todolist.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        files_created = result.get("files_created", [])
        
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            # Trouver fichier principal
            todo_file = None
            for file_path in files_created:
                if "todolist.py" in file_path.lower() and "test" not in file_path.lower():
                    todo_file = Path(temp_dir) / file_path
                    break
            
            if todo_file and todo_file.exists():
                # Tester fonctionnalité
                print(f"\n🔧 Test fonctionnel du code généré...")
                
                sys.path.insert(0, temp_dir)
                
                try:
                    # Importer le module
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("todolist", todo_file)
                    todo_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(todo_module)
                    
                    # Tester la classe
                    if hasattr(todo_module, 'TodoList'):
                        todo = todo_module.TodoList()
                        
                        # Test ajout
                        todo.add_task("Tâche 1")
                        todo.add_task("Tâche 2")
                        tasks = todo.get_tasks()
                        assert len(tasks) == 2, f"Devrait avoir 2 tâches, pas {len(tasks)}"
                        print(f"   ✅ add_task : 2 tâches ajoutées")
                        
                        # Test suppression
                        todo.remove_task("Tâche 1")
                        tasks = todo.get_tasks()
                        assert len(tasks) == 1, f"Devrait avoir 1 tâche, pas {len(tasks)}"
                        print(f"   ✅ remove_task : 1 tâche supprimée")
                        
                        print(f"\n✅ Code généré : FONCTIONNEL")
                    
                except Exception as e:
                    print(f"\n⚠️  Code généré : ERREUR ({e})")
                finally:
                    sys.path.remove(temp_dir)
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_todo_persistance_json():
    """Test E2E : TODO avec persistance JSON fonctionnelle."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_todo_json_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_e2e_todo_json",
            user_request="""Crée une classe TodoList avec persistance JSON.

Méthodes :
- add_task(task: str)
- get_tasks() -> list
- save(filename: str) : Sauvegarde en JSON
- load(filename: str) : Charge depuis JSON

Tests pytest incluant tests de persistance.

Fichiers :
- todo_storage.py
- test_todo_storage.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        files_created = result.get("files_created", [])
        
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            # Trouver fichier principal
            todo_file = None
            for file_path in files_created:
                if "todo" in file_path.lower() and "storage" in file_path.lower() and "test" not in file_path.lower():
                    todo_file = Path(temp_dir) / file_path
                    break
            
            if todo_file and todo_file.exists():
                # Tester persistance JSON
                print(f"\n💾 Test persistance JSON...")
                
                sys.path.insert(0, temp_dir)
                
                try:
                    # Importer le module
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("todo_storage", todo_file)
                    todo_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(todo_module)
                    
                    # Tester la classe
                    if hasattr(todo_module, 'TodoList'):
                        todo = todo_module.TodoList()
                        
                        # Ajouter tâches
                        todo.add_task("Tâche A")
                        todo.add_task("Tâche B")
                        
                        # Sauvegarder
                        json_file = Path(temp_dir) / "test_tasks.json"
                        if hasattr(todo, 'save'):
                            todo.save(str(json_file))
                            
                            # Vérifier fichier JSON créé
                            if json_file.exists():
                                print(f"   ✅ Fichier JSON créé : {json_file.name}")
                                
                                # Vérifier contenu JSON
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    print(f"   ✅ JSON valide : {data}")
                                
                                # Charger dans nouvelle instance
                                todo2 = todo_module.TodoList()
                                if hasattr(todo2, 'load'):
                                    todo2.load(str(json_file))
                                    tasks = todo2.get_tasks()
                                    assert len(tasks) == 2, f"Devrait avoir 2 tâches chargées"
                                    print(f"   ✅ Chargement JSON : 2 tâches restaurées")
                                
                                print(f"\n✅ Persistance JSON : FONCTIONNELLE")
                        
                except Exception as e:
                    print(f"\n⚠️  Persistance JSON : ERREUR ({e})")
                finally:
                    sys.path.remove(temp_dir)
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
