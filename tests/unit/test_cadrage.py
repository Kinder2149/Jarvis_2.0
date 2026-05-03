import pytest
import sqlite3
from pathlib import Path
import tempfile
import shutil

from backend.services.cadrage import check_cadrage_health


@pytest.fixture
def temp_project_with_contexte(tmp_path):
    """Crée un projet temporaire avec PROJET_CONTEXTE.md."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    
    # Créer PROJET_CONTEXTE.md minimal
    contexte = project_path / "PROJET_CONTEXTE.md"
    contexte.write_text("""# PROJET_CONTEXTE

## 6. DÉCISIONS FIGÉES

| Date | Décision | Raison |
|---|---|---|
| 2026-05-01 | Test | Test |

## 8. SESSION EN COURS

Session en cours : test

## 9. BACKLOG

- Item 1
""", encoding="utf-8")
    
    # Créer graphify
    graphify_dir = project_path / "graphify-out"
    graphify_dir.mkdir()
    graph_report = graphify_dir / "GRAPH_REPORT.md"
    graph_report.write_text("# Graph Report\n\n1000 nodes", encoding="utf-8")
    
    return project_path


@pytest.fixture
def temp_db_with_project(temp_project_with_contexte):
    """Crée une BDD temporaire avec un projet."""
    db_path = temp_project_with_contexte / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Créer tables minimales
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name TEXT,
            path TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE app_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Insérer projet
    cursor.execute("""
        INSERT INTO projects (id, name, path)
        VALUES (1, 'Test Project', ?)
    """, (str(temp_project_with_contexte),))
    
    # Insérer methodo_path (vide pour ce test)
    cursor.execute("""
        INSERT OR REPLACE INTO app_config (key, value)
        VALUES ('methodo_path', '')
    """)
    
    conn.commit()
    
    yield conn, 1
    
    conn.close()


def test_check_cadrage_health_all_green(temp_db_with_project):
    """Test check_cadrage_health avec tous les checks verts."""
    conn, project_id = temp_db_with_project
    
    result = check_cadrage_health(project_id, conn)
    
    assert result["verdict_global"] in ["vert", "orange"]
    assert len(result["checks"]) == 7
    
    # Vérifier que PROJET_CONTEXTE est vert
    contexte_check = next((c for c in result["checks"] if c["nom"] == "PROJET_CONTEXTE.md"), None)
    assert contexte_check is not None
    assert contexte_check["statut"] == "vert"


def test_check_cadrage_health_projet_inexistant():
    """Test check_cadrage_health avec projet inexistant."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, path TEXT)")
    conn.commit()
    
    result = check_cadrage_health(999, conn)
    
    assert result["verdict_global"] == "rouge"
    assert result["checks"][0]["statut"] == "rouge"
    
    conn.close()


def test_check_cadrage_health_contexte_absent(tmp_path):
    """Test check_cadrage_health avec PROJET_CONTEXTE absent."""
    project_path = tmp_path / "empty_project"
    project_path.mkdir()
    
    conn = sqlite3.Connection(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, path TEXT)")
    cursor.execute("CREATE TABLE app_config (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("INSERT INTO projects (id, name, path) VALUES (1, 'Test', ?)", (str(project_path),))
    cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES ('methodo_path', '')")
    conn.commit()
    
    result = check_cadrage_health(1, conn)
    
    assert result["verdict_global"] == "rouge"
    
    contexte_check = next((c for c in result["checks"] if c["nom"] == "PROJET_CONTEXTE.md"), None)
    assert contexte_check["statut"] == "rouge"
    
    conn.close()
