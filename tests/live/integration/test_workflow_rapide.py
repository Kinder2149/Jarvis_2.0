"""
Tests d'intégration pour le workflow RAPIDE.

Teste l'enchaînement complet :
CODEUR → TESTEUR → VALIDATEUR → Écriture fichiers

Pour des projets SIMPLES (≤3 fichiers).
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from backend.services.orchestration import SimpleOrchestrator
from backend.models.mission import Mission

@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_rapide_calculatrice():
    """Test workflow RAPIDE complet sur projet calculatrice."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_rapide_calc_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_rapide_calc",
            user_request="""Crée une calculatrice Python simple avec :
- Fonction addition(a, b)
- Fonction soustraction(a, b)
- Tests unitaires pytest

Fichiers attendus :
- calculatrice.py
- test_calculatrice.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications résultat
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        assert result["mode"] == "FAST", f"Mode incorrect : {result['mode']}"
        
        # Vérifier validation
        assert result["validation_result"] in ["VALID", "INVALID"], f"Validation invalide : {result['validation_result']}"
        
        # Vérifier fichiers créés
        files_created = result.get("files_created", [])
        print(f"\n📁 Fichiers créés : {files_created}")
        
        # Note : On ne force pas la validation VALID car c'est justement ce qu'on veut tester
        # On vérifie juste que des fichiers ont été créés
        if result["validation_result"] == "VALID":
            assert len(files_created) > 0, "Aucun fichier créé malgré validation VALID"
            
            # Vérifier existence des fichiers
            for file_path in files_created:
                full_path = Path(temp_dir) / file_path
                assert full_path.exists(), f"Fichier créé mais introuvable : {file_path}"
                
                # Vérifier que le fichier n'est pas vide
                assert full_path.stat().st_size > 0, f"Fichier vide : {file_path}"
            
            print(f"✅ Workflow RAPIDE - Calculatrice : {len(files_created)} fichier(s) créé(s)")
        else:
            print(f"⚠️  Workflow RAPIDE - Calculatrice : INVALID (validation stricte)")
            print(f"   Fichiers créés quand même : {len(files_created)}")
            
            # Afficher raison du rejet si disponible
            if "validation_response" in result:
                print(f"   Raison : {result['validation_response'][:200]}...")
        
        # Vérifier que le workflow s'est terminé (pas de timeout)
        assert "error" not in result or result["error"] is None, f"Erreur : {result.get('error')}"
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_rapide_todo_simple():
    """Test workflow RAPIDE sur projet TODO simple."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_rapide_todo_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_rapide_todo",
            user_request="""Crée une classe TodoList Python simple avec :
- Méthode add_task(task: str)
- Méthode get_tasks() -> list
- Tests unitaires pytest

Fichiers attendus :
- todo.py
- test_todo.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        assert result["mode"] == "FAST", f"Mode incorrect : {result['mode']}"
        
        # Afficher résultat
        print(f"\n📊 Résultat workflow RAPIDE - TODO :")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers : {result.get('files_created', [])}")
        print(f"   Tentatives correction : {result.get('correction_attempts', 0)}")
        
        # Vérifier que le workflow s'est exécuté
        assert "validation_result" in result, "Validation non exécutée"
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_rapide_gestion_erreurs():
    """Test que workflow RAPIDE gère les erreurs correctement."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_rapide_erreur_")
    
    try:
        # Créer mission avec demande ambiguë
        mission = Mission(
            mission_id="test_rapide_erreur",
            user_request="""Crée une fonction de division avec gestion d'erreurs.

Fonction division(a, b) qui :
- Retourne a / b
- Gère division par zéro (raise ValueError)
- Tests unitaires avec pytest.raises

Fichiers :
- division.py
- test_division.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        
        # Le workflow peut échouer ou réussir, on vérifie juste qu'il se termine
        print(f"\n📊 Résultat workflow RAPIDE - Gestion erreurs :")
        print(f"   Success : {result.get('success')}")
        print(f"   Validation : {result.get('validation_result')}")
        print(f"   Fichiers : {result.get('files_created', [])}")
        
        # Si succès, vérifier que les fichiers existent
        if result.get("success") and result.get("validation_result") == "VALID":
            files_created = result.get("files_created", [])
            for file_path in files_created:
                full_path = Path(temp_dir) / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    # Vérifier présence de gestion d'erreurs
                    assert "raise ValueError" in content or "ZeroDivisionError" in content, \
                        "Gestion d'erreurs manquante dans le code"
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_rapide_multifichiers():
    """Test workflow RAPIDE avec plusieurs fichiers."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_rapide_multi_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_rapide_multi",
            user_request="""Crée un système de calcul simple avec :

Fichiers :
1. operations.py : fonctions addition, soustraction, multiplication
2. calculator.py : classe Calculator qui utilise operations.py
3. test_operations.py : tests pour operations.py
4. test_calculator.py : tests pour Calculator

Maximum 4 fichiers.""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        # Afficher résultat
        files_created = result.get("files_created", [])
        print(f"\n📊 Résultat workflow RAPIDE - Multi-fichiers :")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers créés : {len(files_created)}")
        print(f"   Liste : {files_created}")
        
        # Si validation OK, vérifier nombre de fichiers
        if result["validation_result"] == "VALID":
            assert len(files_created) >= 2, f"Pas assez de fichiers créés : {len(files_created)}"
            assert len(files_created) <= 4, f"Trop de fichiers créés : {len(files_created)}"
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_rapide_timeout():
    """Test que workflow RAPIDE ne timeout pas."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_rapide_timeout_")
    
    try:
        # Créer mission simple
        mission = Mission(
            mission_id="test_rapide_timeout",
            user_request="Crée une fonction Python hello_world() qui retourne 'Hello, World!' avec un test.",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE avec timeout pytest (5 min)
        import asyncio
        orchestrator = SimpleOrchestrator()
        result = await asyncio.wait_for(
            orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir),
            timeout=300  # 5 minutes max
        )
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        print(f"\n✅ Workflow RAPIDE - Timeout : Terminé en moins de 5 min")
        
    except asyncio.TimeoutError:
        pytest.fail("Workflow RAPIDE a timeout (>5 min)")
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
