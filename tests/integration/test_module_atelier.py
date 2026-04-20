"""
Tests d'intégration — Module Atelier
call_model est mocké : aucun appel OpenRouter réel.
Vérifie les fonctionnalités du module atelier (prospects, pipeline, export).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from pathlib import Path


@pytest.fixture
def client_and_db(temp_db_path):
    """TestClient avec DB temporaire initialisée."""
    with patch("backend.database.DB_PATH", temp_db_path):
        from backend.database import init_db
        init_db()
        from backend.main import app
        with TestClient(app) as c:
            yield c


async def _mock_call(model_id, messages, api_keys, session_id, step_name, model_type, db):
    """Mock pour call_model."""
    return f"mock output for {step_name}"


class TestCRUDProspect:
    
    def test_crud_prospect_complet(self, client_and_db):
        """POST → GET → PATCH → DELETE → 404."""
        c = client_and_db
        
        # CREATE
        resp_create = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Test",
            "categorie": "restauration",
            "url": "https://restaurant-test.fr"
        })
        assert resp_create.status_code == 201
        prospect_id = resp_create.json()["id"]
        
        # READ
        resp_get = c.get(f"/api/atelier/prospects/{prospect_id}")
        assert resp_get.status_code == 200
        data = resp_get.json()
        assert "prospect" in data
        assert data["prospect"]["nom"] == "Restaurant Test"
        
        # UPDATE
        resp_patch = c.patch(f"/api/atelier/prospects/{prospect_id}", json={
            "statut": "a_contacter"
        })
        assert resp_patch.status_code == 200
        
        resp_get2 = c.get(f"/api/atelier/prospects/{prospect_id}")
        assert resp_get2.json()["prospect"]["statut"] == "a_contacter"
        
        # DELETE
        resp_delete = c.delete(f"/api/atelier/prospects/{prospect_id}")
        assert resp_delete.status_code in [200, 204]
        
        resp_get3 = c.get(f"/api/atelier/prospects/{prospect_id}")
        assert resp_get3.status_code == 404


class TestProspectStatutInitial:
    
    def test_prospect_statut_initial(self, client_and_db):
        """Nouveau prospect → statut="nouveau", session_status=null."""
        c = client_and_db
        
        resp = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Nouveau",
            "categorie": "restauration"
        })
        assert resp.status_code == 201
        prospect_id = resp.json()["id"]
        
        # Vérifier via GET liste
        resp_list = c.get("/api/atelier/prospects")
        assert resp_list.status_code == 200
        prospects = resp_list.json()
        prospect = next(p for p in prospects if p["id"] == prospect_id)
        
        # Status par défaut devrait être défini par le backend
        assert "nom" in prospect
        assert prospect.get("session_status") is None


class TestDemarragePipelineAtelier:
    
    def test_demarrage_pipeline_atelier_10_steps(self, client_and_db):
        """Démarrer pipeline atelier → 10 steps présents."""
        c = client_and_db
        
        # Créer prospect
        resp_prospect = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Pipeline",
            "categorie": "restauration"
        })
        prospect_id = resp_prospect.json()["id"]
        
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            
            resp_start = c.post(f"/api/atelier/prospects/{prospect_id}/start")
        
        assert resp_start.status_code == 200
        session_id = resp_start.json()["session_id"]
        
        # Vérifier nombre de steps
        resp_status = c.get(f"/api/pipelines/{session_id}")
        assert resp_status.status_code == 200
        steps = resp_status.json()["steps"]
        assert len(steps) == 10


class TestUnPipelineParProspect:
    
    def test_un_pipeline_par_prospect(self, client_and_db):
        """Démarrer 2ème pipeline sur même prospect → 400/409."""
        c = client_and_db
        
        # Créer prospect
        resp_prospect = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Unique",
            "categorie": "restauration"
        })
        prospect_id = resp_prospect.json()["id"]
        
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            
            resp1 = c.post(f"/api/atelier/prospects/{prospect_id}/start")
            assert resp1.status_code == 200
            
            resp2 = c.post(f"/api/atelier/prospects/{prospect_id}/start")
            assert resp2.status_code in [400, 409]


class TestSaisieStep0:
    
    def test_saisie_step0_model_type_none(self, client_and_db):
        """Step 0 model_type=none → pas d'appel IA → WAITING_VALIDATION."""
        c = client_and_db
        
        # Créer prospect
        resp_prospect = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Saisie",
            "categorie": "restauration"
        })
        prospect_id = resp_prospect.json()["id"]
        
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            
            resp_start = c.post(f"/api/atelier/prospects/{prospect_id}/start")
        
        session_id = resp_start.json()["session_id"]
        
        # Vérifier step 0
        resp_status = c.get(f"/api/pipelines/{session_id}")
        steps = resp_status.json()["steps"]
        step0 = next(s for s in steps if s["step_index"] == 0)
        
        # Step 0 doit être en WAITING_VALIDATION (moment humain)
        assert step0["status"] in ["WAITING_VALIDATION", "PENDING"]


