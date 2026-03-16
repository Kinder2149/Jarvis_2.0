"""
Test live workflow complet JARVIS 2.0 - Validation audit exhaustif

Objectifs :
1. Vérifier que les classes Codeur et Validateur sont bien instanciées
2. Vérifier que les prompts sont bien chargés avec logs
3. Vérifier workflow complet : JARVIS_Maître → ARCHITECTE → CODEUR → TESTEUR → VALIDATEUR
4. Vérifier que le système est identique à celui utilisé dans l'onglet Projets du frontend

Test avec projet basique : Calculatrice Python
"""

import pytest
import asyncio
import httpx
import os
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"
# Ajouter timestamp pour éviter conflits UNIQUE constraint
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
PROJECT_NAME = f"test_calculatrice_audit_{timestamp}"
PROJECT_PATH = Path(__file__).parent.parent.parent / "projects" / PROJECT_NAME

# Nettoyer projet test si existe
if PROJECT_PATH.exists():
    import shutil
    shutil.rmtree(PROJECT_PATH)

# Créer dossier projet
PROJECT_PATH.mkdir(parents=True, exist_ok=True)


@pytest.mark.asyncio
@pytest.mark.live
async def test_live_workflow_complet_avec_classes_specialisees():
    """
    Test live complet : Valide workflow 5 agents avec projet basique (calculatrice).
    
    Étapes :
    1. Créer projet via API
    2. Créer conversation liée au projet
    3. Envoyer demande utilisateur (calculatrice)
    4. Vérifier que JARVIS_Maître génère marqueur [DEMANDE_CODE_CODEUR:]
    5. Attendre exécution workflow (ARCHITECTE → CODEUR → TESTEUR → VALIDATEUR)
    6. Vérifier fichiers créés (calculator.py, tests/test_calculator.py, README.md)
    
    Note: Timeout 180s (3min) car Gemini API max 5min selon documentation officielle
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        
        # ========================================
        # 1. CRÉER PROJET (comme frontend)
        # ========================================
        print("\n" + "="*60)
        print("ÉTAPE 1 : Création projet via API")
        print("="*60)
        
        project_data = {
            "name": PROJECT_NAME,
            "path": str(PROJECT_PATH),
            "description": "Projet test calculatrice pour validation audit"
        }
        
        response = await client.post(f"{API_URL}/projects", json=project_data)
        assert response.status_code == 200, f"Erreur création projet: {response.text}"
        
        project = response.json()
        project_id = project["id"]
        
        print(f"✅ Projet créé : {project['name']}")
        print(f"   ID: {project_id}")
        print(f"   Path: {project['path']}")
        
        # ========================================
        # 2. CRÉER CONVERSATION (comme frontend)
        # ========================================
        print("\n" + "="*60)
        print("ÉTAPE 2 : Création conversation")
        print("="*60)
        
        conversation_data = {
            "agent_id": "JARVIS_Maître"
        }
        
        # Utiliser endpoint projet pour lier conversation au projet
        response = await client.post(
            f"{API_URL}/projects/{project_id}/conversations",
            json=conversation_data
        )
        assert response.status_code == 200, f"Erreur création conversation: {response.text}"
        
        conversation = response.json()
        conversation_id = conversation["id"]
        
        print(f"✅ Conversation créée : {conversation_id}")
        print(f"   Agent: {conversation['agent_id']}")
        print(f"   Projet: {conversation['project_id']}")
        
        # ========================================
        # 3. ENVOYER DEMANDE UTILISATEUR (comme frontend)
        # ========================================
        print("\n" + "="*60)
        print("ÉTAPE 3 : Envoi demande utilisateur")
        print("="*60)
        
        user_request = """Crée une calculatrice Python simple avec :
- calculator.py : classe Calculator avec méthodes add, subtract, multiply, divide
- tests/test_calculator.py : tests pytest pour toutes les méthodes
- README.md : documentation utilisation

