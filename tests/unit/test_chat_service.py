"""
Tests unitaires — chat_service.py
Vérifie le parsing METHODO, construction system prompt, et envoi messages.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.chat_service import (
    read_methodo_context,
    get_project_context,
    build_system_prompt,
    send_chat_message
)


class TestReadMethodoContext:
    """read_methodo_context() : parsing JARVIS_INDEX.md et chargement fichiers."""

    def test_fichiers_presents(self, tmp_path):
        """JARVIS_INDEX.md + fichiers listés → contenu chargé."""
        # Créer structure METHODO
        methodo = tmp_path / "METHODO"
        methodo.mkdir()
        
        regles_dir = methodo / "REGLES"
        regles_dir.mkdir()
        
        info_dir = methodo / "informations utilisateur"
        info_dir.mkdir()
        
        # Créer JARVIS_INDEX.md avec tableau
        index_content = """# JARVIS INDEX

## TOUJOURS injectés

| Ordre | Fichier | Description |
|-------|---------|-------------|
| 1 | `REGLES/REGLES_GLOBALES.md` | Règles globales |
| 2 | `informations utilisateur/PROFIL_UTILISATEUR.md` | Profil |

## Autres sections
"""
        (methodo / "JARVIS_INDEX.md").write_text(index_content, encoding="utf-8")
        
        # Créer les fichiers référencés
        (regles_dir / "REGLES_GLOBALES.md").write_text("# Règles\nContenu règles", encoding="utf-8")
        (info_dir / "PROFIL_UTILISATEUR.md").write_text("# Profil\nContenu profil", encoding="utf-8")
        
        result = read_methodo_context(str(methodo))
        
        assert "Contenu règles" in result
        assert "Contenu profil" in result
        assert "REGLES GLOBALES" in result or "REGLES_GLOBALES" in result

    def test_fichier_absent_skip_silencieux(self, tmp_path, caplog):
        """Fichier listé mais absent → skip avec warning."""
        methodo = tmp_path / "METHODO"
        methodo.mkdir()
        
        index_content = """## TOUJOURS injectés

| 1 | `FICHIER_ABSENT.md` | Description |
"""
        (methodo / "JARVIS_INDEX.md").write_text(index_content, encoding="utf-8")
        
        result = read_methodo_context(str(methodo))
        
        # Doit retourner une string (vide ou avec sections)
        assert isinstance(result, str)
        # Vérifier qu'un warning a été loggué
        assert any("FICHIER_ABSENT" in record.message for record in caplog.records)

    def test_index_absent_retourne_vide(self, tmp_path):
        """JARVIS_INDEX.md absent → retourne ''."""
        methodo = tmp_path / "METHODO"
        methodo.mkdir()
        
        result = read_methodo_context(str(methodo))
        
        assert result == ""


class TestGetProjectContext:
    """get_project_context() : lecture PROJET_CONTEXTE.md."""

    def test_fichier_present(self, tmp_path):
        """PROJET_CONTEXTE.md présent → contenu retourné."""
        (tmp_path / "PROJET_CONTEXTE.md").write_text("# Projet\nContenu projet", encoding="utf-8")
        
        result = get_project_context(str(tmp_path))
        
        assert result == "# Projet\nContenu projet"

    def test_fichier_absent(self, tmp_path):
        """PROJET_CONTEXTE.md absent → None."""
        result = get_project_context(str(tmp_path))
        
        assert result is None

    def test_fichier_trop_long_tronque(self, tmp_path):
        """Fichier > 12000 chars → tronqué."""
        long_content = "A" * 15000
        (tmp_path / "PROJET_CONTEXTE.md").write_text(long_content, encoding="utf-8")
        
        result = get_project_context(str(tmp_path))
        
        assert len(result) < 15000
        assert "tronqué" in result


class TestBuildSystemPrompt:
    """build_system_prompt() : concaténation des contextes."""

    def test_complet_avec_tous_elements(self):
        """Preset + methodo + session_note + project → tous présents."""
        preset = "Tu es JARVIS"
        methodo = "=== RÈGLES ===\nRègles globales"
        session_note = "Travail sur module chat"
        project = "# Projet JARVIS 2.0"
        
        result = build_system_prompt(preset, methodo, session_note, project)
        
        assert "Tu es JARVIS" in result
        assert "RÈGLES" in result
        assert "NOTE DE SESSION" in result
        assert "Travail sur module chat" in result
        assert "PROJET ACTIF" in result
        assert "# Projet JARVIS 2.0" in result

    def test_sans_projet(self):
        """project_context = None → pas de section PROJET ACTIF."""
        preset = "Tu es JARVIS"
        
        result = build_system_prompt(preset, "", "", None)
        
        assert "Tu es JARVIS" in result
        assert "PROJET ACTIF" not in result

    def test_sans_methodo_ni_session_note(self):
        """Seulement preset → pas de sections vides."""
        preset = "Tu es JARVIS"
        
        result = build_system_prompt(preset, "", "", None)
        
        assert result == "Tu es JARVIS"


class TestSendChatMessage:
    """send_chat_message() : envoi message avec mock httpx."""

    @pytest.mark.asyncio
    async def test_envoi_message_mock_success(self, tmp_path):
        """Mock httpx → 2 messages créés en DB."""
        import sqlite3
        from datetime import datetime
        
        # Créer DB temporaire
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Créer tables
        cursor.execute("""
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                title TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                path TEXT
            )
        """)
        
        # Créer conversation
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO conversations (project_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (None, "Test", now, now)
        )
        conv_id = cursor.lastrowid
        conn.commit()
        
        # Config mock
        config = {
            "api_keys": {"openrouter_key": "sk-test"},
            "chat": {
                "model": "anthropic/claude-sonnet-4.5",
                "methodo_path": "",
                "session_note": "",
                "system_prompt_preset": "Tu es JARVIS"
            }
        }
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Bonjour utilisateur"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await send_chat_message(conv_id, "Bonjour JARVIS", conn, config)
        
        # Vérifier résultat
        assert result["content"] == "Bonjour utilisateur"
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        
        # Vérifier messages en DB
        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id", (conv_id,))
        messages = cursor.fetchall()
        
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Bonjour JARVIS"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Bonjour utilisateur"
        
        conn.close()

    @pytest.mark.asyncio
    async def test_erreur_401_message_clair(self, tmp_path):
        """HTTP 401 → exception avec message clair."""
        import sqlite3
        from datetime import datetime
        
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                title TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                created_at TEXT
            )
        """)
        
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO conversations (project_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (None, "Test", now, now)
        )
        conv_id = cursor.lastrowid
        conn.commit()
        
        config = {
            "api_keys": {"openrouter_key": "sk-invalid"},
            "chat": {
                "model": "anthropic/claude-sonnet-4.5",
                "methodo_path": "",
                "session_note": "",
                "system_prompt_preset": "Tu es JARVIS"
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await send_chat_message(conv_id, "Test", conn, config)
            
            assert "Clé API invalide" in str(exc_info.value)
        
        conn.close()
