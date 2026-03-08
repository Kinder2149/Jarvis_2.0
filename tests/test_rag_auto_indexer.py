"""
Tests unitaires pour RAGAutoIndexer
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from backend.services.rag_auto_indexer import RAGAutoIndexer


class TestProjectHash:
    """Tests de génération de hash projet"""
    
    def test_generate_project_hash_consistent(self):
        """Test que le hash est consistant pour le même chemin"""
        indexer = RAGAutoIndexer()
        
        hash1 = indexer._generate_project_hash("/test/path")
        hash2 = indexer._generate_project_hash("/test/path")
        
        assert hash1 == hash2
    
    def test_generate_project_hash_different_paths(self):
        """Test que des chemins différents génèrent des hash différents"""
        indexer = RAGAutoIndexer()
        
        hash1 = indexer._generate_project_hash("/test/path1")
        hash2 = indexer._generate_project_hash("/test/path2")
        
        assert hash1 != hash2
    
    def test_generate_project_hash_normalized(self):
        """Test que les chemins sont normalisés"""
        indexer = RAGAutoIndexer()
        
        hash1 = indexer._generate_project_hash("/test/path")
        hash2 = indexer._generate_project_hash("/test/path/")
        hash3 = indexer._generate_project_hash("/test//path")
        
        # Tous devraient être identiques après normalisation
        assert hash1 == hash2 == hash3
    
    def test_generate_project_hash_length(self):
        """Test que le hash a la longueur attendue (12 caractères)"""
        indexer = RAGAutoIndexer()
        
        project_hash = indexer._generate_project_hash("/test/path")
        
        assert len(project_hash) == 12


class TestProjectIndexing:
    """Tests d'indexation de projets"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.indexer = RAGAutoIndexer(rag_projects_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_is_project_indexed_false_initially(self):
        """Test qu'un projet n'est pas indexé initialement"""
        assert self.indexer.is_project_indexed("/test/path") is False
    
    def test_index_completed_mission_creates_directory(self):
        """Test que l'indexation crée le dossier projet"""
        result = self.indexer.index_completed_mission(
            mission_id="test_001",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test request",
            files_created=["test.py"]
        )
        
        project_dir = Path(self.temp_dir) / "test_project"
        assert project_dir.exists()
        assert project_dir.is_dir()
    
    def test_index_completed_mission_creates_metadata(self):
        """Test que l'indexation crée metadata.json"""
        result = self.indexer.index_completed_mission(
            mission_id="test_002",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test request",
            files_created=["test.py", "main.py"]
        )
        
        metadata_file = Path(self.temp_dir) / "test_project" / "metadata.json"
        assert metadata_file.exists()
        
        metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
        assert metadata["mission_id"] == "test_002"
        assert metadata["project_name"] == "test_project"
        assert metadata["user_request"] == "Test request"
        assert len(metadata["files_created"]) == 2
        assert metadata["status"] == "completed"
    
    def test_index_completed_mission_creates_architecture(self):
        """Test que l'indexation crée architecture.md si fourni"""
        arch_doc = "# Architecture\n\nTest architecture"
        
        result = self.indexer.index_completed_mission(
            mission_id="test_003",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test",
            files_created=["test.py"],
            architecture_doc=arch_doc
        )
        
        arch_file = Path(self.temp_dir) / "test_project" / "architecture.md"
        assert arch_file.exists()
        assert arch_file.read_text(encoding='utf-8') == arch_doc
    
    def test_index_completed_mission_creates_lessons_learned(self):
        """Test que l'indexation crée lessons_learned.md"""
        result = self.indexer.index_completed_mission(
            mission_id="test_004",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test request",
            files_created=["test.py"]
        )
        
        lessons_file = Path(self.temp_dir) / "test_project" / "lessons_learned.md"
        assert lessons_file.exists()
        
        content = lessons_file.read_text(encoding='utf-8')
        assert "test_project" in content
        assert "test_004" in content
        assert "Test request" in content
    
    def test_index_completed_mission_returns_success(self):
        """Test que l'indexation retourne success=True"""
        result = self.indexer.index_completed_mission(
            mission_id="test_005",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test",
            files_created=["test.py"]
        )
        
        assert result["success"] is True
        assert "project_hash" in result
        assert "indexed_at" in result
        assert "rag_path" in result
    
    def test_index_completed_mission_updates_index(self):
        """Test que l'indexation met à jour index.json"""
        self.indexer.index_completed_mission(
            mission_id="test_006",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test",
            files_created=["test.py"]
        )
        
        index_file = Path(self.temp_dir) / "index.json"
        assert index_file.exists()
        
        index_data = json.loads(index_file.read_text(encoding='utf-8'))
        assert len(index_data["projects"]) == 1
        assert index_data["projects"][0]["name"] == "test_project"
        assert index_data["projects"][0]["mission_id"] == "test_006"


