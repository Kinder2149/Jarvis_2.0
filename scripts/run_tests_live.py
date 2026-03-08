"""
Script de lancement global pour tous les tests live JARVIS 2.0.

Usage:
    python scripts/run_tests_live.py [options]

Options:
    --unit          : Exécuter uniquement les tests unitaires
    --integration   : Exécuter uniquement les tests d'intégration
    --e2e           : Exécuter uniquement les tests E2E
    --all           : Exécuter tous les tests (défaut)
    --verbose       : Mode verbeux
    --stop-on-fail  : Arrêter à la première erreur
"""

import sys
import subprocess
from pathlib import Path
import argparse

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def run_tests(test_path: str, verbose: bool = False, stop_on_fail: bool = False) -> int:
    """
    Exécute les tests pytest pour un chemin donné.
    
    Args:
        test_path: Chemin vers les tests
        verbose: Mode verbeux
        stop_on_fail: Arrêter à la première erreur
    
    Returns:
        Code retour pytest (0 = succès, >0 = échecs)
    """
    cmd = [sys.executable, "-m", "pytest", test_path, "-m", "live"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if stop_on_fail:
        cmd.append("-x")
    
    # Ajouter options pytest
    cmd.extend([
        "--tb=short",  # Traceback court
        "--color=yes",  # Couleurs
    ])
    
    print(f"\n{'='*80}")
    print(f"🧪 Exécution : {test_path}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd, cwd=root_dir)
    return result.returncode

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Lancement des tests live JARVIS 2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python scripts/run_tests_live.py --unit
  python scripts/run_tests_live.py --integration --verbose
  python scripts/run_tests_live.py --e2e --stop-on-fail
  python scripts/run_tests_live.py --all
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="Tests unitaires uniquement")
    parser.add_argument("--integration", action="store_true", help="Tests d'intégration uniquement")
    parser.add_argument("--e2e", action="store_true", help="Tests E2E uniquement")
    parser.add_argument("--all", action="store_true", help="Tous les tests (défaut)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux")
    parser.add_argument("-x", "--stop-on-fail", action="store_true", help="Arrêter à la première erreur")
    
    args = parser.parse_args()
    
    # Si aucune option, exécuter tous les tests
    if not (args.unit or args.integration or args.e2e):
        args.all = True
    
    tests_dir = root_dir / "tests" / "live"
    
    # Vérifier que le dossier existe
    if not tests_dir.exists():
        print(f"❌ Erreur : Dossier tests live introuvable : {tests_dir}")
        return 1
    
    print("\n" + "="*80)
    print("🚀 LANCEMENT TESTS LIVE JARVIS 2.0")
    print("="*80)
    print(f"\n📁 Dossier tests : {tests_dir}")
    print(f"🔧 Options : verbose={args.verbose}, stop_on_fail={args.stop_on_fail}")
    
    results = {}
    
    # Tests unitaires
    if args.unit or args.all:
        unit_dir = tests_dir / "unit"
        if unit_dir.exists():
            results["unit"] = run_tests(str(unit_dir), args.verbose, args.stop_on_fail)
        else:
            print(f"\n⚠️  Dossier unit/ introuvable : {unit_dir}")
    
    # Tests d'intégration
    if args.integration or args.all:
        integration_dir = tests_dir / "integration"
        if integration_dir.exists():
            results["integration"] = run_tests(str(integration_dir), args.verbose, args.stop_on_fail)
        else:
            print(f"\n⚠️  Dossier integration/ introuvable : {integration_dir}")
    
    # Tests E2E
    if args.e2e or args.all:
        e2e_dir = tests_dir / "e2e"
        if e2e_dir.exists():
            results["e2e"] = run_tests(str(e2e_dir), args.verbose, args.stop_on_fail)
        else:
            print(f"\n⚠️  Dossier e2e/ introuvable : {e2e_dir}")
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80 + "\n")
    
    total_success = 0
    total_failed = 0
    
    for test_type, return_code in results.items():
        status = "✅ SUCCÈS" if return_code == 0 else "❌ ÉCHECS"
        print(f"  {test_type.upper():15} : {status}")
        
        if return_code == 0:
            total_success += 1
        else:
            total_failed += 1
    
    print(f"\n{'='*80}")
    print(f"Total : {total_success} succès, {total_failed} échecs")
    print(f"{'='*80}\n")
    
    # Code retour global
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
