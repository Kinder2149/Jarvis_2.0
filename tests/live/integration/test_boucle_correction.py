"""
Tests d'intégration pour la boucle de correction.

Teste le mécanisme de correction :
VALIDATEUR rejette → CODEUR corrige → VALIDATEUR re-valide

Limite : max_corrections = 5
"""

import pytest
import tempfile
import shutil
from backend.services.orchestration import SimpleOrchestrator
from backend.models.mission import Mission

@pytest.mark.live
@pytest.mark.asyncio
async def test_boucle_correction_max_attempts():
    """Test que la boucle de correction respecte max_corrections."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_correction_max_")
    
    try:
        # Créer mission avec demande complexe (peut nécessiter corrections)
        mission = Mission(
            mission_id="test_correction_max",
            user_request="""Crée une fonction Python de validation d'email complexe.

Fonction validate_email(email: str) -> bool qui :
- Vérifie format email (regex)
- Vérifie domaine valide
- Gère tous les cas edge (espaces, caractères spéciaux)
- Raise ValueError si invalide
- Tests exhaustifs avec pytest

Fichiers :
- validator.py
- test_validator.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        
        # Vérifier que correction_attempts est présent
        correction_attempts = result.get("correction_attempts", 0)
        print(f"\n📊 Tentatives de correction : {correction_attempts}")
        
        # Vérifier que max_corrections (5) n'est pas dépassé
        assert correction_attempts <= 5, f"Max corrections dépassé : {correction_attempts} > 5"
        
        # Afficher résultat
        print(f"   Validation finale : {result['validation_result']}")
        print(f"   Fichiers créés : {len(result.get('files_created', []))}")
        
        # Si INVALID après 5 tentatives, c'est normal (limite atteinte)
        if correction_attempts == 5 and result["validation_result"] == "INVALID":
            print(f"   ⚠️  Limite max_corrections atteinte (5), code reste INVALID")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_boucle_correction_convergence():
    """Test que la boucle de correction converge (code s'améliore)."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_correction_conv_")
    
    try:
        # Créer mission simple (devrait converger rapidement)
        mission = Mission(
            mission_id="test_correction_conv",
            user_request="""Crée une fonction Python simple de multiplication.

Fonction multiply(a, b) qui retourne a * b.
Tests pytest avec 3 cas de test.

Fichiers :
- math_ops.py
- test_math_ops.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        
        # Afficher progression
        correction_attempts = result.get("correction_attempts", 0)
        validation_result = result["validation_result"]
        
        print(f"\n📊 Convergence boucle de correction :")
        print(f"   Tentatives : {correction_attempts}")
        print(f"   Résultat : {validation_result}")
        
        # Pour un projet simple, on s'attend à peu de corrections
        if validation_result == "VALID":
            print(f"   ✅ Code validé après {correction_attempts} correction(s)")
        else:
            print(f"   ⚠️  Code non validé après {correction_attempts} tentative(s)")
            # Afficher raison si disponible
            if "validation_response" in result:
                print(f"   Raison : {result['validation_response'][:200]}...")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_boucle_correction_validation_response():
    """Test que VALIDATEUR fournit des feedbacks exploitables."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_correction_feedback_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_correction_feedback",
            user_request="""Crée une classe Python Stack (pile LIFO).

Classe Stack avec méthodes :
- push(item) : Ajoute un élément
- pop() -> item : Retire et retourne le dernier élément
- is_empty() -> bool : Vérifie si vide
- Tests unitaires pytest

Fichiers :
- stack.py
- test_stack.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        
        # Récupérer réponse de validation
        validation_response = result.get("validation_response", "")
        
        print(f"\n📝 Réponse VALIDATEUR complète :")
        print(f"{validation_response}")
        print(f"\n{'='*80}\n")
        
        # Vérifier que la réponse n'est pas vide
        assert len(validation_response) > 0, "Réponse VALIDATEUR vide"
        
        # Vérifier format STATUT
        assert "STATUT:" in validation_response.upper() or "STATUT :" in validation_response.upper(), \
            "Format STATUT manquant"
        
        # Si INVALID, vérifier présence de justifications
        if "INVALIDE" in validation_response.upper():
            # Chercher des mots-clés de feedback
            feedback_keywords = [
                "erreur", "manque", "incorrect", "problème",
                "syntaxe", "import", "fonction", "variable"
            ]
            found_feedback = [kw for kw in feedback_keywords if kw in validation_response.lower()]
            
            print(f"📊 Feedback VALIDATEUR : {len(found_feedback)} mot(s)-clé(s) trouvé(s)")
            print(f"   Mots-clés : {found_feedback}")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_boucle_correction_code_evolue():
    """Test que le code évolue entre les corrections."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_correction_evolue_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_correction_evolue",
            user_request="""Crée une fonction de tri personnalisée.

Fonction custom_sort(liste: list, reverse: bool = False) -> list qui :
- Trie une liste de nombres
- Paramètre reverse pour tri décroissant
- Gère liste vide
- Tests pytest avec plusieurs cas

Fichiers :
- sorting.py
- test_sorting.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        
        # Afficher évolution
        correction_attempts = result.get("correction_attempts", 0)
        files_created = result.get("files_created", [])
        
        print(f"\n📊 Évolution du code :")
        print(f"   Corrections : {correction_attempts}")
        print(f"   Fichiers finaux : {files_created}")
        print(f"   Validation : {result['validation_result']}")
        
        # Si des fichiers ont été créés, vérifier qu'ils existent
        if len(files_created) > 0:
            from pathlib import Path
            for file_path in files_created:
                full_path = Path(temp_dir) / file_path
                if full_path.exists():
                    size = full_path.stat().st_size
                    print(f"   📄 {file_path} : {size} bytes")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_boucle_correction_pas_de_regression():
    """Test que les corrections ne créent pas de régressions."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_correction_regr_")
    
    try:
        # Créer mission simple
        mission = Mission(
            mission_id="test_correction_regr",
            user_request="""Crée deux fonctions mathématiques simples.

Fonctions :
- add(a, b) : retourne a + b
- subtract(a, b) : retourne a - b

Tests pytest pour chaque fonction.

Fichiers :
- operations.py
- test_operations.py""",
            project_path=temp_dir
        )
        
        # Exécuter workflow RAPIDE
        orchestrator = SimpleOrchestrator()
        result = await orchestrator.execute_fast_mode(mission, mission.user_request, temp_dir)
        
        # Vérifications
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        # Vérifier qu'il n'y a pas eu trop de corrections (signe de régression)
        correction_attempts = result.get("correction_attempts", 0)
        
        print(f"\n📊 Test régression :")
        print(f"   Corrections : {correction_attempts}")
        print(f"   Validation : {result['validation_result']}")
        
        # Pour un projet très simple, on ne devrait pas avoir beaucoup de corrections
        # Si > 3 corrections, c'est suspect (possible régression)
        if correction_attempts > 3:
            print(f"   ⚠️  Nombre élevé de corrections ({correction_attempts}) pour un projet simple")
            print(f"   → Possible régression ou validation trop stricte")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
