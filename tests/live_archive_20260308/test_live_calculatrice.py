"""
Test live : Projet calculatrice simple
Nécessite API Gemini active
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from backend.services.orchestration import SimpleOrchestrator


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_calculatrice():
    """
    Test live : Génération d'une calculatrice Python simple
    
    Ce test appelle réellement les agents Gemini pour générer du code.
    Il vérifie que le workflow RAPIDE fonctionne de bout en bout.
    """
    # Créer dossier temporaire pour le projet
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir) / "calculatrice"
    project_path.mkdir()
    
    try:
        orchestrator = SimpleOrchestrator()
        
        # Exécuter mission
        result = await orchestrator.start_mission(
            user_request=(
                "Crée une calculatrice Python simple avec les fonctions : "
                "addition, soustraction, multiplication, division. "
                "Ajoute une fonction main() qui demande à l'utilisateur de choisir une opération."
            ),
            project_name="calculatrice",
            project_path=str(project_path)
        )
        
        # Vérifications de base
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        assert result["mode"] == "FAST", "Devrait utiliser mode RAPIDE"
        
        # Vérifier que des fichiers ont été créés
        files_created = result.get("files_created", [])
        assert len(files_created) > 0, "Aucun fichier créé"
        
        # Vérifier qu'au moins un fichier Python existe
        python_files = [f for f in files_created if f.endswith('.py')]
        assert len(python_files) > 0, "Aucun fichier Python créé"
        
        # Vérifier que les fichiers existent réellement sur disque
        for file_path in files_created:
            full_path = project_path / file_path
            assert full_path.exists(), f"Fichier {file_path} n'existe pas sur disque"
        
        # Vérifier contenu du fichier principal
        main_file = None
        for f in python_files:
            if "calculatrice" in f.lower() or "main" in f.lower():
                main_file = project_path / f
                break
        
        if main_file and main_file.exists():
            content = main_file.read_text(encoding='utf-8')
            
            # Vérifier présence des fonctions attendues
            assert "def" in content, "Aucune fonction définie"
            
            # Vérifier au moins quelques opérations
            operations_found = sum([
                "addition" in content.lower() or "add" in content.lower(),
                "soustraction" in content.lower() or "subtract" in content.lower(),
                "multiplication" in content.lower() or "multiply" in content.lower(),
                "division" in content.lower() or "divide" in content.lower()
            ])
            assert operations_found >= 2, "Moins de 2 opérations trouvées dans le code"
        
        # Vérifier que des tests ont été créés
        test_files = [f for f in files_created if "test" in f.lower()]
        assert len(test_files) > 0, "Aucun fichier de test créé"
        
        print(f"\n✅ Test live calculatrice réussi !")
        print(f"   Mode : {result['mode']}")
        print(f"   Fichiers créés : {len(files_created)}")
        print(f"   Fichiers Python : {len(python_files)}")
        print(f"   Fichiers tests : {len(test_files)}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_calculatrice_code_quality():
    """
    Test live : Vérification qualité du code généré
    """
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir) / "calculatrice"
    project_path.mkdir()
    
    try:
        orchestrator = SimpleOrchestrator()
        
        result = await orchestrator.start_mission(
            user_request="Crée une calculatrice Python avec addition et soustraction",
            project_name="calculatrice",
            project_path=str(project_path)
        )
        
        assert result["success"] is True
        
        # Vérifier validation
        mission_id = result.get("mission_id")
        if mission_id:
            mission = orchestrator.mission_manager.get_mission(mission_id)
            
            # Vérifier que le code a été validé
            assert mission.code_validated is True, "Code non validé"
            assert mission.tests_validated is True, "Tests non validés"
        
        print(f"\n✅ Test qualité code réussi !")
        
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_calculatrice_files_structure():
    """
    Test live : Vérification structure des fichiers
    """
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir) / "calculatrice"
    project_path.mkdir()
    
    try:
        orchestrator = SimpleOrchestrator()
        
        result = await orchestrator.start_mission(
            user_request=(
                "Crée une calculatrice Python simple. "
                "Sépare le code en modules : un fichier pour les opérations, "
                "un fichier pour l'interface utilisateur."
            ),
            project_name="calculatrice",
            project_path=str(project_path)
        )
        
        assert result["success"] is True
        
        files_created = result.get("files_created", [])
        
        # Vérifier qu'il y a plusieurs fichiers Python
        python_files = [f for f in files_created if f.endswith('.py') and not f.startswith('test_')]
        assert len(python_files) >= 2, f"Attendu au moins 2 fichiers Python, trouvé {len(python_files)}"
        
        # Vérifier que chaque fichier a du contenu
        for file_path in python_files:
            full_path = project_path / file_path
            content = full_path.read_text(encoding='utf-8')
            assert len(content) > 50, f"Fichier {file_path} trop court"
        
        print(f"\n✅ Test structure fichiers réussi !")
        print(f"   Fichiers Python : {python_files}")
        
    finally:
        shutil.rmtree(temp_dir)
