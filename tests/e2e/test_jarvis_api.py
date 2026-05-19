"""
Tests E2E API JARVIS — Sans navigateur, sans LLM.
Scénarios 4 et 5 : CRUD conversations + sauvegarde config.
"""
import pytest
import httpx


def test_scenario_4_crud_conversations(api_client: httpx.Client):
    """
    SCÉNARIO 4 — CRUD conversations via API REST.
    
    1. POST /api/jarvis/conversations → 201
    2. GET /api/jarvis/conversations → liste contient la conversation
    3. GET /api/jarvis/conversations/{id} → 200, messages vide
    4. DELETE /api/jarvis/conversations/{id} → 204
    5. GET /api/jarvis/conversations/{id} → 404
    """
    # 1. Créer une conversation
    response = api_client.post("/api/jarvis/conversations", json={"title": "Test E2E"})
    assert response.status_code == 201, f"POST failed: {response.text}"
    
    body = response.json()
    assert "id" in body, "Response body missing 'id'"
    assert body["title"] == "Test E2E", f"Title mismatch: {body['title']}"
    
    conv_id = body["id"]
    
    # 2. Lister les conversations
    response = api_client.get("/api/jarvis/conversations")
    assert response.status_code == 200, f"GET list failed: {response.text}"
    
    conversations = response.json()
    assert isinstance(conversations, list), "Response is not a list"
    assert any(c["id"] == conv_id for c in conversations), f"Conversation {conv_id} not in list"
    
    # 3. Récupérer la conversation par ID
    response = api_client.get(f"/api/jarvis/conversations/{conv_id}")
    assert response.status_code == 200, f"GET by ID failed: {response.text}"
    
    conv = response.json()
    assert conv["id"] == conv_id, f"ID mismatch: {conv['id']}"
    assert "messages" in conv, "Response missing 'messages'"
    assert isinstance(conv["messages"], list), "messages is not a list"
    assert len(conv["messages"]) == 0, f"Expected empty messages, got {len(conv['messages'])}"
    
    # 4. Supprimer la conversation
    response = api_client.delete(f"/api/jarvis/conversations/{conv_id}")
    assert response.status_code == 204, f"DELETE failed: {response.status_code} {response.text}"
    
    # 5. Vérifier que la conversation n'existe plus
    response = api_client.get(f"/api/jarvis/conversations/{conv_id}")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


def test_scenario_5_save_api_key(api_client: httpx.Client, cleanup_test_config):
    """
    SCÉNARIO 5 — Paramètres : sauvegarde clé API.
    
    1. POST /api/config avec une clé de test
    2. Vérifier réponse 200 (pas 500 — bug corrigé)
    3. GET /api/config pour vérifier persistance
    """
    # 1. Sauvegarder une clé API de test
    payload = {
        "api_keys": {
            "openrouter_key": "test-key-e2e-12345"
        },
        "model_preferences": {
            "routing": "google/gemini-2.5-flash",
            "structuring": "google/gemini-2.5-flash",
            "code": "anthropic/claude-haiku-4.5",
            "analysis": "anthropic/claude-sonnet-4.5"
        },
        "chat": None
    }
    
    response = api_client.post("/api/config", json=payload)
    assert response.status_code == 200, f"POST /api/config failed: {response.status_code} {response.text}"
    
    body = response.json()
    assert "message" in body, "Response missing 'message'"
    
    # 3. Vérifier que la clé est bien persistée
    response = api_client.get("/api/config")
    assert response.status_code == 200, f"GET /api/config failed: {response.text}"
    
    config = response.json()
    assert "api_keys" in config, "Response missing 'api_keys'"
    assert "openrouter_key" in config["api_keys"], "openrouter_key not in api_keys"
    
    # La clé est masquée dans la réponse (seulement les 4 derniers caractères)
    saved_key = config["api_keys"]["openrouter_key"]
    assert saved_key.endswith("2345"), f"Key not saved correctly: {saved_key}"


def test_api_health_check(api_client: httpx.Client):
    """
    Test de santé basique : vérifier que le serveur répond.
    """
    response = api_client.get("/api/jarvis/conversations")
    assert response.status_code == 200, f"Server not responding: {response.status_code}"