class TestAntiDuplication:
    """Tests anti-doublon"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.indexer = RAGAutoIndexer(rag_projects_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_is_project_indexed_true_after_indexing(self):
        """Test qu'un projet est détecté comme indexé après indexation"""
        self.indexer.index_completed_mission(
            mission_id="test_007",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test",
            files_created=["test.py"]
        )
        
        assert self.indexer.is_project_indexed("/test/path") is True
    
    def test_index_same_project_twice_updates(self):
        """Test que ré-indexer le même projet met à jour au lieu de dupliquer"""
        # Première indexation
        result1 = self.indexer.index_completed_mission(
            mission_id="test_008",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test 1",
            files_created=["test.py"]
        )
        
        # Deuxième indexation même projet
        result2 = self.indexer.index_completed_mission(
            mission_id="test_009",
            project_path="/test/path",
            project_name="test_project",
            user_request="Test 2",
            files_created=["test.py", "main.py"]
        )
        
        # Vérifier qu'il n'y a qu'une seule entrée dans l'index
        index_data = self.indexer._load_index()
        assert len(index_data["projects"]) == 1
        
        # Vérifier que c'est la dernière mission
        assert index_data["projects"][0]["mission_id"] == "test_009"
        assert result2["is_update"] is True
    
    def test_different_projects_both_indexed(self):
        """Test que des projets différents sont tous indexés"""
        self.indexer.index_completed_mission(
            mission_id="test_010",
            project_path="/test/path1",
            project_name="project1",
            user_request="Test 1",
            files_created=["test1.py"]
        )
        
        self.indexer.index_completed_mission(
            mission_id="test_011",
            project_path="/test/path2",
            project_name="project2",
            user_request="Test 2",
            files_created=["test2.py"]
        )
        
        index_data = self.indexer._load_index()
        assert len(index_data["projects"]) == 2


class TestIndexManagement:
    """Tests de gestion de l'index"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.indexer = RAGAutoIndexer(rag_projects_path=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_get_indexed_projects_empty(self):
        """Test get_indexed_projects() retourne liste vide si aucun projet"""
        projects = self.indexer.get_indexed_projects()
        assert isinstance(projects, list)
        assert len(projects) == 0
    
    def test_get_indexed_projects_returns_all(self):
        """Test get_indexed_projects() retourne tous les projets"""
        self.indexer.index_completed_mission(
            "test_012", "/path1", "project1", "Test 1", ["test1.py"]
        )
        self.indexer.index_completed_mission(
            "test_013", "/path2", "project2", "Test 2", ["test2.py"]
        )
        
        projects = self.indexer.get_indexed_projects()
        assert len(projects) == 2
    
    def test_get_project_by_hash_exists(self):
        """Test get_project_by_hash() retourne projet existant"""
        result = self.indexer.index_completed_mission(
            "test_014", "/test/path", "test_project", "Test", ["test.py"]
        )
        
        project_hash = result["project_hash"]
        project = self.indexer.get_project_by_hash(project_hash)
        
        assert project is not None
        assert project["name"] == "test_project"
        assert project["mission_id"] == "test_014"
    
    def test_get_project_by_hash_not_exists(self):
        """Test get_project_by_hash() retourne None si inexistant"""
        project = self.indexer.get_project_by_hash("nonexistent_hash")
        assert project is None
    
    def test_remove_project_from_index_exists(self):
        """Test remove_project_from_index() supprime projet existant"""
        result = self.indexer.index_completed_mission(
            "test_015", "/test/path", "test_project", "Test", ["test.py"]
        )
        
        project_hash = result["project_hash"]
        removed = self.indexer.remove_project_from_index(project_hash)
        
        assert removed is True
        assert self.indexer.get_project_by_hash(project_hash) is None
    
    def test_remove_project_from_index_not_exists(self):
        """Test remove_project_from_index() retourne False si inexistant"""
        removed = self.indexer.remove_project_from_index("nonexistent_hash")
        assert removed is False
    
    def test_remove_project_updates_index(self):
        """Test remove_project_from_index() met à jour l'index"""
        result1 = self.indexer.index_completed_mission(
            "test_016", "/path1", "project1", "Test 1", ["test1.py"]
        )
        result2 = self.indexer.index_completed_mission(
            "test_017", "/path2", "project2", "Test 2", ["test2.py"]
        )
        
        self.indexer.remove_project_from_index(result1["project_hash"])
        
        projects = self.indexer.get_indexed_projects()
        assert len(projects) == 1
        assert projects[0]["name"] == "project2"


class TestIndexPersistence:
    """Tests de persistance de l'index"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_index_persists_across_instances(self):
        """Test que l'index persiste entre instances"""
        # Créer projets avec première instance
        indexer1 = RAGAutoIndexer(rag_projects_path=self.temp_dir)
        indexer1.index_completed_mission(
            "test_018", "/path1", "project1", "Test 1", ["test1.py"]
        )
        indexer1.index_completed_mission(
            "test_019", "/path2", "project2", "Test 2", ["test2.py"]
        )
        
        # Créer nouvelle instance et vérifier projets chargés
        indexer2 = RAGAutoIndexer(rag_projects_path=self.temp_dir)
        projects = indexer2.get_indexed_projects()
        
        assert len(projects) == 2
        project_names = [p["name"] for p in projects]
        assert "project1" in project_names
        assert "project2" in project_names
    
    def test_index_file_created_automatically(self):
        """Test que le fichier index.json est créé automatiquement"""
        indexer = RAGAutoIndexer(rag_projects_path=self.temp_dir)
        
        index_file = Path(self.temp_dir) / "index.json"
        assert index_file.exists()
