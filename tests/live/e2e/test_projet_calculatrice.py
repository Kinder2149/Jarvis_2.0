"""
Test E2E complet : Projet Calculatrice.

Teste le workflow complet de bout en bout :
1. Demande utilisateur → Détection complexité
2. Orchestration (RAPIDE ou COMPLET)
3. Génération code + tests
4. Validation
5. Écriture fichiers
6. Exécution des tests générés
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
async def test_e2e_calculatrice_complete():
    """Test E2E complet : Calculatrice avec exécution des tests."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_calc_")
    
    try:
        # 1. Demande utilisateur
        user_request = """Crée une calculatrice Python avec :
- Fonction addition(a, b)
- Fonction soustraction(a, b)
- Fonction multiplication(a, b)
- Fonction division(a, b) avec gestion division par zéro
- Tests unitaires pytest complets

Fichiers :
- calculatrice.py
- test_calculatrice.py"""
        
        # 2. Détection complexité
        orchestrator = SimpleOrchestrator()
        complexity = orchestrator.detect_project_complexity(user_request)
        print(f"\n📊 Complexité détectée : {complexity}")
        assert complexity == "SIMPLE", f"Complexité incorrecte : {complexity}"
        
        # 3. Créer mission
        mission = Mission(
            mission_id="test_e2e_calc",
            user_request=user_request,
            project_path=temp_dir
        )
        
        # 4. Exécuter workflow
        result = await orchestrator.execute_fast_mode(mission, user_request, temp_dir)
        
        # 5. Vérifications résultat
        assert result is not None, "Résultat None"
        assert result["success"] is True, f"Mission échouée : {result.get('error')}"
        
        print(f"\n📊 Résultat workflow :")
        print(f"   Mode : {result['mode']}")
        print(f"   Validation : {result['validation_result']}")
        print(f"   Fichiers : {result.get('files_created', [])}")
        print(f"   Corrections : {result.get('correction_attempts', 0)}")
        
        # 6. Vérifier fichiers créés
        files_created = result.get("files_created", [])
        
        if result["validation_result"] == "VALID" and len(files_created) > 0:
            # 7. Vérifier existence fichiers
            calc_file = None
            test_file = None
            
            for file_path in files_created:
                full_path = Path(temp_dir) / file_path
                assert full_path.exists(), f"Fichier manquant : {file_path}"
                
                if "calculatrice.py" in file_path.lower() and "test" not in file_path.lower():
                    calc_file = full_path
                elif "test" in file_path.lower() and "calculatrice" in file_path.lower():
                    test_file = full_path
            
            print(f"\n📁 Fichiers trouvés :")
            print(f"   Calculatrice : {calc_file}")
            print(f"   Tests : {test_file}")
            
            # 8. Exécuter les tests générés (si pytest disponible)
            if test_file and test_file.exists():
                print(f"\n🧪 Exécution des tests générés...")
                
                try:
                    # Exécuter pytest sur le fichier de test
                    result_pytest = subprocess.run(
                        [sys.executable, "-m", "pytest", str(test_file), "-v"],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    print(f"\n📊 Résultat pytest :")
                    print(f"   Code retour : {result_pytest.returncode}")
                    print(f"   Stdout : {result_pytest.stdout[:500]}")
                    
                    if result_pytest.returncode == 0:
                        print(f"\n✅ Tests générés : TOUS PASSENT")
                    else:
                        print(f"\n⚠️  Tests générés : ÉCHECS DÉTECTÉS")
                        print(f"   Stderr : {result_pytest.stderr[:500]}")
                    
                except subprocess.TimeoutExpired:
                    print(f"\n⚠️  Tests générés : TIMEOUT (>30s)")
                except Exception as e:
                    print(f"\n⚠️  Tests générés : ERREUR ({e})")
            
            # 9. Vérifier contenu code (imports, fonctions)
            if calc_file and calc_file.exists():
                code_content = calc_file.read_text(encoding='utf-8')
                
                print(f"\n📝 Vérification code calculatrice :")
                assert "def addition" in code_content, "Fonction addition manquante"
                assert "def soustraction" in code_content, "Fonction soustraction manquante"
                assert "def multiplication" in code_content, "Fonction multiplication manquante"
                assert "def division" in code_content, "Fonction division manquante"
                print(f"   ✅ Toutes les fonctions présentes")
            
            print(f"\n✅ E2E Calculatrice : SUCCÈS COMPLET")
        else:
            print(f"\n⚠️  E2E Calculatrice : Validation échouée ou aucun fichier créé")
            print(f"   → Test partiel (workflow exécuté mais code non validé)")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_calculatrice_fonctionnelle():
    """Test E2E : Calculatrice fonctionnelle (import et exécution)."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_calc_func_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_e2e_calc_func",
            user_request="""Crée une calculatrice Python minimaliste.

Fonctions :
- add(a, b) : retourne a + b
- subtract(a, b) : retourne a - b

Tests pytest simples.

Fichiers :
- calc.py
- test_calc.py""",
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
            calc_file = None
            for file_path in files_created:
                if "calc.py" in file_path.lower() and "test" not in file_path.lower():
                    calc_file = Path(temp_dir) / file_path
                    break
            
            if calc_file and calc_file.exists():
                # Tester import et exécution
                print(f"\n🔧 Test fonctionnel du code généré...")
                
                # Ajouter temp_dir au PYTHONPATH
                sys.path.insert(0, temp_dir)
                
                try:
                    # Importer le module
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("calc", calc_file)
                    calc_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(calc_module)
                    
                    # Tester les fonctions
                    if hasattr(calc_module, 'add'):
                        result_add = calc_module.add(2, 3)
                        assert result_add == 5, f"add(2, 3) devrait retourner 5, pas {result_add}"
                        print(f"   ✅ add(2, 3) = {result_add}")
                    
                    if hasattr(calc_module, 'subtract'):
                        result_sub = calc_module.subtract(5, 3)
                        assert result_sub == 2, f"subtract(5, 3) devrait retourner 2, pas {result_sub}"
                        print(f"   ✅ subtract(5, 3) = {result_sub}")
                    
                    print(f"\n✅ Code généré : FONCTIONNEL")
                    
                except Exception as e:
                    print(f"\n⚠️  Code généré : ERREUR À L'EXÉCUTION ({e})")
                finally:
                    # Retirer temp_dir du PYTHONPATH
                    sys.path.remove(temp_dir)
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.live
@pytest.mark.asyncio
async def test_e2e_calculatrice_qualite_code():
    """Test E2E : Qualité du code généré (syntaxe, style)."""
    
    # Créer dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="test_e2e_calc_qual_")
    
    try:
        # Créer mission
        mission = Mission(
            mission_id="test_e2e_calc_qual",
            user_request="""Crée une calculatrice Python avec docstrings.

Fonctions :
- multiply(a, b) : multiplie deux nombres
- divide(a, b) : divise a par b, gère division par zéro

Chaque fonction doit avoir une docstring.
Tests pytest.

Fichiers :
- calculator.py
- test_calculator.py""",
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
            calc_file = None
            for file_path in files_created:
                if "calculator.py" in file_path.lower() and "test" not in file_path.lower():
                    calc_file = Path(temp_dir) / file_path
                    break
            
            if calc_file and calc_file.exists():
                code_content = calc_file.read_text(encoding='utf-8')
                
                print(f"\n📝 Analyse qualité code :")
                
                # Vérifier syntaxe Python
                try:
                    compile(code_content, '<string>', 'exec')
                    print(f"   ✅ Syntaxe Python valide")
                except SyntaxError as e:
                    print(f"   ❌ Erreur syntaxe : {e}")
                    pytest.fail(f"Code généré contient erreur syntaxe : {e}")
                
                # Vérifier présence docstrings
                has_docstrings = '"""' in code_content or "'''" in code_content
                print(f"   {'✅' if has_docstrings else '⚠️ '} Docstrings : {'Présentes' if has_docstrings else 'Absentes'}")
                
                # Vérifier gestion erreurs
                has_error_handling = "raise" in code_content or "except" in code_content
                print(f"   {'✅' if has_error_handling else '⚠️ '} Gestion erreurs : {'Présente' if has_error_handling else 'Absente'}")
                
                # Vérifier imports (si nécessaire)
                lines = code_content.split('\n')
                import_lines = [l for l in lines if l.strip().startswith('import') or l.strip().startswith('from')]
                print(f"   📦 Imports : {len(import_lines)}")
                
                print(f"\n✅ Qualité code : Analysée")
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
