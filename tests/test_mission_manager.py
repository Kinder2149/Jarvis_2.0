"""
Tests unitaires pour MissionManager
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from backend.services.mission_manager import MissionManager
from backend.models.mission import Mission, MissionStatus


class TestMissionManagerCreation:
    """Tests de création de missions"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MissionManager(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_mission_minimal(self):
        """Test création mission avec paramètres minimaux"""
        mission = self.manager.create_mission(
            mission_id="test_001",
            user_request="Test request",
            project_path="/test/path"
        )
        
        assert mission.mission_id == "test_001"
        assert mission.user_request == "Test request"
        assert mission.project_path == "/test/path"
        assert mission.status == MissionStatus.PENDING
    
    def test_create_mission_auto_id(self):
        """Test création mission avec ID fourni"""
        import uuid
        mission_id = f"test_{uuid.uuid4().hex[:8]}"
        
        mission = self.manager.create_mission(
            mission_id=mission_id,
            user_request="Test request",
            project_path="/test/path"
        )
        
        assert mission.mission_id == mission_id
        assert len(mission.mission_id) > 0
    
    def test_create_mission_saves_to_storage(self):
        """Test que create_mission sauvegarde dans storage"""
        mission = self.manager.create_mission(
            mission_id="test_002",
            user_request="Test",
            project_path="/test"
        )
        
        # Vérifier que le fichier existe (chemin peut varier selon storage_path)
        assert self.manager.storage_path.exists()
        
        # Vérifier que la mission est dans le storage
        retrieved = self.manager.get_mission("test_002")
        assert retrieved is not None
        assert retrieved.mission_id == "test_002"


class TestMissionManagerRetrieval:
    """Tests de récupération de missions"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MissionManager(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_get_mission_exists(self):
        """Test get_mission() retourne mission existante"""
        created = self.manager.create_mission(
            mission_id="test_003",
            user_request="Test",
            project_path="/test"
        )
        
        retrieved = self.manager.get_mission("test_003")
        
        assert retrieved is not None
        assert retrieved.mission_id == created.mission_id
        assert retrieved.user_request == created.user_request
    
    def test_get_mission_not_exists(self):
        """Test get_mission() retourne None si mission inexistante"""
        retrieved = self.manager.get_mission("nonexistent")
        assert retrieved is None
    
    def test_list_missions_empty(self):
        """Test list_missions() retourne liste vide si aucune mission"""
        missions = self.manager.list_missions()
        assert isinstance(missions, list)
        assert len(missions) == 0
    
    def test_list_missions_multiple(self):
        """Test list_missions() retourne toutes les missions"""
        self.manager.create_mission("test_004", "Request 1", "/test1")
        self.manager.create_mission("test_005", "Request 2", "/test2")
        self.manager.create_mission("test_006", "Request 3", "/test3")
        
        missions = self.manager.list_missions()
        
        assert len(missions) == 3
        mission_ids = [m.mission_id for m in missions]
        assert "test_004" in mission_ids
        assert "test_005" in mission_ids
        assert "test_006" in mission_ids


class TestMissionManagerUpdate:
    """Tests de mise à jour de missions"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MissionManager(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_update_mission_status(self):
        """Test update_mission() met à jour le statut"""
        mission = self.manager.create_mission(
            mission_id="test_007",
            user_request="Test",
            project_path="/test"
        )
        
        mission.status = MissionStatus.IN_PROGRESS
        self.manager.update_mission(mission)
        
        retrieved = self.manager.get_mission("test_007")
        assert retrieved.status == MissionStatus.IN_PROGRESS
    
    def test_update_mission_files(self):
        """Test update_mission() met à jour les fichiers"""
        mission = self.manager.create_mission(
            mission_id="test_008",
            user_request="Test",
            project_path="/test"
        )
        
        mission.files_created = ["file1.py", "file2.py"]
        mission.files_modified = ["main.py"]
        self.manager.update_mission(mission)
        
        retrieved = self.manager.get_mission("test_008")
        assert len(retrieved.files_created) == 2
        assert len(retrieved.files_modified) == 1
    
    def test_update_mission_validation_flags(self):
        """Test update_mission() met à jour les flags de validation"""
        mission = self.manager.create_mission(
            mission_id="test_009",
            user_request="Test",
            project_path="/test"
        )
        
        mission.architecture_validated = True
        mission.code_validated = True
        mission.tests_validated = False
        self.manager.update_mission(mission)
        
        retrieved = self.manager.get_mission("test_009")
        assert retrieved.architecture_validated is True
        assert retrieved.code_validated is True
        assert retrieved.tests_validated is False


