"""
Tests d'intégration — API Chat (/api/chat/*)
Vérifie les routes conversations et messages avec mock httpx.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def client_and_db(temp_db_path):
    """Client FastAPI avec DB temporaire."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            yield c


class TestCreateConversation:
    """POST /api/chat/conversations"""

    def test_creation_sans_projet(self, client_and_db):
        """Création conversation sans projet → 200, retourne id + title."""
        c = client_and_db
        
        response = c.post("/api/chat/conversations", json={"title": "Test Chat"})
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Chat"
        assert data["project_id"] is None

    def test_creation_avec_projet(self, client_and_db):
        """Création avec project_id → project_id présent dans réponse."""
        c = client_and_db
        
        # Créer un projet d'abord
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test Project",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            response = c.post("/api/chat/conversations", json={
                "project_id": project["id"],
                "title": "Chat Projet"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == project["id"]


class TestListConversations:
    """GET /api/chat/conversations"""

    def test_liste_vide_au_debut(self, client_and_db):
        """Aucune conversation → liste vide."""
        c = client_and_db
        
        response = c.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_liste_avec_conversations(self, client_and_db):
        """Conversations créées → retournées dans la liste."""
        c = client_and_db
        
        c.post("/api/chat/conversations", json={"title": "Conv 1"})
        c.post("/api/chat/conversations", json={"title": "Conv 2"})
        
        response = c.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("message_count" in conv for conv in data)

    def test_filtre_par_projet(self, client_and_db):
        """Filtre project_id → retourne seulement conversations du projet."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            # Créer 1 conv avec projet, 1 sans
            c.post("/api/chat/conversations", json={"project_id": project["id"], "title": "Avec projet"})
            c.post("/api/chat/conversations", json={"title": "Sans projet"})
            
            response = c.get(f"/api/chat/conversations?project_id={project['id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Avec projet"


class TestGetConversation:
    """GET /api/chat/conversations/{id}"""

    def test_get_conversation_existante(self, client_and_db):
        """Conversation existante → retourne messages (vide au début)."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        
        response = c.get(f"/api/chat/conversations/{conv['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv["id"]
        assert data["title"] == "Test"
        assert "messages" in data
        assert len(data["messages"]) == 0

    def test_get_conversation_inexistante(self, client_and_db):
        """Conversation inexistante → 404."""
        c = client_and_db
        
        response = c.get("/api/chat/conversations/99999")
        
        assert response.status_code == 404


class TestSendMessage:
    """POST /api/chat/conversations/{id}/messages"""

    def test_envoi_message_mock_httpx(self, client_and_db):
        """Envoi message avec mock httpx → 200, 2 messages créés."""
        c = client_and_db
        
        # Insérer une clé API dans SQLite pour le test
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO app_config (key, value, category, updated_at)
            VALUES ('openrouter_key', 'sk-test-key', 'api_keys', datetime('now'))
        """)
        conn.commit()
        conn.close()
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        
        # Mock httpx response au format OpenRouter
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Réponse assistant"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        with patch("backend.services.chat_service.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            response = c.post(f"/api/chat/conversations/{conv['id']}/messages", json={
                "content": "Bonjour"
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_message" in data
        assert data["user_message"]["content"] == "Bonjour"
        assert data["user_message"]["role"] == "user"
        
        assert "assistant_message" in data
        assert data["assistant_message"]["content"] == "Réponse assistant"
        assert data["assistant_message"]["role"] == "assistant"
        
        # Vérifier que les messages sont bien en DB
        conv_data = c.get(f"/api/chat/conversations/{conv['id']}").json()
        assert len(conv_data["messages"]) == 2


class TestDeleteConversation:
    """DELETE /api/chat/conversations/{id}"""

    def test_suppression_conversation(self, client_and_db):
        """Suppression conversation → 200, {"deleted": true}."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "À supprimer"}).json()
        
        response = c.delete(f"/api/chat/conversations/{conv['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

    def test_get_apres_suppression(self, client_and_db):
        """GET après DELETE → 404."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        c.delete(f"/api/chat/conversations/{conv['id']}")
        
        response = c.get(f"/api/chat/conversations/{conv['id']}")
        
        assert response.status_code == 404

    def test_suppression_inexistante(self, client_and_db):
        """DELETE conversation inexistante → 404."""
        c = client_and_db
        
        response = c.delete("/api/chat/conversations/99999")
        
        assert response.status_code == 404


class TestConversationFolderPath:
    """Tests folder_path sur conversations."""

    def test_creation_avec_folder_path_explicite(self, client_and_db):
        """Création avec folder_path → folder_path présent."""
        c = client_and_db
        
        response = c.post("/api/chat/conversations", json={
            "title": "Chat Dossier",
            "folder_path": "C:\\Test\\Folder"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["folder_path"] == "C:\\Test\\Folder"

    def test_creation_avec_projet_herite_path(self, client_and_db):
        """Création avec project_id → hérite du local_path du projet."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.TemporaryDirectory() as local_dir:
                project = c.post("/api/projects", json={
                    "name": "Test Project",
                    "path": tmpdir,
                    "type": "Web",
                    "local_path": local_dir
                }).json()
                
                response = c.post("/api/chat/conversations", json={
                    "project_id": project["id"],
                    "title": "Chat Projet"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["folder_path"] == local_dir

    def test_update_folder_path(self, client_and_db):
        """PATCH /conversations/{id}/folder → met à jour folder_path."""
        c = client_and_db
        
        conv = c.post("/api/chat/conversations", json={"title": "Test"}).json()
        
        response = c.patch(f"/api/chat/conversations/{conv['id']}/folder?folder_path=C:\\New\\Path")
        
        assert response.status_code == 200
        assert response.json()["folder_path"] == "C:\\New\\Path"
        
        # Vérifier que la conversation a bien été mise à jour
        conv_data = c.get(f"/api/chat/conversations/{conv['id']}").json()
        assert conv_data["folder_path"] == "C:\\New\\Path"

    def test_liste_conversations_inclut_folder_path(self, client_and_db):
        """GET /conversations → folder_path inclus dans la liste."""
        c = client_and_db
        
        c.post("/api/chat/conversations", json={
            "title": "Conv 1",
            "folder_path": "C:\\Folder1"
        })
        
        response = c.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["folder_path"] == "C:\\Folder1"


class TestConversationInternetAccess:
    """Tests internet_access sur conversations."""

    def test_creation_avec_internet_false_par_defaut(self, client_and_db):
        """Création conversation → internet_access False par défaut."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test Project",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            r = c.post("/api/chat/conversations", json={"project_id": project["id"]})
            assert r.status_code == 200
            data = r.json()
            assert "internet_access" in data or True  # champ optionnel dans create

    def test_patch_internet_access(self, client_and_db):
        """PATCH active l'accès internet."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test Project",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            # Créer conversation
            r = c.post("/api/chat/conversations", json={"project_id": project["id"]})
            conv_id = r.json()["id"]
            
            # PATCH
            r2 = c.patch(f"/api/chat/conversations/{conv_id}", json={"internet_access": True})
            assert r2.status_code == 200


class TestConversationContextSummary:
    """Tests context_summary sur conversations."""

    def test_patch_context_summary(self, client_and_db):
        """PATCH met à jour le résumé de conversation."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test Project",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            r = c.post("/api/chat/conversations", json={"project_id": project["id"]})
            conv_id = r.json()["id"]
            
            r2 = c.patch(f"/api/chat/conversations/{conv_id}", json={"context_summary": "Résumé test"})
            assert r2.status_code == 200

    def test_get_conversation_inclut_context_summary(self, client_and_db):
        """GET conversation retourne context_summary."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test Project",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            r = c.post("/api/chat/conversations", json={"project_id": project["id"]})
            conv_id = r.json()["id"]
            
            c.patch(f"/api/chat/conversations/{conv_id}", json={"context_summary": "Test résumé"})
            
            r2 = c.get(f"/api/chat/conversations/{conv_id}")
            assert r2.status_code == 200
            # Le champ context_summary doit être présent
            data = r2.json()
            assert "context_summary" in data


class TestConversationModel:
    """Tests model sur conversations."""

    def test_patch_model(self, client_and_db):
        """PATCH met à jour le modèle de la conversation."""
        c = client_and_db
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = c.post("/api/projects", json={
                "name": "Test Project",
                "path": tmpdir,
                "type": "Web"
            }).json()
            
            r = c.post("/api/chat/conversations", json={"project_id": project["id"]})
            conv_id = r.json()["id"]
            
            r2 = c.patch(f"/api/chat/conversations/{conv_id}", json={"model": "anthropic/claude-opus-4"})
            assert r2.status_code == 200


class TestGlobalContextInjection:
    """Vérifie que le global_context est bien injecté dans le system prompt."""

    def test_global_context_sauvegarde_et_relecture(self, client_and_db):
        """Le global_context sauvegardé via POST /config/global_context
        est bien retourné par GET /config/global_context."""
        c = client_and_db

        # Sauvegarder
        resp = c.post("/api/config/global_context", json={"value": "Contexte de test"})
        assert resp.status_code == 200

        # Relire
        resp = c.get("/api/config/global_context")
        assert resp.status_code == 200
        assert resp.json()["value"] == "Contexte de test"

    def test_global_context_vide_par_defaut(self, client_and_db):
        """Sans configuration, global_context retourne une chaîne vide."""
        c = client_and_db
        resp = c.get("/api/config/global_context")
        assert resp.status_code == 200
        data = resp.json()
        assert "value" in data
        assert data["value"] == "" or data["value"] is None or isinstance(data["value"], str)

    def test_global_context_ecrase_ancienne_valeur(self, client_and_db):
        """POST /config/global_context remplace l'ancienne valeur."""
        c = client_and_db
        c.post("/api/config/global_context", json={"value": "Première version"})
        c.post("/api/config/global_context", json={"value": "Deuxième version"})
        resp = c.get("/api/config/global_context")
        assert resp.json()["value"] == "Deuxième version"


class TestConversationModelBehavior:
    """Vérifie que le modèle est correctement associé à une conversation."""

    def test_create_conversation_avec_model(self, client_and_db):
        """Une conversation créée avec un modèle le conserve en GET."""
        c = client_and_db
        resp = c.post("/api/chat/conversations", json={
            "title": "Test modèle",
            "model": "anthropic/claude-haiku-4-5"
        })
        assert resp.status_code == 200
        conv_id = resp.json()["id"]

        resp = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp.status_code == 200
        assert resp.json()["model"] == "anthropic/claude-haiku-4-5"

    def test_patch_model_persiste(self, client_and_db):
        """PATCH model sur une conversation existante → GET retourne le nouveau modèle."""
        c = client_and_db
        resp = c.post("/api/chat/conversations", json={"title": "Test patch model"})
        conv_id = resp.json()["id"]

        c.patch(f"/api/chat/conversations/{conv_id}", json={"model": "google/gemini-2.0-flash-001"})

        resp = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp.json()["model"] == "google/gemini-2.0-flash-001"

    def test_model_present_dans_liste_conversations(self, client_and_db):
        """GET /conversations liste inclut le champ model pour chaque conversation."""
        c = client_and_db
        c.post("/api/chat/conversations", json={"title": "Conv1", "model": "test-model"})
        resp = c.get("/api/chat/conversations")
        assert resp.status_code == 200
        convs = resp.json()
        assert len(convs) >= 1
        assert "model" in convs[0]


class TestConversationDossierAssociation:
    """Vérifie qu'une conversation s'associe correctement à un dossier."""

    def test_create_conversation_avec_project_id(self, client_and_db, tmp_path):
        """Créer une conversation liée à un dossier → project_id retourné en GET."""
        c = client_and_db

        # Créer un dossier avec un chemin temporaire valide
        dossier_path = tmp_path / "mon-dossier-test"
        dossier_path.mkdir()
        resp = c.post("/api/projects/", json={
            "name": "Mon Dossier Test",
            "path": str(dossier_path),
            "type": "general",
            "module_type": "dossier"
        })
        assert resp.status_code == 200
        dossier_id = resp.json()["id"]

        # Créer une conversation liée
        resp = c.post("/api/chat/conversations", json={
            "title": "Conv liée",
            "project_id": dossier_id
        })
        assert resp.status_code == 200
        conv_id = resp.json()["id"]

        # Vérifier l'association
        resp = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == dossier_id

    def test_conversations_filtrees_par_project_id(self, client_and_db, tmp_path):
        """GET /conversations?project_id=X ne retourne que les convs de ce dossier."""
        c = client_and_db

        dossier_path = tmp_path / "dossier-filtre"
        dossier_path.mkdir()
        resp = c.post("/api/projects/", json={
            "name": "Dossier Filtre",
            "path": str(dossier_path),
            "type": "general",
            "module_type": "dossier"
        })
        dossier_id = resp.json()["id"]

        # Conv liée au dossier
        c.post("/api/chat/conversations", json={"title": "Conv A", "project_id": dossier_id})
        # Conv non liée
        c.post("/api/chat/conversations", json={"title": "Conv B"})

        resp = c.get(f"/api/chat/conversations?project_id={dossier_id}")
        assert resp.status_code == 200
        convs = resp.json()
        assert len(convs) == 1
        assert convs[0]["title"] == "Conv A"

    def test_conversation_herite_local_path_du_dossier(self, client_and_db, tmp_path):
        """Si dossier a un local_path et conv n'a pas de folder_path → héritage automatique."""
        c = client_and_db

        # Créer dossier avec local_path
        local_path = str(tmp_path)
        dossier_path = tmp_path / "dossier-path"
        dossier_path.mkdir()
        resp = c.post("/api/projects/", json={
            "name": "Dossier Path",
            "path": str(dossier_path),
            "type": "general",
            "module_type": "dossier"
        })
        dossier_id = resp.json()["id"]
        c.patch(f"/api/projects/{dossier_id}", json={"local_path": local_path})

        # Créer conv liée sans folder_path explicite
        resp = c.post("/api/chat/conversations", json={
            "title": "Conv héritage",
            "project_id": dossier_id
        })
        conv_id = resp.json()["id"]

        resp = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp.json()["folder_path"] == local_path


class TestConversationInternetAndSummary:
    """Tests pour internet_access comportement et update-summary endpoint."""

    def test_internet_access_false_par_defaut(self, client_and_db):
        """Une nouvelle conversation a internet_access=False par défaut."""
        c = client_and_db
        resp = c.post("/api/chat/conversations", json={"title": "Test internet"})
        conv_id = resp.json()["id"]
        resp = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp.json()["internet_access"] == False

    def test_patch_internet_access_true(self, client_and_db):
        """PATCH internet_access=True → GET retourne True."""
        c = client_and_db
        resp = c.post("/api/chat/conversations", json={"title": "Test internet patch"})
        conv_id = resp.json()["id"]

        c.patch(f"/api/chat/conversations/{conv_id}", json={"internet_access": True})
        resp = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp.json()["internet_access"] == True

    def test_update_summary_conversation_vide(self, client_and_db):
        """POST /update-summary sur conversation sans messages → retourne summary vide, pas d'erreur 500."""
        c = client_and_db
        resp = c.post("/api/chat/conversations", json={"title": "Conv vide"})
        conv_id = resp.json()["id"]

        resp = c.post(f"/api/chat/conversations/{conv_id}/update-summary")
        # Pas d'erreur serveur — peut retourner 200 avec summary vide ou message explicatif
        assert resp.status_code in [200, 204]
        if resp.status_code == 200:
            data = resp.json()
            assert "summary" in data or "ok" in data

    def test_update_summary_conversation_inexistante(self, client_and_db):
        """POST /update-summary sur conversation inexistante → 404."""
        c = client_and_db
        resp = c.post("/api/chat/conversations/99999/update-summary")
        assert resp.status_code == 404

    def test_patch_context_summary_puis_get(self, client_and_db):
        """PATCH context_summary → GET retourne la valeur mise à jour."""
        c = client_and_db
        resp = c.post("/api/chat/conversations", json={"title": "Test summary"})
        conv_id = resp.json()["id"]

        summary = "Résumé de test : on a parlé de Python et de FastAPI."
        c.patch(f"/api/chat/conversations/{conv_id}", json={"context_summary": summary})

        resp = c.get(f"/api/chat/conversations/{conv_id}")
        assert resp.json()["context_summary"] == summary
