"""
Test simple pour vérifier l'état de la mission après création.
"""

import pytest
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
PROJECT_NAME = f"test_mission_status_{timestamp}"
PROJECT_PATH = Path(__file__).parent.parent.parent / "projects" / PROJECT_NAME

# Nettoyer projet test si existe
if PROJECT_PATH.exists():
    import shutil
    shutil.rmtree(PROJECT_PATH)

# Créer dossier projet
PROJECT_PATH.mkdir(parents=True, exist_ok=True)


@pytest.mark.asyncio
@pytest.mark.live
async def test_mission_status_after_creation():
    """
    Test simple : Vérifier que la mission est créée et récupérable via API.
    
    Note: Timeout 180s (3min) car Gemini API max 5min selon documentation officielle
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        
        # 1. CRÉER PROJET
        print("\n" + "="*60)
        print("ÉTAPE 1 : Création projet")
        print("="*60)
        
        project_data = {
            "name": PROJECT_NAME,
            "path": str(PROJECT_PATH),
            "description": "Test mission status"
        }
        
        response = await client.post(f"{API_URL}/projects", json=project_data)
        assert response.status_code == 200, f"Erreur création projet: {response.text}"
        
        project = response.json()
        project_id = project["id"]
        print(f"✅ Projet créé : {project['name']}")
        print(f"   ID: {project_id}")
        
        # 2. CRÉER CONVERSATION
        print("\n" + "="*60)
        print("ÉTAPE 2 : Création conversation")
        print("="*60)
        
        conversation_data = {
            "agent_id": "JARVIS_Maître"
        }
        
        response = await client.post(
            f"{API_URL}/projects/{project_id}/conversations",
            json=conversation_data
        )
        assert response.status_code == 200, f"Erreur création conversation: {response.text}"
        
        conversation = response.json()
        conversation_id = conversation["id"]
        print(f"✅ Conversation créée : {conversation_id}")
        
        # 3. ENVOYER DEMANDE
        print("\n" + "="*60)
        print("ÉTAPE 3 : Envoi demande utilisateur")
        print("="*60)
        
        user_request = "Crée une calculatrice Python simple avec calculator.py"
        
        message_data = {
            "content": user_request,
            "role": "user"
        }
        
        response = await client.post(
            f"{API_URL}/conversations/{conversation_id}/messages",
            json=message_data
        )
        assert response.status_code == 200, f"Erreur envoi message: {response.text}"
        print(f"✅ Message envoyé")
        
        # 4. ATTENDRE ET RÉCUPÉRER MISSION
        print("\n" + "="*60)
        print("ÉTAPE 4 : Récupération mission")
        print("="*60)
        
        print("⏳ Attente 5 secondes pour création mission...")
        await asyncio.sleep(5)
        
        # Récupérer missions pour ce projet
        response = await client.get(f"{API_URL}/missions", params={"project_path": str(PROJECT_PATH)})
        print(f"📊 Status code: {response.status_code}")
        print(f"📊 Response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Erreur récupération missions: {response.text}"
        
        missions = response.json()
        print(f"📊 Nombre de missions: {len(missions)}")
        
        if len(missions) == 0:
            print("❌ AUCUNE MISSION CRÉÉE")
            print("\n🔍 Vérification alternative : Récupérer toutes les missions")
            response = await client.get(f"{API_URL}/missions")
            all_missions = response.json()
            print(f"📊 Total missions dans le système: {len(all_missions)}")
            if all_missions:
                print("\n📋 Dernière mission:")
                last_mission = all_missions[0]
                for key, value in last_mission.items():
                    print(f"   {key}: {value}")
            assert False, "Aucune mission créée pour ce projet"
        
        mission = missions[0]
        mission_id = mission['mission_id']
        mission_status = mission['status']
        
        print(f"\n✅ Mission trouvée : {mission_id}")
        print(f"   Status: {mission_status}")
        print(f"   Phase: {mission.get('current_phase', 'N/A')}")
        print(f"   Project path: {mission.get('project_path', 'N/A')}")
        
        # Afficher tous les champs de la mission
        print("\n📋 Détails complets mission:")
        for key, value in mission.items():
            print(f"   {key}: {value}")
        
        # Si mission en attente validation, valider automatiquement
        if mission_status == "validating":
            print("\n⏸️  Mission en attente validation architecture")
            print("✅ Validation automatique de l'architecture...")
            
            response = await client.post(
                f"{API_URL}/missions/{mission_id}/validate",
                json={"approved": True}
            )
            assert response.status_code == 200, f"Erreur validation: {response.text}"
            print("✅ Architecture validée")
            
            # Continuer workflow
            print("🚀 Continuation du workflow...")
            response = await client.post(f"{API_URL}/missions/{mission_id}/continue")
            assert response.status_code == 200, f"Erreur continuation: {response.text}"
            print("✅ Workflow relancé")
            
            # Attendre exécution
            print("⏳ Attente 30 secondes pour workflow complet...")
            await asyncio.sleep(30)
            
            # Vérifier fichiers créés
            print("\n📁 Vérification fichiers créés:")
            calculator_file = PROJECT_PATH / "calculator.py"
            if calculator_file.exists():
                print(f"   ✅ calculator.py créé ({calculator_file.stat().st_size} bytes)")
            else:
                print(f"   ⚠️  calculator.py non créé")
        
        print("\n✅ TEST RÉUSSI : Mission créée et récupérable")