class TestMissionManagerDelete:
    """Tests de suppression de missions"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MissionManager(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_delete_mission_exists(self):
        """Test delete_mission() supprime mission existante"""
        self.manager.create_mission(
            mission_id="test_010",
            user_request="Test",
            project_path="/test"
        )
        
        result = self.manager.delete_mission("test_010")
        
        assert result is True
        assert self.manager.get_mission("test_010") is None
    
    def test_delete_mission_not_exists(self):
        """Test delete_mission() retourne False si mission inexistante"""
        result = self.manager.delete_mission("nonexistent")
        assert result is False
    
    def test_delete_mission_updates_storage(self):
        """Test delete_mission() met à jour le storage"""
        self.manager.create_mission("test_011", "Test 1", "/test1")
        self.manager.create_mission("test_012", "Test 2", "/test2")
        
        self.manager.delete_mission("test_011")
        
        missions = self.manager.list_missions()
        assert len(missions) == 1
        assert missions[0].mission_id == "test_012"


class TestMissionManagerFilters:
    """Tests des méthodes de filtrage (bonus)"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MissionManager(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_get_missions_by_status(self):
        """Test get_missions_by_status() filtre correctement"""
        m1 = self.manager.create_mission("test_013", "Test 1", "/test1")
        m2 = self.manager.create_mission("test_014", "Test 2", "/test2")
        m3 = self.manager.create_mission("test_015", "Test 3", "/test3")
        
        m2.status = MissionStatus.IN_PROGRESS
        self.manager.update_mission(m2)
        
        m3.status = MissionStatus.COMPLETED
        self.manager.update_mission(m3)
        
        pending = self.manager.get_missions_by_status(MissionStatus.PENDING)
        in_progress = self.manager.get_missions_by_status(MissionStatus.IN_PROGRESS)
        completed = self.manager.get_missions_by_status(MissionStatus.COMPLETED)
        
        assert len(pending) == 1
        assert len(in_progress) == 1
        assert len(completed) == 1
        assert pending[0].mission_id == "test_013"
        assert in_progress[0].mission_id == "test_014"
        assert completed[0].mission_id == "test_015"
    
    def test_get_active_missions(self):
        """Test get_active_missions() retourne missions actives"""
        m1 = self.manager.create_mission("test_016", "Test 1", "/test1")
        m2 = self.manager.create_mission("test_017", "Test 2", "/test2")
        m3 = self.manager.create_mission("test_018", "Test 3", "/test3")
        
        m2.status = MissionStatus.IN_PROGRESS
        self.manager.update_mission(m2)
        
        m3.status = MissionStatus.COMPLETED
        self.manager.update_mission(m3)
        
        active = self.manager.get_active_missions()
        
        assert len(active) == 2
        active_ids = [m.mission_id for m in active]
        assert "test_016" in active_ids  # PENDING
        assert "test_017" in active_ids  # IN_PROGRESS
        assert "test_018" not in active_ids  # COMPLETED


class TestMissionManagerPersistence:
    """Tests de persistance du storage"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_persistence_across_instances(self):
        """Test que les missions persistent entre instances"""
        # Créer fichier storage dans temp_dir
        storage_file = Path(self.temp_dir) / "missions.json"
        
        # Créer missions avec première instance
        manager1 = MissionManager(storage_path=str(storage_file))
        manager1.create_mission("test_019", "Test 1", "/test1")
        manager1.create_mission("test_020", "Test 2", "/test2")
        
        # Créer nouvelle instance et vérifier missions chargées
        manager2 = MissionManager(storage_path=str(storage_file))
        missions = manager2.list_missions()
        
        assert len(missions) == 2
        mission_ids = [m.mission_id for m in missions]
        assert "test_019" in mission_ids
        assert "test_020" in mission_ids
