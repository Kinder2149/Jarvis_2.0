import pytest
import sqlite3
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.services import reflexion_service
from backend.schemas.reflexion import ReflexionStatut


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name TEXT,
            path TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE reflexion_sessions (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            livrable_type TEXT,
            titre TEXT,
            statut TEXT,
            modele_utilise TEXT DEFAULT 'anthropic/claude-sonnet-4.5',
            livrable_id INTEGER,
            frozen_at TEXT,
            input_tokens_total INTEGER DEFAULT 0,
            output_tokens_total INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE reflexion_messages (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            attachments TEXT,
            compacted INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE mission_prompts (
            id INTEGER PRIMARY KEY,
            reflexion_session_id INTEGER,
            livrable_type TEXT,
            content TEXT,
            recommandation_modele TEXT,
            files_targeted TEXT,
            created_at TEXT,
            consumed_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE app_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE model_decision_log (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            step_name TEXT,
            model_type TEXT,
            model_id_chosen TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER
        )
    """)
    
    conn.commit()
    
    cursor.execute("INSERT INTO projects (id, name, path) VALUES (1, 'Test', ?)", (str(tmp_path),))
    cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('prompts_json_path', 'backend/data/prompts.json')")
    cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('openrouter_key', 'test_key')")
    conn.commit()
    
    yield conn
    conn.close()


@pytest.mark.asyncio
async def test_freeze_session_mission_code(db_conn, tmp_path):
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (id, project_id, livrable_type, titre, statut, created_at, updated_at)
        VALUES (1, 1, 'mission_code', 'Test mission', 'OUVERTE', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    
    cursor.execute("""
        INSERT INTO reflexion_messages (session_id, role, content, created_at)
        VALUES (1, 'user', 'Je veux ajouter un bouton dark mode', ?)
    """, (datetime.now().isoformat(),))
    
    cursor.execute("""
        INSERT INTO reflexion_messages (session_id, role, content, created_at)
        VALUES (1, 'assistant', 'Très bien, je vais vous aider à cadrer cette mission.', ?)
    """, (datetime.now().isoformat(),))
    
    db_conn.commit()
    
    mock_livrable = """# MISSION CODE — Ajout bouton dark mode

## Objectif
Ajouter un bouton de basculement dark mode dans la page Paramètres.

## Contexte
Aucune décision figée pertinente.

## Fichiers concernés
- `frontend/parametres.html` — Ajout du bouton UI
- `frontend/assets/js/parametres.js` — Logique de basculement

## Contraintes
- Ne pas casser les tests existants

## Critères de réussite (test manuel en français)
1. Ouvrir la page Paramètres
2. Cliquer sur le bouton dark mode
3. Vérifier que le thème change

## Recommandation modèle
`anthropic/claude-haiku-4.5` — Mission simple, 2 fichiers
"""
    
    with patch('backend.services.model_router.call_model', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_livrable
        
        livrable = await reflexion_service.freeze_session(1, db_conn)
    
    assert livrable is not None
    assert livrable['livrable_type'] == 'mission_code'
    assert 'MISSION CODE' in livrable['content']
    assert livrable['recommandation_modele'] == 'anthropic/claude-haiku-4.5'
    
    cursor.execute("SELECT statut, livrable_id FROM reflexion_sessions WHERE id = 1")
    session = cursor.fetchone()
    assert session['statut'] == ReflexionStatut.FIGEE.value
    assert session['livrable_id'] == livrable['id']


@pytest.mark.asyncio
async def test_freeze_session_decision_figee(db_conn, tmp_path):
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (id, project_id, livrable_type, titre, statut, created_at, updated_at)
        VALUES (2, 1, 'decision_figee', 'Décision test', 'OUVERTE', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    
    db_conn.commit()
    
    mock_livrable = "| 2026-05-15 | Utiliser Claude Sonnet 4.5 pour le Module Réflexion | Performance et qualité de raisonnement supérieures |"
    
    with patch('backend.services.model_router.call_model', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_livrable
        
        livrable = await reflexion_service.freeze_session(2, db_conn)
    
    assert livrable is not None
    assert livrable['livrable_type'] == 'decision_figee'
    assert '2026-05-15' in livrable['content']


@pytest.mark.asyncio
async def test_freeze_session_plan_multi_missions(db_conn, tmp_path):
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (id, project_id, livrable_type, titre, statut, created_at, updated_at)
        VALUES (3, 1, 'plan_multi_missions', 'Plan test', 'OUVERTE', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    
    db_conn.commit()
    
    mock_livrable = """# PLAN — Refonte Module Chat

## Vision globale
Améliorer l'UX du Module Chat en 3 missions.

## Missions (ordre d'exécution)

### Mission 1 — UI améliorée
# MISSION CODE — UI améliorée

## Objectif
Améliorer l'interface du chat.

## Fichiers concernés
- `frontend/chat.html` — Mise à jour UI

## Critères de réussite (test manuel en français)
1. Ouvrir le chat
2. Vérifier la nouvelle UI

## Recommandation modèle
`anthropic/claude-haiku-4.5` — Simple

### Mission 2 — Backend optimisé
# MISSION CODE — Backend optimisé

## Objectif
Optimiser les requêtes backend.

## Fichiers concernés
- `backend/services/chat_service.py` — Optimisation

## Critères de réussite (test manuel en français)
1. Envoyer un message
2. Vérifier la rapidité

## Recommandation modèle
`anthropic/claude-haiku-4.5` — Simple
"""
    
    with patch('backend.services.model_router.call_model', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_livrable
        
        livrable = await reflexion_service.freeze_session(3, db_conn)
    
    assert livrable is not None
    assert livrable['livrable_type'] == 'plan_multi_missions'
    assert 'Mission 1' in livrable['content']
    assert 'Mission 2' in livrable['content']


@pytest.mark.asyncio
async def test_freeze_erreur_llm(db_conn, tmp_path):
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (id, project_id, livrable_type, titre, statut, created_at, updated_at)
        VALUES (4, 1, 'mission_code', 'Test erreur', 'OUVERTE', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    
    db_conn.commit()
    
    with patch('backend.services.model_router.call_model', new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = Exception("Erreur LLM test")
        
        with pytest.raises(Exception):
            await reflexion_service.freeze_session(4, db_conn)
    
    cursor.execute("SELECT statut FROM reflexion_sessions WHERE id = 4")
    session = cursor.fetchone()
    assert session['statut'] == ReflexionStatut.OUVERTE.value


def test_recommandation_modele_petite_mission(tmp_path):
    files = ['frontend/test.html', 'frontend/test.js']
    
    for f in files:
        file_path = tmp_path / f
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text('a' * 1000)
    
    model = reflexion_service.recommend_model(files, tmp_path)
    assert model == 'anthropic/claude-haiku-4.5'


def test_recommandation_modele_grosse_mission(tmp_path):
    files = ['backend/service1.py', 'backend/service2.py', 'backend/service3.py']
    
    for f in files:
        file_path = tmp_path / f
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text('a' * 50000)
    
    model = reflexion_service.recommend_model(files, tmp_path)
    assert model == 'google/gemini-2.5-pro'


def test_get_livrable(db_conn):
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (id, project_id, livrable_type, titre, statut, livrable_id, created_at, updated_at)
        VALUES (5, 1, 'mission_code', 'Test', 'FIGEE', 1, ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    
    cursor.execute("""
        INSERT INTO mission_prompts (id, reflexion_session_id, livrable_type, content, created_at)
        VALUES (1, 5, 'mission_code', 'Test content', ?)
    """, (datetime.now().isoformat(),))
    
    db_conn.commit()
    
    livrable = reflexion_service.get_livrable(5, db_conn)
    
    assert livrable is not None
    assert livrable['id'] == 1
    assert livrable['content'] == 'Test content'


def test_mark_consumed(db_conn):
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO mission_prompts (id, reflexion_session_id, livrable_type, content, created_at)
        VALUES (2, 1, 'mission_code', 'Test', ?)
    """, (datetime.now().isoformat(),))
    
    db_conn.commit()
    
    reflexion_service.mark_consumed(2, db_conn)
    
    cursor.execute("SELECT consumed_at FROM mission_prompts WHERE id = 2")
    row = cursor.fetchone()
    assert row['consumed_at'] is not None


@pytest.mark.asyncio
async def test_figer_returns_fichiers_modifies_and_writes_docs(db_conn, tmp_path):
    """Phase 4.1 — freeze_session mission_code retourne fichiers_modifies et écrit les docs."""
    cursor = db_conn.cursor()
    
    # Créer PROJET_CONTEXTE.md avec section 8
    pc_path = tmp_path / "PROJET_CONTEXTE.md"
    pc_path.write_text(
        "# PROJET_CONTEXTE\n\n## 8. SESSION EN COURS\n\nAncien contenu\n\n## 9. BACKLOG\n",
        encoding="utf-8"
    )
    
    # Créer CHANGELOG.md
    cl_path = tmp_path / "CHANGELOG.md"
    cl_path.write_text(
        "# CHANGELOG\n\n| Date | Mission | Description | Fichiers |\n|------|---------|-------------|----------|\n",
        encoding="utf-8"
    )
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (id, project_id, livrable_type, titre, statut, created_at, updated_at)
        VALUES (10, 1, 'mission_code', 'Mission test fichiers', 'OUVERTE', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    db_conn.commit()
    
    mock_livrable = """# MISSION CODE — Test

## Fichiers concernés
- `frontend/test.html`

## Recommandation modèle
`anthropic/claude-haiku-4.5` — Simple
"""
    
    with patch('backend.services.model_router.call_model', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_livrable
        livrable = await reflexion_service.freeze_session(10, db_conn)
    
    # Vérifier que fichiers_modifies est présent et correct
    assert 'fichiers_modifies' in livrable
    assert livrable['fichiers_modifies'] == ['PROJET_CONTEXTE.md', 'CHANGELOG.md']
    
    # Vérifier que PROJET_CONTEXTE.md contient la nouvelle section 8
    pc_content = pc_path.read_text(encoding="utf-8")
    assert '🔒 Mission cadrée — en attente d\'exécution' in pc_content
    assert 'Mission test fichiers' in pc_content
    
    # Vérifier que CHANGELOG.md contient la ligne CADRAGE
    cl_content = cl_path.read_text(encoding="utf-8")
    assert 'CADRAGE' in cl_content


@pytest.mark.asyncio
async def test_figer_decision_figee_returns_empty_fichiers_modifies(db_conn, tmp_path):
    """Phase 4.2 — freeze_session decision_figee retourne fichiers_modifies = []."""
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (id, project_id, livrable_type, titre, statut, created_at, updated_at)
        VALUES (11, 1, 'decision_figee', 'Décision test', 'OUVERTE', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    db_conn.commit()
    
    mock_livrable = "| 2026-05-15 | Décision test | Raison test |"
    
    with patch('backend.services.model_router.call_model', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_livrable
        livrable = await reflexion_service.freeze_session(11, db_conn)
    
    assert 'fichiers_modifies' in livrable
    assert livrable['fichiers_modifies'] == []
