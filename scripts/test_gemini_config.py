"""
Script de validation configuration Gemini 5 agents
Teste l'accessibilité de chaque modèle configuré
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Charger .env
load_dotenv()

def test_gemini_import():
    """Teste si google.generativeai est installé"""
    try:
        import google.generativeai as genai
        print("✅ google.generativeai installé")
        return True, genai
    except ImportError:
        print("❌ google.generativeai non installé")
        print("   Installer avec: pip install google-generativeai")
        return False, None

def test_api_key():
    """Teste si clé API est configurée"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY non configurée dans .env")
        return False
    
    if len(api_key) < 20:
        print("⚠️  GEMINI_API_KEY semble invalide (trop courte)")
        return False
    
    print(f"✅ GEMINI_API_KEY configurée ({api_key[:10]}...)")
    return True

def test_agent_model(genai, agent_name: str, model_name: str) -> bool:
    """Teste si modèle est accessible pour un agent"""
    if not model_name:
        print(f"❌ {agent_name}: Modèle non configuré")
        return False
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Test")
        
        if response and response.text:
            print(f"✅ {agent_name}: {model_name} - OK")
            return True
        else:
            print(f"⚠️  {agent_name}: {model_name} - Réponse vide")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower():
            print(f"⚠️  {agent_name}: {model_name} - QUOTA ÉPUISÉ")
        elif "not found" in error_msg.lower():
            print(f"❌ {agent_name}: {model_name} - MODÈLE INTROUVABLE")
        else:
            print(f"❌ {agent_name}: {model_name} - ERREUR: {error_msg[:100]}")
        return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔍 Test Configuration Gemini 5 Agents - JARVIS 2.0")
    print("=" * 60)
    print()
    
    # 1. Test import
    print("📦 Vérification dépendances...")
    success, genai = test_gemini_import()
    if not success:
        return 1
    print()
    
    # 2. Test clé API
    print("🔑 Vérification clé API...")
    if not test_api_key():
        return 1
    
    # Configurer genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    print()
    
    # 3. Test modèles agents
    print("🤖 Test modèles agents...")
    print()
    
    agents = {
        "JARVIS_Maître": os.getenv("JARVIS_MAITRE_MODEL", "gemini-2.5-pro"),
        "ARCHITECTE": os.getenv("ARCHITECTE_MODEL", "gemini-2.5-pro"),
        "CODEUR": os.getenv("CODEUR_MODEL", "gemini-2.5-pro"),
        "TESTEUR": os.getenv("TESTEUR_MODEL", "gemini-2.0-flash"),
        "VALIDATEUR": os.getenv("VALIDATEUR_MODEL", "gemini-3.1-pro-preview"),
        "BASE": os.getenv("BASE_MODEL", "gemini-2.5-pro"),
    }
    
    results = {}
    for agent, model in agents.items():
        results[agent] = test_agent_model(genai, agent, model)
    
    # 4. Résumé
    print()
    print("=" * 60)
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"📊 Résultats: {success_count}/{total_count} agents OK")
    print()
    
    if all(results.values()):
        print("✅ Configuration validée - Tous les agents fonctionnels")
        return 0
    else:
        print("❌ Configuration incomplète - Certains agents non fonctionnels")
        print()
        print("Agents en échec:")
        for agent, success in results.items():
            if not success:
                print(f"  - {agent}: {agents[agent]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
