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
    send_chat_message,
    read_local_folder,
    read_local_file,
    search_web
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
        
        result = build_system_prompt(preset=preset, methodo_context=methodo, session_note=session_note, project_context=project)
        
        assert "Tu es JARVIS" in result
        assert "RÈGLES" in result
        assert "NOTE DE SESSION" in result
        assert "Travail sur module chat" in result
        assert "PROJET ACTIF" in result
        assert "# Projet JARVIS 2.0" in result

    def test_sans_projet(self):
        """project_context = None → pas de section PROJET ACTIF."""
        preset = "Tu es JARVIS"
        
        result = build_system_prompt(preset=preset, methodo_context="", session_note="", project_context=None)
        
        assert "Tu es JARVIS" in result
        assert "PROJET ACTIF" not in result

    def test_sans_methodo_ni_session_note(self):
        """Seulement preset → pas de sections vides."""
        preset = "Tu es JARVIS"
        
        result = build_system_prompt(preset=preset, methodo_context="", session_note="", project_context=None)
        
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
                folder_path TEXT,
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
                folder_path TEXT,
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


class TestReadLocalFolder:
    """read_local_folder() : liste fichiers d'un dossier local."""

    def test_dossier_present_non_recursif(self, tmp_path):
        """Dossier avec fichiers → liste retournée."""
        (tmp_path / "file1.txt").write_text("contenu 1")
        (tmp_path / "file2.md").write_text("contenu 2")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("contenu 3")
        
        result = read_local_folder(str(tmp_path), recursive=False)
        
        assert result["error"] is None
        assert len(result["files"]) == 2
        assert any(f["path"] == "file1.txt" for f in result["files"])
        assert any(f["path"] == "file2.md" for f in result["files"])
        assert not any(f["path"] == "subdir/file3.txt" for f in result["files"])

    def test_dossier_present_recursif(self, tmp_path):
        """Dossier avec sous-dossiers → liste récursive."""
        (tmp_path / "file1.txt").write_text("contenu 1")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("contenu 2")
        
        result = read_local_folder(str(tmp_path), recursive=True)
        
        assert result["error"] is None
        assert len(result["files"]) == 2
        assert any("file1.txt" in f["path"] for f in result["files"])
        assert any("subdir" in f["path"] and "file2.txt" in f["path"] for f in result["files"])

    def test_graph_report_detecte(self, tmp_path):
        """GRAPH_REPORT.md présent → graph_report=True."""
        graphify_dir = tmp_path / "graphify-out"
        graphify_dir.mkdir()
        (graphify_dir / "GRAPH_REPORT.md").write_text("# Graph Report")
        
        result = read_local_folder(str(tmp_path))
        
        assert result["graph_report"] is True

    def test_dossier_absent(self):
        """Dossier inexistant → erreur."""
        result = read_local_folder("/chemin/inexistant")
        
        assert result["error"] is not None
        assert "introuvable" in result["error"].lower()

    def test_chemin_fichier_pas_dossier(self, tmp_path):
        """Chemin vers fichier (pas dossier) → erreur."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("contenu")
        
        result = read_local_folder(str(file_path))
        
        assert result["error"] is not None
        assert "pas un dossier" in result["error"].lower()


class TestReadLocalFile:
    """read_local_file() : lit contenu fichier avec sécurité."""

    def test_fichier_present_petit(self, tmp_path):
        """Fichier < 50 Ko → contenu complet."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Contenu test")
        
        result = read_local_file(str(tmp_path), "test.txt")
        
        assert result["error"] is None
        assert result["content"] == "Contenu test"
        assert result["truncated"] is False

    def test_fichier_trop_grand_tronque(self, tmp_path):
        """Fichier > 50 Ko → tronqué."""
        file_path = tmp_path / "big.txt"
        content = "x" * (60 * 1024)  # 60 Ko
        file_path.write_text(content)
        
        result = read_local_file(str(tmp_path), "big.txt")
        
        assert result["error"] is None
        assert len(result["content"]) <= 50 * 1024
        assert result["truncated"] is True

    def test_path_traversal_bloque(self, tmp_path):
        """Tentative path traversal → accès refusé."""
        (tmp_path / "file.txt").write_text("contenu")
        
        result = read_local_file(str(tmp_path), "../../../etc/passwd")
        
        assert result["error"] is not None
        assert "path traversal" in result["error"].lower()

    def test_fichier_absent(self, tmp_path):
        """Fichier inexistant → erreur."""
        result = read_local_file(str(tmp_path), "absent.txt")
        
        assert result["error"] is not None
        assert "introuvable" in result["error"].lower()

    def test_chemin_vers_dossier(self, tmp_path):
        """Chemin vers dossier (pas fichier) → erreur."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        result = read_local_file(str(tmp_path), "subdir")
        
        assert result["error"] is not None
        assert "pas un fichier" in result["error"].lower()


class TestSearchWeb:
    """search_web() : recherche web via API."""

    @pytest.mark.asyncio
    async def test_sans_cle_api_desactive(self):
        """Pas de clé API → recherche désactivée gracieusement."""
        result = await search_web("test query", api_key=None)
        
        assert result["error"] is not None
        assert "désactivée" in result["error"].lower()
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_avec_cle_api_mock_success(self):
        """Avec clé API → résultats retournés."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {"title": "Result 1", "url": "https://example.com/1", "description": "Desc 1"},
                    {"title": "Result 2", "url": "https://example.com/2", "description": "Desc 2"}
                ]
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await search_web("test query", api_key="fake_key")
            
            assert result["error"] is None
            assert len(result["results"]) == 2
            assert result["results"][0]["title"] == "Result 1"
            assert result["results"][0]["url"] == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_erreur_api_gere(self):
        """Erreur API → erreur retournée gracieusement."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await search_web("test query", api_key="fake_key")
            
            assert result["error"] is not None
            assert result["results"] == []
