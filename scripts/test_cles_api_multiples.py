"""
Script de test manuel pour vérifier que chaque agent utilise sa propre clé API Gemini.

Usage:
    python scripts/test_cles_api_multiples.py
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
from backend.ia.providers.provider_factory import ProviderFactory

# Charger .env
load_dotenv()

def test_cles_api():
    """Teste que chaque agent a sa propre clé API."""
    
    print("=" * 80)
    print("TEST : Vérification des clés API multiples par agent")
    print("=" * 80)
    print()
    
    agents = ["ARCHITECTE", "JARVIS_Maître", "CODEUR", "TESTEUR", "VALIDATEUR"]
    
    # Vider le cache pour forcer la recréation
    ProviderFactory.clear_cache()
    
    cles_trouvees = {}
    
    for agent in agents:
        print(f"🔍 Test agent : {agent}")
        
        try:
            # Créer le provider pour cet agent
            provider = ProviderFactory.create(agent)
            
            # Récupérer la clé API (afficher seulement les 20 premiers caractères)
            cle_api = provider.api_key
            cle_affichee = f"{cle_api[:20]}..." if len(cle_api) > 20 else cle_api
            
            # Vérifier si clé spécifique ou globale
            env_agent_name = agent.upper().replace("Î", "I").replace("È", "E")
            if env_agent_name == "JARVIS_MAÎTRE":
                env_agent_name = "JARVIS_MAITRE"
            
            cle_specifique = os.getenv(f"GEMINI_API_KEY_{env_agent_name}")
            cle_globale = os.getenv("GEMINI_API_KEY")
            
            if cle_specifique and cle_api == cle_specifique:
                print(f"   ✅ Clé spécifique : {cle_affichee}")
                cles_trouvees[agent] = "spécifique"
            elif cle_api == cle_globale:
                print(f"   ⚠️  Clé globale : {cle_affichee}")
                cles_trouvees[agent] = "globale"
            else:
                print(f"   ❓ Clé inconnue : {cle_affichee}")
                cles_trouvees[agent] = "inconnue"
            
            print(f"   📦 Modèle : {provider.model}")
            print()
            
        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            print()
            cles_trouvees[agent] = "erreur"
    
    # Résumé
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print()
    
    nb_specifiques = sum(1 for v in cles_trouvees.values() if v == "spécifique")
    nb_globales = sum(1 for v in cles_trouvees.values() if v == "globale")
    nb_erreurs = sum(1 for v in cles_trouvees.values() if v == "erreur")
    
    print(f"✅ Clés spécifiques : {nb_specifiques}/{len(agents)}")
    print(f"⚠️  Clés globales : {nb_globales}/{len(agents)}")
    print(f"❌ Erreurs : {nb_erreurs}/{len(agents)}")
    print()
    
    # Vérifier unicité des clés
    cles_uniques = set()
    for agent in agents:
        try:
            provider = ProviderFactory.create(agent)
            cles_uniques.add(provider.api_key)
        except:
            pass
    
    print(f"🔑 Clés API uniques : {len(cles_uniques)}")
    print()
    
    # Verdict
    if nb_specifiques == len(agents):
        print("🎉 SUCCÈS : Tous les agents ont leur clé API spécifique !")
        return True
    elif nb_globales == len(agents):
        print("⚠️  ATTENTION : Tous les agents utilisent la clé globale")
        print("   → Vérifier que les variables GEMINI_API_KEY_{AGENT} sont définies dans .env")
        return False
    else:
        print("⚠️  MIXTE : Certains agents ont des clés spécifiques, d'autres non")
        print("   → Configuration partielle détectée")
        return False

if __name__ == "__main__":
    success = test_cles_api()
    sys.exit(0 if success else 1)
