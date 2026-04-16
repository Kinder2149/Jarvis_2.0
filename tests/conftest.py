"""
Fixtures partagées pour tous les tests JARVIS.
"""
import sqlite3
import pytest
from pathlib import Path


# ─── DB en mémoire ────────────────────────────────────────────────────────────

def _create_schema(conn: sqlite3.Connection):
    """Crée toutes les tables JARVIS dans la connexion donnée."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            workflow_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CREATED',
            current_step_index INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pipeline_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            step_index INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            step_display_name TEXT NOT NULL,
            model_type TEXT NOT NULL,
            model_used TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            input_data TEXT,
            output_data TEXT,
            requires_validation INTEGER DEFAULT 0,
            validated_at TEXT,
            error_message TEXT,
            output_type TEXT DEFAULT 'text',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS model_decision_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            step_name TEXT,
            model_type TEXT,
            model_id_chosen TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            title TEXT NOT NULL DEFAULT 'Nouvelle conversation',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()


def make_memory_db() -> sqlite3.Connection:
    """Retourne une connexion SQLite en mémoire avec le schéma JARVIS."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _create_schema(conn)
    return conn


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """Base SQLite en mémoire, isolée par test."""
    conn = make_memory_db()
    yield conn
    conn.close()


@pytest.fixture
def sample_config():
    """Configuration JARVIS avec les modèles validés avril 2026."""
    return {
        "api_keys": {
            "openrouter_key": "sk-or-test-key",
            "anthropic_key": "",
            "google_key": ""
        },
        "model_preferences": {
            "routing": "google/gemini-2.0-flash-001",
            "structuring": "anthropic/claude-haiku-4.5",
            "code": "anthropic/claude-sonnet-4.5",
            "analysis": "anthropic/claude-opus-4.5"
        }
    }


@pytest.fixture
def project_in_db(db, tmp_path):
    """Crée un projet de test dans la DB en mémoire avec un dossier réel."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO projects (name, path, type) VALUES (?, ?, ?)",
        ("Test Project", str(project_dir), "web")
    )
    db.commit()
    return {"id": cursor.lastrowid, "path": str(project_dir)}


@pytest.fixture
def temp_db_path(tmp_path):
    """Chemin vers un fichier SQLite temporaire (pour les tests d'intégration API)."""
    return tmp_path / "test_jarvis.db"
