import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_connection


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM reflexion_messages")
    cursor.execute("DELETE FROM mission_prompts")
    cursor.execute("DELETE FROM reflexion_sessions")
    cursor.execute("DELETE FROM projects WHERE name LIKE 'Test%'")
    
    cursor.execute("""
        INSERT INTO projects (name, path, type, created_at)
        VALUES ('Test Integration', 'c:/test', 'dev', datetime('now'))
    """)
    project_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    yield project_id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reflexion_messages")
    cursor.execute("DELETE FROM mission_prompts")
    cursor.execute("DELETE FROM reflexion_sessions")
    cursor.execute("DELETE FROM projects WHERE name LIKE 'Test%'")
    conn.commit()
    conn.close()


def test_full_flow_mission_code(setup_test_db):
    project_id = setup_test_db
    
    response = client.post('/api/reflexions', json={
        'project_id': project_id,
        'livrable_type': 'mission_code'
    })
    assert response.status_code == 201
    session = response.json()
    session_id = session['id']
    assert session['statut'] == 'OUVERTE'
    assert session['livrable_type'] == 'mission_code'
    
    response = client.get(f'/api/reflexions/{session_id}')
    assert response.status_code == 200
    session_detail = response.json()
    assert session_detail['id'] == session_id
    
    response = client.get(f'/api/reflexions/{session_id}/livrable')
    assert response.status_code == 404
    
    response = client.get(f'/api/reflexions?project_id={project_id}')
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) >= 1
    assert any(s['id'] == session_id for s in sessions)


def test_abandon_session(setup_test_db):
    project_id = setup_test_db
    
    response = client.post('/api/reflexions', json={
        'project_id': project_id,
        'livrable_type': 'decision_figee'
    })
    assert response.status_code == 201
    session_id = response.json()['id']
    
    response = client.post(f'/api/reflexions/{session_id}/abandon')
    assert response.status_code == 200
    
    response = client.get(f'/api/reflexions/{session_id}')
    assert response.status_code == 200
    session = response.json()
    assert session['statut'] == 'ABANDONNEE'


def test_delete_session(setup_test_db):
    project_id = setup_test_db
    
    response = client.post('/api/reflexions', json={
        'project_id': project_id,
        'livrable_type': 'plan_multi_missions'
    })
    assert response.status_code == 201
    session_id = response.json()['id']
    
    response = client.delete(f'/api/reflexions/{session_id}')
    assert response.status_code == 204
    
    response = client.get(f'/api/reflexions/{session_id}')
    assert response.status_code == 404


def test_sante_cadrage(setup_test_db):
    project_id = setup_test_db
    
    response = client.post('/api/reflexions', json={
        'project_id': project_id,
        'livrable_type': 'mission_code'
    })
    assert response.status_code == 201
    session_id = response.json()['id']
    
    response = client.post(f'/api/reflexions/{session_id}/sante-cadrage')
    assert response.status_code == 200
    health = response.json()
    assert 'verdict_global' in health
    assert 'checks' in health
    assert health['verdict_global'] in ['vert', 'orange', 'rouge']
