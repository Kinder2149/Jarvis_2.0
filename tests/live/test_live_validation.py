"""
Tests live de validation JARVIS — Appels API réels
Nécessite serveur actif sur http://localhost:8000 + clé OpenRouter configurée
"""
import pytest
import httpx
import time


BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


@pytest.mark.live
def test_connexion_openrouter():
    """TEST 1 — Vérifier que la connexion OpenRouter fonctionne"""
    response = httpx.post(
        f"{BASE_URL}/api/config/test",
        json={"provider": "openrouter"},
        timeout=TIMEOUT
    )
    
    assert response.status_code == 200, f"Status code: {response.status_code}, Body: {response.text}"
    data = response.json()
    assert data.get("status") == "success", f"Connexion OpenRouter échouée: {data}"
    print(f"✅ Connexion OpenRouter validée: {data.get('message', 'OK')}")


@pytest.mark.live
def test_chat_message_reel():
    """TEST 2 — Créer conversation + envoyer message réel + vérifier réponse IA"""
    client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)
    
    # Créer conversation
    conv_response = client.post("/api/chat/conversations", json={"title": "Test live"})
    assert conv_response.status_code == 200
    conv = conv_response.json()
    conv_id = conv["id"]
    print(f"✅ Conversation créée: id={conv_id}")
    
    try:
        # Envoyer message
        msg_response = client.post(
            f"/api/chat/conversations/{conv_id}/messages",
            json={"content": "Réponds uniquement : OK"}
        )
        assert msg_response.status_code == 200
        msg_data = msg_response.json()
        
        # Vérifier réponse assistant
        assert "assistant_message" in msg_data, "Pas de champ 'assistant_message' dans la réponse"
        assistant_msg = msg_data["assistant_message"]
        assert "content" in assistant_msg, "Pas de champ 'content' dans assistant_message"
        assert assistant_msg["content"], "Réponse vide"
        assert assistant_msg.get("role") == "assistant", f"Role attendu: assistant, reçu: {assistant_msg.get('role')}"
        
        response_preview = assistant_msg["content"][:100]
        print(f"✅ Réponse IA reçue: {response_preview}")
        
    finally:
        # Nettoyer
        client.delete(f"/api/chat/conversations/{conv_id}")
        print(f"✅ Conversation supprimée: id={conv_id}")
        client.close()


@pytest.mark.live
def test_pipeline_session_start_reel():
    """TEST 3 — Démarrer pipeline session_start réel + vérifier statut + aborter"""
    client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)
    
    # Récupérer premier projet
    projects_response = client.get("/api/projects")
    assert projects_response.status_code == 200
    projects = projects_response.json()
    
    project_created = False
    if not projects:
        # Créer projet de test
        project_response = client.post("/api/projects", json={
            "name": "Test live",
            "path": "C:\\Temp",
            "type": "Test"
        })
        assert project_response.status_code == 200
        project = project_response.json()
        project_created = True
        print(f"✅ Projet de test créé: id={project['id']}")
    else:
        project = projects[0]
        print(f"✅ Utilisation projet existant: id={project['id']}, name={project['name']}")
    
    project_id = project["id"]
    
    try:
        # Démarrer pipeline
        pipeline_response = client.post("/api/pipelines/start", json={
            "project_id": project_id,
            "workflow_type": "session_start",
            "initial_input": "Test de validation live"
        })
        assert pipeline_response.status_code == 200
        pipeline_data = pipeline_response.json()
        
        session = pipeline_data.get("session", {})
        session_id = session.get("id")
        status = session.get("status")
        
        assert session_id, "Pas de session_id dans la réponse"
        assert status in ["WAITING_VALIDATION", "COMPLETED", "RUNNING", "IN_PROGRESS"], \
            f"Statut inattendu: {status}"
        
        print(f"✅ Pipeline démarré: session_id={session_id}, status={status}")
        
        # Attendre un peu pour que le pipeline démarre
        time.sleep(2)
        
        # Récupérer statut détaillé
        status_response = client.get(f"/api/pipelines/{session_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            current_step = status_data.get("current_step", {})
            step_name = current_step.get("name", "N/A")
            print(f"✅ Étape courante: {step_name}")
        
        # Aborter le pipeline
        abort_response = client.post(f"/api/pipelines/{session_id}/abort")
        assert abort_response.status_code == 200
        print(f"✅ Pipeline aborté: session_id={session_id}")
        
    finally:
        # Nettoyer projet si créé pour le test
        if project_created:
            client.delete(f"/api/projects/{project_id}")
            print(f"✅ Projet de test supprimé: id={project_id}")
        client.close()


@pytest.mark.live
def test_lecture_dossier_local():
    """TEST 4 — Créer conversation avec folder_path + lire fichier réel"""
    client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)
    
    # Créer conversation avec folder_path
    conv_response = client.post("/api/chat/conversations", json={
        "title": "Test lecture locale",
        "folder_path": "C:\\DEV\\PROJETS\\intelligence_artificielle\\Jarvis-2.0"
    })
    assert conv_response.status_code == 200
    conv = conv_response.json()
    conv_id = conv["id"]
    print(f"✅ Conversation créée avec folder_path: id={conv_id}")
    
    try:
        # Demander lecture du fichier
        msg_response = client.post(
            f"/api/chat/conversations/{conv_id}/messages",
            json={"content": "lis PROJET_CONTEXTE.md"}
        )
        assert msg_response.status_code == 200
        msg_data = msg_response.json()
        
        # Vérifier que la réponse contient "JARVIS" (preuve de lecture)
        assert "assistant_message" in msg_data, "Pas de champ 'assistant_message' dans la réponse"
        content = msg_data["assistant_message"].get("content", "")
        assert "JARVIS" in content, f"Le fichier PROJET_CONTEXTE.md n'a pas été lu correctement. Réponse: {content[:200]}"
        
        print(f"✅ Fichier PROJET_CONTEXTE.md lu avec succès (contient 'JARVIS')")
        
    finally:
        # Nettoyer
        client.delete(f"/api/chat/conversations/{conv_id}")
        print(f"✅ Conversation supprimée: id={conv_id}")
        client.close()
