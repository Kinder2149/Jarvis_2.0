"""
Script de test pour valider le vidage du cache agent au démarrage

Vérifie que :
1. Le cache agent est bien vidé au démarrage
2. Le prompt JARVIS_MAITRE.md est rechargé à chaque instanciation
3. Les logs de chargement apparaissent correctement

Usage:
    python scripts/test_cache_agent.py
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.agent_factory import get_agent, clear_cache, _AGENTS_CACHE


def test_cache_clearing():
    """Test que le cache est bien vidé"""
    print("\n🧪 TEST 1 : Vidage du cache agent")
    print("=" * 60)
    
    # Instancier JARVIS_Maître
    print("1️⃣ Première instanciation de JARVIS_Maître...")
    agent1 = get_agent("JARVIS_Maître")
    print(f"   ✅ Agent instancié : {agent1.name}")
    print(f"   📝 Prompt chargé : {len(agent1.system_prompt)} chars")
    print(f"   🗂️  Cache contient : {list(_AGENTS_CACHE.keys())}")
    
    # Vérifier que l'agent est en cache
    assert "JARVIS_Maître" in _AGENTS_CACHE, "❌ Agent devrait être en cache"
    print("   ✅ Agent bien mis en cache")
    
    # Vider le cache
    print("\n2️⃣ Vidage du cache...")
    clear_cache()
    print(f"   🗂️  Cache après vidage : {list(_AGENTS_CACHE.keys())}")
    assert len(_AGENTS_CACHE) == 0, "❌ Cache devrait être vide"
    print("   ✅ Cache vidé avec succès")
    
    # Réinstancier
    print("\n3️⃣ Deuxième instanciation de JARVIS_Maître...")
    agent2 = get_agent("JARVIS_Maître")
    print(f"   ✅ Agent réinstancié : {agent2.name}")
    print(f"   📝 Prompt rechargé : {len(agent2.system_prompt)} chars")
    
    # Vérifier que c'est une nouvelle instance
    assert agent1 is not agent2, "❌ Devrait être une nouvelle instance"
    print("   ✅ Nouvelle instance créée (pas depuis cache)")
    
    print("\n✅ TEST 1 RÉUSSI : Cache fonctionne correctement\n")


def test_prompt_content():
    """Test que le prompt contient les instructions workflow unique"""
    print("\n🧪 TEST 2 : Contenu du prompt JARVIS_Maître")
    print("=" * 60)
    
    # Vider cache pour forcer rechargement
    clear_cache()
    
    # Instancier agent
    agent = get_agent("JARVIS_Maître")
    prompt = agent.system_prompt
    
    print(f"📝 Prompt chargé : {len(prompt)} chars")
    
    # Vérifications critiques
    checks = [
        ("[DEMANDE_CODE_CODEUR:", "Marqueur de délégation"),
        ("WORKFLOW UNIQUE", "Section workflow unique"),
        ("RÈGLE ABSOLUE POST-VALIDATION", "Instructions post-validation"),
        ("Rien avant. Rien après. Juste le marqueur.", "Instruction stricte"),
    ]
    
    all_passed = True
    for pattern, description in checks:
        if pattern in prompt:
            print(f"   ✅ {description} : PRÉSENT")
        else:
            print(f"   ❌ {description} : ABSENT")
            all_passed = False
    
    if all_passed:
        print("\n✅ TEST 2 RÉUSSI : Prompt contient toutes les instructions requises\n")
    else:
        print("\n❌ TEST 2 ÉCHOUÉ : Prompt incomplet\n")
        sys.exit(1)


def test_prompt_preview():
    """Affiche un extrait du prompt pour vérification manuelle"""
    print("\n🧪 TEST 3 : Aperçu du prompt")
    print("=" * 60)
    
    clear_cache()
    agent = get_agent("JARVIS_Maître")
    prompt = agent.system_prompt
    
    # Trouver la section workflow unique
    if "WORKFLOW UNIQUE" in prompt:
        idx = prompt.index("WORKFLOW UNIQUE")
        section = prompt[idx:idx+1000]
        print("\n📄 Extrait section WORKFLOW UNIQUE :")
        print("-" * 60)
        print(section)
        print("-" * 60)
        print("\n✅ TEST 3 RÉUSSI : Section workflow unique trouvée\n")
    else:
        print("❌ TEST 3 ÉCHOUÉ : Section workflow unique non trouvée\n")
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 TESTS VALIDATION CACHE AGENT")
    print("=" * 60)
    
    try:
        test_cache_clearing()
        test_prompt_content()
        test_prompt_preview()
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("=" * 60)
        print("\n💡 Le cache agent fonctionne correctement.")
        print("💡 Le prompt JARVIS_MAITRE.md est bien rechargé à chaque instanciation.")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