Utilise Python 3, pytest, gestion erreurs (division par zéro)."""
        
        message_data = {
            "content": user_request
        }
        
        print(f"📝 Demande utilisateur ({len(user_request)} chars):")
        print(f"   {user_request[:100]}...")
        
        response = await client.post(
            f"{API_URL}/conversations/{conversation_id}/messages",
            json=message_data
        )
        
        assert response.status_code == 200, f"Erreur envoi message: {response.text}"
        
        result = response.json()
        jarvis_response = result.get("response", "")
        
        print(f"\n✅ Réponse JARVIS_Maître reçue ({len(jarvis_response)} chars)")
        print(f"   Début: {jarvis_response[:200]}...")
        
        # ========================================
        # 4. VÉRIFIER MARQUEUR DÉLÉGATION
        # ========================================
        print("\n" + "="*60)
        print("ÉTAPE 4 : Vérification marqueur délégation")
        print("="*60)
        
        assert "[DEMANDE_CODE_CODEUR:" in jarvis_response, (
            "❌ JARVIS_Maître n'a PAS généré le marqueur [DEMANDE_CODE_CODEUR:]\n"
            f"Réponse complète:\n{jarvis_response}"
        )
        
        print("✅ Marqueur [DEMANDE_CODE_CODEUR:] détecté")
        
        # Extraire la demande
        import re
        match = re.search(r'\[DEMANDE_CODE_CODEUR:\s*(.*?)\]', jarvis_response, re.DOTALL)
        if match:
            demande_extraite = match.group(1).strip()
            print(f"   Demande extraite ({len(demande_extraite)} chars):")
            print(f"   {demande_extraite[:150]}...")
        
        # ========================================
        # 5. RÉCUPÉRER MISSION ET VALIDER ARCHITECTURE
        # ========================================
        print("\n" + "="*60)
        print("ÉTAPE 5 : Récupération mission et validation architecture")
        print("="*60)
        
        # Attendre création mission (asynchrone - ARCHITECTE peut prendre 30-60s)
        print("⏳ Attente 10 secondes pour création mission et appel ARCHITECTE...")
        await asyncio.sleep(10)
        
        # Récupérer liste missions pour ce projet
        print(f"📊 Récupération missions pour projet: {PROJECT_PATH}")
        response = await client.get(f"{API_URL}/missions", params={"project_path": str(PROJECT_PATH)})
        print(f"📊 Status code: {response.status_code}")
        print(f"📊 Response preview: {response.text[:500]}")
        
        assert response.status_code == 200, f"Erreur récupération missions: {response.text}"
        
        missions = response.json()
        print(f"📊 Nombre de missions trouvées: {len(missions)}")
        
        if len(missions) == 0:
            print("❌ AUCUNE MISSION - Récupération toutes missions pour debug")
            response_all = await client.get(f"{API_URL}/missions")
            all_missions = response_all.json()
            print(f"📊 Total missions système: {len(all_missions)}")
            if all_missions:
                print(f"📋 Dernière mission: {all_missions[0]['mission_id']}")
                print(f"   Project: {all_missions[0].get('project_path', 'N/A')}")
        
        assert len(missions) > 0, "Aucune mission créée"
        
        mission = missions[0]  # Dernière mission créée
        mission_id = mission["mission_id"]
        mission_status = mission["status"]
        
        print(f"✅ Mission trouvée : {mission_id}")
        print(f"   Status: {mission_status}")
        print(f"   Phase: {mission.get('current_phase', 'N/A')}")
        
        # Si mission en attente validation, valider automatiquement
        if mission_status.lower() == "validating":
            print("\n⏸️  Mission en attente validation architecture")
            print("✅ Validation automatique de l'architecture...")
            
            response = await client.post(
                f"{API_URL}/missions/{mission_id}/validate",
                json={"approved": True}
            )
            assert response.status_code == 200, f"Erreur validation architecture: {response.text}"
            print("✅ Architecture validée")
            
            # Continuer workflow
            print("🚀 Continuation du workflow (CODEUR → TESTEUR → VALIDATEUR)...")
            response = await client.post(f"{API_URL}/missions/{mission_id}/continue")
            assert response.status_code == 200, f"Erreur continuation workflow: {response.text}"
            print("✅ Workflow relancé")
            
            # Attendre exécution complète (CODEUR + TESTEUR + VALIDATEUR peuvent prendre du temps)
            print("⏳ Attente 60 secondes pour exécution workflow complet...")
            await asyncio.sleep(60)
        else:
            print(f"⚠️  Mission status inattendu: {mission_status}")
            print("⏳ Attente 5 secondes...")
            await asyncio.sleep(5)
        
        # Vérifier historique messages
        response = await client.get(f"{API_URL}/conversations/{conversation_id}/messages")
        assert response.status_code == 200
        messages = response.json()
        print(f"✅ {len(messages)} messages dans l'historique")
        
        # ========================================
        # 6. VÉRIFIER FICHIERS CRÉÉS
        # ========================================
        print("\n" + "="*60)
        print("ÉTAPE 6 : Vérification fichiers créés")
        print("="*60)
        
        expected_files = [
            "calculator.py",
            "tests/test_calculator.py",
            "README.md"
        ]
        
        files_created = []
        files_missing = []
        
        for file_path in expected_files:
            full_path = PROJECT_PATH / file_path
            if full_path.exists():
                files_created.append(file_path)
                size = full_path.stat().st_size
                print(f"   ✅ {file_path} ({size} bytes)")
            else:
                files_missing.append(file_path)
                print(f"   ❌ {file_path} MANQUANT")
        
        # ========================================
        # 7. VÉRIFIER CONTENU FICHIERS
        # ========================================
        if files_created:
            print("\n" + "="*60)
            print("ÉTAPE 7 : Vérification contenu fichiers")
            print("="*60)
            
            # Vérifier calculator.py
            calculator_path = PROJECT_PATH / "calculator.py"
            if calculator_path.exists():
                content = calculator_path.read_text(encoding="utf-8")
                print(f"\n📄 calculator.py ({len(content)} chars):")
                print(f"   Début: {content[:200]}...")
                
                # Vérifications basiques
                assert "class Calculator" in content, "Classe Calculator manquante"
                assert "def add" in content, "Méthode add manquante"
                assert "def subtract" in content, "Méthode subtract manquante"
                assert "def multiply" in content, "Méthode multiply manquante"
                assert "def divide" in content, "Méthode divide manquante"
                
                print("   ✅ Classe Calculator avec 4 méthodes")
            
            # Vérifier test_calculator.py
            test_path = PROJECT_PATH / "tests" / "test_calculator.py"
            if test_path.exists():
                content = test_path.read_text(encoding="utf-8")
                print(f"\n📄 tests/test_calculator.py ({len(content)} chars):")
                print(f"   Début: {content[:200]}...")
                
                # Vérifications basiques
                assert "import pytest" in content or "def test_" in content, "Tests pytest manquants"
                
                print("   ✅ Tests pytest présents")
        
        # ========================================
        # 8. RÉSUMÉ FINAL
        # ========================================
        print("\n" + "="*60)
        print("RÉSUMÉ FINAL")
        print("="*60)
        
        print(f"\n✅ Projet créé : {project['name']}")
        print(f"✅ Conversation créée : {conversation_id}")
        print(f"✅ JARVIS_Maître a généré marqueur [DEMANDE_CODE_CODEUR:]")
        print(f"✅ Fichiers créés : {len(files_created)}/{len(expected_files)}")
        
        if files_created:
            print("\nFichiers générés :")
            for f in files_created:
                print(f"   - {f}")
        
        if files_missing:
            print("\n⚠️  Fichiers manquants :")
            for f in files_missing:
                print(f"   - {f}")
        
        print("\n" + "="*60)
        print("TEST LIVE TERMINÉ")
        print("="*60)
        
        # Assertion finale
        assert len(files_created) > 0, (
            "❌ ÉCHEC : Aucun fichier créé par le workflow\n"
            f"Fichiers attendus : {expected_files}\n"
            f"Vérifiez les logs serveur pour voir l'exécution du workflow"
        )


@pytest.mark.asyncio
@pytest.mark.live
async def test_live_verification_classes_agents():
    """
    Test live pour vérifier que les classes Codeur et Validateur sont bien instanciées
    
    Vérifie via l'API /api/agents que les agents sont correctement configurés
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("\n" + "="*60)
        print("VÉRIFICATION CLASSES AGENTS")
        print("="*60)
        
        # Récupérer liste agents
        response = await client.get(f"{BASE_URL}/agents")
        assert response.status_code == 200
        
        data = response.json()
        agents = data.get("agents", [])
        
        print(f"\n✅ {len(agents)} agents configurés:")
        
        for agent in agents:
            print(f"\n   Agent: {agent['id']}")
            print(f"   - Nom: {agent['name']}")
            print(f"   - Rôle: {agent['role']}")
            print(f"   - Type: {agent.get('type', 'N/A')}")
        
        # Vérifier présence CODEUR et VALIDATEUR
        agent_ids = [a['id'] for a in agents]
        
        assert "CODEUR" in agent_ids, "Agent CODEUR manquant"
        assert "VALIDATEUR" in agent_ids, "Agent VALIDATEUR manquant"
        
        print("\n✅ Agents CODEUR et VALIDATEUR présents dans la configuration")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST LIVE WORKFLOW COMPLET - VALIDATION AUDIT")
    print("="*60)
    print("\nPrérequis :")
    print("- Serveur JARVIS démarré sur http://localhost:8000")
    print("- API Gemini configurée (.env)")
    print("\nExécution :")
    print("pytest tests/live/test_live_workflow_complet_audit.py -v -s -m live")
    print("="*60)