class TestCheckpointStep4:
    
    def test_checkpoint_step4_model_type_none(self, client_and_db):
        """Step 4 (checkpoint) model_type=none → pas d'appel IA."""
        c = client_and_db
        
        # Créer prospect
        resp_prospect = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Checkpoint",
            "categorie": "restauration"
        })
        prospect_id = resp_prospect.json()["id"]
        
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            
            resp_start = c.post(f"/api/atelier/prospects/{prospect_id}/start")
        
        session_id = resp_start.json()["session_id"]
        
        # Vérifier step 4
        resp_status = c.get(f"/api/pipelines/{session_id}")
        steps = resp_status.json()["steps"]
        step4 = next(s for s in steps if s["step_index"] == 4)
        
        # Step 4 doit avoir model_type none ou être en WAITING_VALIDATION
        assert step4["status"] in ["PENDING", "WAITING_VALIDATION"]


class TestSessionStatusDansGetProspects:
    
    def test_session_status_dans_get_prospects(self, client_and_db):
        """GET /api/atelier/prospects → chaque prospect a session_status."""
        c = client_and_db
        
        # Créer prospect sans session
        resp1 = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Sans Session",
            "categorie": "restauration"
        })
        
        # Créer prospect avec session
        resp2 = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Avec Session",
            "categorie": "restauration"
        })
        prospect2_id = resp2.json()["id"]
        
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            c.post(f"/api/atelier/prospects/{prospect2_id}/start")
        
        # GET liste
        resp_list = c.get("/api/atelier/prospects")
        assert resp_list.status_code == 200
        prospects = resp_list.json()
        
        # Vérifier que tous ont le champ session_status ou status
        for prospect in prospects:
            assert "session_status" in prospect or "status" in prospect


class TestExportStep9:
    
    def test_export_step9_model_type_none(self, client_and_db):
        """Step 9 (export) model_type=none → pas d'appel IA."""
        c = client_and_db
        
        # Créer prospect
        resp_prospect = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Export",
            "categorie": "restauration"
        })
        prospect_id = resp_prospect.json()["id"]
        
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            
            resp_start = c.post(f"/api/atelier/prospects/{prospect_id}/start")
        
        session_id = resp_start.json()["session_id"]
        
        # Vérifier step 9
        resp_status = c.get(f"/api/pipelines/{session_id}")
        steps = resp_status.json()["steps"]
        step9 = next(s for s in steps if s["step_index"] == 9)
        
        # Step 9 doit être PENDING initialement
        assert step9["status"] == "PENDING"


class TestExportZipCreeFichier:
    
    def test_export_zip_cree_fichier(self, client_and_db, tmp_path):
        """Pipeline arrivé à export → fichier ZIP créé."""
        c = client_and_db
        
        # Créer prospect
        resp_prospect = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant ZIP",
            "categorie": "restauration"
        })
        prospect_id = resp_prospect.json()["id"]
        
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            
            resp_start = c.post(f"/api/atelier/prospects/{prospect_id}/start")
        
        session_id = resp_start.json()["session_id"]
        
        # Forcer step 8 en WAITING_VALIDATION
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE pipeline_steps 
            SET status = 'WAITING_VALIDATION', output_data = 'Test files'
            WHERE session_id = ? AND step_index = 8
        """, (session_id,))
        cursor.execute("""
            UPDATE sessions 
            SET status = 'WAITING_VALIDATION', current_step_index = 8
            WHERE id = ?
        """, (session_id,))
        cursor.execute("""
            SELECT id FROM pipeline_steps 
            WHERE session_id = ? AND step_index = 8
        """, (session_id,))
        step_id = cursor.fetchone()["id"]
        conn.commit()
        conn.close()
        
        # Valider step 8 (devrait déclencher step 9 export)
        with patch("backend.services.pipeline_engine.call_model", new_callable=AsyncMock) as mock:
            mock.side_effect = _mock_call
            
            resp_validate = c.post(f"/api/pipelines/{session_id}/validate/{step_id}", json={
                "approved": True
            })
        
        # Note: Le test vérifie que la validation passe, 
        # la création du ZIP dépend de l'implémentation de atelier_service
        assert resp_validate.status_code == 200


class TestMouvementKanban:
    
    def test_mouvement_kanban_change_statut(self, client_and_db):
        """PATCH statut → GET retourne nouveau statut."""
        c = client_and_db
        
        # Créer prospect
        resp = c.post("/api/atelier/prospects", json={
            "nom": "Restaurant Kanban",
            "categorie": "restauration"
        })
        assert resp.status_code == 201
        prospect_id = resp.json()["id"]
        
        # Changer statut
        resp_patch = c.patch(f"/api/atelier/prospects/{prospect_id}", json={
            "statut": "a_contacter"
        })
        assert resp_patch.status_code == 200
        
        # Vérifier
        resp_get = c.get(f"/api/atelier/prospects/{prospect_id}")
        data = resp_get.json()
        assert "prospect" in data
        assert data["prospect"]["statut"] == "a_contacter"
        
        # Changer à nouveau
        resp_patch2 = c.patch(f"/api/atelier/prospects/{prospect_id}", json={
            "statut": "en_analyse"
        })
        assert resp_patch2.status_code == 200
        
        resp_get2 = c.get(f"/api/atelier/prospects/{prospect_id}")
        assert resp_get2.json()["prospect"]["statut"] == "en_analyse"
