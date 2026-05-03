import pytest
from backend.database import get_connection
from backend.services import reflexion_service


@pytest.mark.live
def test_live_mission_code():
    """
    Test live avec clé API réelle pour mission_code.
    Vérifie que le livrable généré est parseable et au bon format.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM projects LIMIT 1")
    project_row = cursor.fetchone()
    if not project_row:
        pytest.skip("Aucun projet disponible pour le test live")
    
    project_id = project_row['id']
    
    try:
        session = reflexion_service.create_session(
            project_id=project_id,
            livrable_type='mission_code',
            db_conn=conn
        )
        session_id = session['id']
        
        import asyncio
        
        messages = asyncio.run(reflexion_service.send_user_message(
            session_id=session_id,
            content="Je veux ajouter un bouton de test dans la page d'accueil",
            db_conn=conn
        ))
        
        assert len(messages) >= 2
        assert any(msg['role'] == 'assistant' for msg in messages)
        
        livrable = asyncio.run(reflexion_service.freeze_session(session_id, conn))
        
        assert livrable is not None
        assert livrable['livrable_type'] == 'mission_code'
        assert '# MISSION CODE' in livrable['content']
        assert '## Objectif' in livrable['content']
        assert '## Fichiers concernés' in livrable['content']
        assert '## Critères de réussite' in livrable['content']
        assert livrable['recommandation_modele'] in [
            'anthropic/claude-haiku-4.5',
            'google/gemini-2.5-pro',
            'anthropic/claude-sonnet-4.5'
        ]
        
        cursor.execute("SELECT statut FROM reflexion_sessions WHERE id = ?", (session_id,))
        session_check = cursor.fetchone()
        assert session_check['statut'] == 'FIGEE'
        
    finally:
        if 'session_id' in locals():
            cursor.execute("DELETE FROM reflexion_messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM mission_prompts WHERE reflexion_session_id = ?", (session_id,))
            cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
            conn.commit()
        conn.close()


@pytest.mark.live
def test_live_decision_figee():
    """
    Test live avec clé API réelle pour decision_figee.
    Vérifie que le format ligne tableau est respecté.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM projects LIMIT 1")
    project_row = cursor.fetchone()
    if not project_row:
        pytest.skip("Aucun projet disponible pour le test live")
    
    project_id = project_row['id']
    
    try:
        session = reflexion_service.create_session(
            project_id=project_id,
            livrable_type='decision_figee',
            db_conn=conn
        )
        session_id = session['id']
        
        import asyncio
        
        messages = asyncio.run(reflexion_service.send_user_message(
            session_id=session_id,
            content="Nous décidons d'utiliser TypeScript pour tous les nouveaux modules frontend",
            db_conn=conn
        ))
        
        assert len(messages) >= 2
        
        livrable = asyncio.run(reflexion_service.freeze_session(session_id, conn))
        
        assert livrable is not None
        assert livrable['livrable_type'] == 'decision_figee'
        assert '|' in livrable['content']
        
        lines = [line.strip() for line in livrable['content'].split('\n') if line.strip()]
        assert any('|' in line and line.count('|') >= 3 for line in lines)
        
    finally:
        if 'session_id' in locals():
            cursor.execute("DELETE FROM reflexion_messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM mission_prompts WHERE reflexion_session_id = ?", (session_id,))
            cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
            conn.commit()
        conn.close()


@pytest.mark.live
def test_live_plan_multi_missions():
    """
    Test live avec clé API réelle pour plan_multi_missions.
    Vérifie qu'au moins 2 missions sont générées.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM projects LIMIT 1")
    project_row = cursor.fetchone()
    if not project_row:
        pytest.skip("Aucun projet disponible pour le test live")
    
    project_id = project_row['id']
    
    try:
        session = reflexion_service.create_session(
            project_id=project_id,
            livrable_type='plan_multi_missions',
            db_conn=conn
        )
        session_id = session['id']
        
        import asyncio
        
        messages = asyncio.run(reflexion_service.send_user_message(
            session_id=session_id,
            content="Je veux refondre complètement le Module Chat : nouvelle UI, optimisation backend, et ajout de fonctionnalités avancées",
            db_conn=conn
        ))
        
        assert len(messages) >= 2
        
        livrable = asyncio.run(reflexion_service.freeze_session(session_id, conn))
        
        assert livrable is not None
        assert livrable['livrable_type'] == 'plan_multi_missions'
        assert '# PLAN' in livrable['content']
        assert '## Vision globale' in livrable['content']
        assert '## Missions' in livrable['content']
        
        mission_count = livrable['content'].count('### Mission')
        assert mission_count >= 2, f"Attendu au moins 2 missions, trouvé {mission_count}"
        
    finally:
        if 'session_id' in locals():
            cursor.execute("DELETE FROM reflexion_messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM mission_prompts WHERE reflexion_session_id = ?", (session_id,))
            cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
            conn.commit()
        conn.close()
