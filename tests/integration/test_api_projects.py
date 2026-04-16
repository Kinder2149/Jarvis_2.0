"""
Tests d'intégration — routes /api/projects
Utilise une DB SQLite dans un fichier temporaire.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from pathlib import Path


@pytest.fixture
def client_with_temp_db(temp_db_path):
    """
    TestClient avec une DB SQLite temporaire.
    Patche backend.database.DB_PATH → get_connection() utilise le fichier temp.
    """
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            yield c


class TestListProjects:

    def test_retourne_liste_vide_au_depart(self, client_with_temp_db):
        response = client_with_temp_db.get("/api/projects")
        assert response.status_code == 200
        assert response.json() == []

    def test_retourne_les_projets_crees(self, client_with_temp_db, tmp_path):
        project_dir = tmp_path / "mon_projet"
        project_dir.mkdir()
        client_with_temp_db.post("/api/projects", json={
            "name": "Mon Projet", "path": str(project_dir), "type": "web"
        })
        data = client_with_temp_db.get("/api/projects").json()
        assert len(data) == 1
        assert data[0]["name"] == "Mon Projet"


class TestCreateProject:

    def test_cree_projet_avec_dossier_existant(self, client_with_temp_db, tmp_path):
        project_dir = tmp_path / "nouveau"
        project_dir.mkdir()
        response = client_with_temp_db.post("/api/projects", json={
            "name": "Nouveau Projet", "path": str(project_dir), "type": "web"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Nouveau Projet"

    def test_erreur_si_dossier_inexistant(self, client_with_temp_db):
        response = client_with_temp_db.post("/api/projects", json={
            "name": "Ghost", "path": "/chemin/inexistant/12345", "type": "web"
        })
        assert response.status_code == 400

    def test_has_projet_contexte_false_sans_fichier(self, client_with_temp_db, tmp_path):
        project_dir = tmp_path / "sans_contexte"
        project_dir.mkdir()
        response = client_with_temp_db.post("/api/projects", json={
            "name": "Sans contexte", "path": str(project_dir), "type": "web"
        })
        assert response.json()["has_projet_contexte"] is False

    def test_has_projet_contexte_true_avec_fichier(self, client_with_temp_db, tmp_path):
        project_dir = tmp_path / "avec_contexte"
        project_dir.mkdir()
        (project_dir / "PROJET_CONTEXTE.md").write_text("# Mon projet")
        response = client_with_temp_db.post("/api/projects", json={
            "name": "Avec contexte", "path": str(project_dir), "type": "web"
        })
        assert response.json()["has_projet_contexte"] is True


class TestGetProject:

    def test_get_projet_existant(self, client_with_temp_db, tmp_path):
        project_dir = tmp_path / "projet_get"
        project_dir.mkdir()
        created = client_with_temp_db.post("/api/projects", json={
            "name": "Get Test", "path": str(project_dir), "type": "web"
        }).json()

        response = client_with_temp_db.get(f"/api/projects/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_404_pour_projet_inconnu(self, client_with_temp_db):
        response = client_with_temp_db.get("/api/projects/99999")
        assert response.status_code == 404

    def test_pas_de_session_active_au_debut(self, client_with_temp_db, tmp_path):
        project_dir = tmp_path / "projet_no_session"
        project_dir.mkdir()
        created = client_with_temp_db.post("/api/projects", json={
            "name": "No session", "path": str(project_dir), "type": "web"
        }).json()

        data = client_with_temp_db.get(f"/api/projects/{created['id']}").json()
        assert "active_session" not in data or data.get("active_session") is None


class TestDeleteProject:

    def test_supprime_projet(self, client_with_temp_db, tmp_path):
        project_dir = tmp_path / "projet_delete"
        project_dir.mkdir()
        created = client_with_temp_db.post("/api/projects", json={
            "name": "À supprimer", "path": str(project_dir), "type": "web"
        }).json()

        response = client_with_temp_db.delete(f"/api/projects/{created['id']}")
        assert response.status_code == 200

        # Le projet ne doit plus être dans la liste
        projects = client_with_temp_db.get("/api/projects").json()
        ids = [p["id"] for p in projects]
        assert created["id"] not in ids


class TestProjectLocalPath:

    def test_create_project_avec_local_path(self, client_with_temp_db, tmp_path):
        """Création projet avec local_path → local_path présent."""
        project_dir = tmp_path / "projet_local"
        project_dir.mkdir()
        local_dir = tmp_path / "local_folder"
        local_dir.mkdir()
        
        response = client_with_temp_db.post("/api/projects", json={
            "name": "Projet Local",
            "path": str(project_dir),
            "type": "web",
            "local_path": str(local_dir)
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["local_path"] == str(local_dir)

    def test_patch_project_local_path(self, client_with_temp_db, tmp_path):
        """PATCH /projects/{id} avec local_path → met à jour."""
        project_dir = tmp_path / "projet_patch"
        project_dir.mkdir()
        
        created = client_with_temp_db.post("/api/projects", json={
            "name": "Patch Test",
            "path": str(project_dir),
            "type": "web"
        }).json()
        
        local_dir = tmp_path / "new_local"
        local_dir.mkdir()
        
        response = client_with_temp_db.patch(
            f"/api/projects/{created['id']}?local_path={str(local_dir)}"
        )
        
        assert response.status_code == 200
        assert response.json()["local_path"] == str(local_dir)
        
        # Vérifier que GET retourne bien le local_path
        project_data = client_with_temp_db.get(f"/api/projects/{created['id']}").json()
        assert project_data["local_path"] == str(local_dir)

    def test_conversation_herite_folder_path_du_projet(self, client_with_temp_db, tmp_path):
        """Conversation créée avec project_id hérite du local_path."""
        project_dir = tmp_path / "projet_conv"
        project_dir.mkdir()
        local_dir = tmp_path / "local_conv"
        local_dir.mkdir()
        
        # Créer projet avec local_path
        project = client_with_temp_db.post("/api/projects", json={
            "name": "Projet Conv",
            "path": str(project_dir),
            "type": "web",
            "local_path": str(local_dir)
        }).json()
        
        # Créer conversation avec project_id
        conv_response = client_with_temp_db.post("/api/chat/conversations", json={
            "project_id": project["id"],
            "title": "Test Conv"
        })
        
        assert conv_response.status_code == 200
        conv_data = conv_response.json()
        # La conversation doit hériter du local_path du projet
        assert conv_data["folder_path"] == str(local_dir)
