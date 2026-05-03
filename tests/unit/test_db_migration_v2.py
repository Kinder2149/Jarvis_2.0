"""
Tests unitaires — _migrate_v2() dans database.py
Vérifie l'idempotence et la présence des nouvelles colonnes.
"""
import sqlite3
import pytest
from backend.database import _migrate_v2


def _make_db():
    """Crée une DB SQLite en mémoire avec le schéma minimal."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            workflow_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CREATED',
            current_step_index INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE pipeline_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            step_index INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            step_display_name TEXT NOT NULL,
            model_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def _get_columns(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return [row["name"] for row in cursor.fetchall()]


class TestMigrateV2:

    def test_colonnes_sessions_apres_migration(self):
        conn = _make_db()
        _migrate_v2(conn)
        cols = _get_columns(conn, "sessions")
        assert "modele_override" in cols
        assert "source_mission_prompt_id" in cols
        conn.close()

    def test_colonne_pipeline_steps_apres_migration(self):
        conn = _make_db()
        _migrate_v2(conn)
        cols = _get_columns(conn, "pipeline_steps")
        assert "sub_step_index" in cols
        conn.close()

    def test_migration_idempotente_double_appel(self):
        conn = _make_db()
        _migrate_v2(conn)
        _migrate_v2(conn)
        cols_sessions = _get_columns(conn, "sessions")
        assert "modele_override" in cols_sessions
        assert "source_mission_prompt_id" in cols_sessions
        conn.close()

    def test_migration_idempotente_triple_appel(self):
        conn = _make_db()
        for _ in range(3):
            _migrate_v2(conn)
        cols = _get_columns(conn, "sessions")
        assert "modele_override" in cols
        conn.close()

    def test_index_cree(self):
        conn = _make_db()
        _migrate_v2(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            ("idx_pipeline_steps_session_sub",)
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_donnees_existantes_intactes(self):
        conn = _make_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (project_id, workflow_type, status, current_step_index) VALUES (?, ?, ?, ?)",
            (1, "atelier_restauration", "COMPLETED", 0)
        )
        conn.commit()

        _migrate_v2(conn)

        cursor.execute("SELECT workflow_type, status FROM sessions WHERE id = 1")
        row = cursor.fetchone()
        assert row["workflow_type"] == "atelier_restauration"
        assert row["status"] == "COMPLETED"
        conn.close()

    def test_modele_override_nullable(self):
        conn = _make_db()
        _migrate_v2(conn)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (project_id, workflow_type, status, current_step_index, modele_override) VALUES (?, ?, ?, ?, ?)",
            (1, "code_mission", "CREATED", 0, None)
        )
        conn.commit()
        cursor.execute("SELECT modele_override FROM sessions WHERE id = 1")
        row = cursor.fetchone()
        assert row["modele_override"] is None
        conn.close()

    def test_modele_override_storable(self):
        conn = _make_db()
        _migrate_v2(conn)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (project_id, workflow_type, status, current_step_index, modele_override) VALUES (?, ?, ?, ?, ?)",
            (1, "code_mission", "CREATED", 0, "anthropic/claude-sonnet-4.5")
        )
        conn.commit()
        cursor.execute("SELECT modele_override FROM sessions WHERE id = 1")
        row = cursor.fetchone()
        assert row["modele_override"] == "anthropic/claude-sonnet-4.5"
        conn.close()
