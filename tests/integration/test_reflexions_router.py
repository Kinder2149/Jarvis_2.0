import pytest
from fastapi.testclient import TestClient
import sqlite3
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, patch

from backend.main import app
from backend.database import DB_PATH, get_connection


@pytest.fixture
def client_with_project(tmp_path):
    """Client de test avec un projet créé."""
    # Créer un dossier temporaire pour le projet
    project_folder = tmp_path / "test_reflexion_project"
    project_folder.mkdir()
    
    # Utiliser la vraie BDD de test
    conn = get_connection()
    cursor = conn.cursor()
    
    # Créer un projet de test avec folder_path (anciennement path)
    # Vérifier quelle colonne existe
    cursor.execute("PRAGMA table_info(projects)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'folder_path' in columns:
        cursor.execute("""
            INSERT INTO projects (name, folder_path, type, module_type)
            VALUES ('Test Reflexion', ?, 'code', 'code')
        """, (str(project_folder),))
    else:
        cursor.execute("""
            INSERT INTO projects (name, path, type, module_type)
            VALUES ('Test Reflexion', ?, 'code', 'code')
        """, (str(project_folder),))
    
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    
    client = TestClient(app)
    
    yield client, project_id
    
    # Cleanup
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


def test_create_reflexion(client_with_project):
    """Test création d'une session de réflexion."""
    client, project_id = client_with_project
    
    response = client.post("/api/reflexions", json={
        "project_id": project_id,
        "livrable_type": "mission_code"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == project_id
    assert data["livrable_type"] == "mission_code"
    assert data["statut"] == "OUVERTE"
    
    session_id = data["id"]
    
    # Cleanup
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def test_create_reflexion_projet_inexistant():
    """Test création avec projet inexistant."""
    client = TestClient(app)
    
    response = client.post("/api/reflexions", json={
        "project_id": 99999,
        "livrable_type": "mission_code"
    })
    
    assert response.status_code == 404


def test_get_reflexion(client_with_project):
    """Test récupération d'une session."""
    client, project_id = client_with_project
    
    # Créer session
    response = client.post("/api/reflexions", json={
        "project_id": project_id,
        "livrable_type": "decision_figee"
    })
    session_id = response.json()["id"]
    
    # Récupérer session
    response = client.get(f"/api/reflexions/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert "messages" in data
    
    # Cleanup
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def test_send_message_with_stub(client_with_project):
    """Test envoi message avec stub R01."""
    client, project_id = client_with_project
    
    # Créer session
    response = client.post("/api/reflexions", json={
        "project_id": project_id,
        "livrable_type": "mission_code"
    })
    session_id = response.json()["id"]
    
    # Envoyer message avec mock LLM
    with patch('backend.services.model_router.call_model', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "STUB R01 — Réponse de test"
        response = client.post(f"/api/reflexions/{session_id}/messages", json={
            "content": "Test message"
        })
    
    assert response.status_code == 201
    messages = response.json()
    assert len(messages) == 2  # user + assistant stub
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test message"
    assert messages[1]["role"] == "assistant"
    assert "STUB R01" in messages[1]["content"]
    
    # Cleanup
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def test_delete_session_ouverte(client_with_project):
    """Test suppression session OUVERTE."""
    client, project_id = client_with_project
    
    # Créer session
    response = client.post("/api/reflexions", json={
        "project_id": project_id,
        "livrable_type": "mission_code"
    })
    session_id = response.json()["id"]
    
    # Supprimer
    response = client.delete(f"/api/reflexions/{session_id}")
    
    assert response.status_code == 204
    
    # Vérifier suppression
    response = client.get(f"/api/reflexions/{session_id}")
    assert response.status_code == 404


def test_abandon_session(client_with_project):
    """Test abandon d'une session."""
    client, project_id = client_with_project
    
    # Créer session
    response = client.post("/api/reflexions", json={
        "project_id": project_id,
        "livrable_type": "plan_multi_missions"
    })
    session_id = response.json()["id"]
    
    # Abandonner
    response = client.post(f"/api/reflexions/{session_id}/abandon")
    
    assert response.status_code == 200
    data = response.json()
    assert data["statut"] == "ABANDONNEE"
    
    # Cleanup
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def test_proposer_edit_fichier_non_autorise(client_with_project):
    """Test proposition d'édition sur fichier non autorisé."""
    client, project_id = client_with_project
    
    # Créer session
    response = client.post("/api/reflexions", json={
        "project_id": project_id,
        "livrable_type": "mission_code"
    })
    session_id = response.json()["id"]
    
    # Proposer édition fichier .py (interdit)
    response = client.post(f"/api/reflexions/{session_id}/proposer-edit", json={
        "file_path": "test.py",
        "new_content": "print('test')"
    })
    
    assert response.status_code == 403
    
    # Cleanup
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
