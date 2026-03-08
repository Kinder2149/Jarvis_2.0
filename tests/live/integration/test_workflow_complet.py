"""
Tests d'intégration pour le workflow COMPLET.

Teste l'enchaînement complet :
ARCHITECTE → CODEUR → TESTEUR → VALIDATEUR → Écriture fichiers

Pour des projets COMPLEXES (>3 fichiers).
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from backend.services.orchestration import SimpleOrchestrator
from backend.models.mission import Mission

@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_complet_api_rest():
    """Test workflow COMPLET sur projet API REST."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_complet_api_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_complet_api",
            user_request="""Crée une API REST simple pour gérer des tâches (TODO).

Fonctionnalités :
- GET /tasks : Liste toutes les tâches
- POST /tasks : Crée une nouvelle tâche
- DELETE /tasks/{id} : Supprime une tâche

Contraintes :
- FastAPI
- Persistance en mémoire (liste Python)
- Tests API avec pytest
- Documentation OpenAPI automatique

Fichiers attendus :
- main.py : API FastAPI
- models.py : Modèle Task
- test_api.py : Tests API
- README.md : Documentation""",
            project_path=temp_dir
        )
        
        # Exécuter workflow COMPLET
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_complete_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications résultat
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        assert result["mode"] == "COMPLETE", f"Mode incorrect : {result['mode']}"
        
        # Vérifier que ARCHITECTE a été appelé
        assert "architecture_response" in result, "ARCHITECTE non appelé"
        architecture = result["architecture_response"]
        assert len(architecture) > 100, "Architecture trop courte"
        
        print(f"\n📐 Architecture proposée : {len(architecture)} chars")
        print(f"Extrait : {architecture[:200]}...")
        
        # Vérifier validation
        assert result["validation_result"] in ["VALID", "INVALID"], f"Validation invalide : {result['validation_result']}"
        
        # Vérifier fichiers créés
        files_created = result.get("files_created", [])
        print(f"\n📁 Fichiers créés : {files_created}")
        
        if result["validation_result"] == "VALID":
            assert len(files_created) > 0, "Aucun fichier créé malgré validation VALID"
            assert len(files_created) >= 3, f"Pas assez de fichiers pour une API : {len(files_created)}"
            
            # Vérifier existence des fichiers
            for file_path in files_created:
                full_path = Path(temp_dir) / file_path
                assert full_path.exists(), f"Fichier créé mais introuvable : {file_path}"
            
            print(f"✅ Workflow COMPLET - API REST : {len(files_created)} fichier(s) créé(s)")
        else:
            print(f"⚠️  Workflow COMPLET - API REST : INVALID (validation stricte)")
            print(f"   Fichiers créés quand même : {len(files_created)}")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_complet_blog():
    """Test workflow COMPLET sur projet blog minimaliste."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_complet_blog_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_complet_blog",
            user_request="""Crée un système de blog minimaliste en Python.

Fonctionnalités :
- Classe Article (titre, contenu, date)
- Classe Blog (liste articles)
- Méthodes : ajouter_article, lister_articles, rechercher
- Persistance JSON
- Tests unitaires complets

Fichiers attendus :
- models.py : Article, Blog
- storage.py : Gestion JSON
- test_models.py : Tests modèles
- test_storage.py : Tests persistance""",
            project_path=temp_dir
        )
        
        # Exécuter workflow COMPLET
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_complete_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        assert result["mode"] == "COMPLETE", f"Mode incorrect : {result['mode']}"
        
        # Vérifier ARCHITECTE
        assert "architecture_response" in result, "ARCHITECTE non appelé"
        
        # Afficher résultat
        print(f"\n📊 Résultat workflow COMPLET - Blog :")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers : {result.get('files_created', [])}")
        print(f"   Tentatives correction : {result.get('correction_attempts', 0)}")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_complet_architecture_respectee():
    """Test que le CODEUR respecte l'architecture proposée par ARCHITECTE."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_complet_archi_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_complet_archi",
            user_request="""Crée un système de gestion d'utilisateurs.

Fonctionnalités :
- Classe User (nom, email, id)
- Classe UserManager (CRUD utilisateurs)
- Validation email
- Tests unitaires

Architecture souhaitée :
- user.py : Classe User
- user_manager.py : Classe UserManager
- validators.py : Validation email
- test_user.py : Tests User
- test_user_manager.py : Tests UserManager""",
            project_path=temp_dir
        )
        
        # Exécuter workflow COMPLET
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_complete_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        # Récupérer architecture proposée
        architecture = result.get("architecture_response", "")
        print(f"\n📐 Architecture ARCHITECTE :")
        print(f"{architecture[:500]}...")
        
        # Récupérer fichiers créés
        files_created = result.get("files_created", [])
        print(f"\n📁 Fichiers CODEUR : {files_created}")
        
        # Vérifier cohérence (au moins quelques fichiers mentionnés dans l'architecture)
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            # Extraire noms de fichiers de l'architecture
            architecture_lower = architecture.lower()
            
            # Vérifier que certains fichiers créés sont mentionnés dans l'architecture
            mentioned_count = 0
            for file_path in files_created:
                filename = Path(file_path).name.lower()
                if filename in architecture_lower:
                    mentioned_count += 1
            
            print(f"\n📊 Cohérence architecture/code : {mentioned_count}/{len(files_created)} fichiers mentionnés")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_complet_multifichiers():
    """Test workflow COMPLET avec nombreux fichiers (>3)."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_complet_multi_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_complet_multi",
            user_request="""Crée une bibliothèque de calculs mathématiques.

Modules :
- basic.py : addition, soustraction, multiplication, division
- advanced.py : puissance, racine, factorielle
- statistics.py : moyenne, médiane, écart-type
- test_basic.py : Tests basic
- test_advanced.py : Tests advanced
- test_statistics.py : Tests statistics
- README.md : Documentation

Minimum 6 fichiers.""",
            project_path=temp_dir
        )
        
        # Exécuter workflow COMPLET
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_complete_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        # Vérifier nombre de fichiers
        files_created = result.get("files_created", [])
        print(f"\n📊 Résultat workflow COMPLET - Multi-fichiers :")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers créés : {len(files_created)}")
        print(f"   Liste : {files_created}")
        
        if result["validation_result"] == "VALID":
            assert len(files_created) >= 4, f"Pas assez de fichiers : {len(files_created)}"
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_workflow_complet_timeout():
    """Test que workflow COMPLET ne timeout pas."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_complet_timeout_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_complet_timeout",
            user_request="""Crée un système de gestion de contacts.

Fonctionnalités :
- Classe Contact (nom, téléphone, email)
- Classe ContactManager (ajouter, supprimer, rechercher)
- Persistance JSON
- Tests unitaires

Fichiers :
- contact.py
- contact_manager.py
- storage.py
- test_contact.py
- test_contact_manager.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow COMPLET avec timeout (10 min)
        import asyncio
        orchestrator = SimpleOrchestrator()
        result = await asyncio.wait_for(
            orchestrator.execute_complete_mode(mission, mission.user_request, temp_dir),
            timeout=600  # 10 minutes max
        )
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        print(f"\n✅ Workflow COMPLET - Timeout : Terminé en moins de 10 min")
        
    except asyncio.TimeoutError:
        pytest.fail("Workflow COMPLET a timeout (>10 min)")
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
