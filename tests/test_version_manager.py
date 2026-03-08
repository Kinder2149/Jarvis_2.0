"""
Tests unitaires pour VersionManager
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from backend.services.version_manager import VersionManager


class TestVersionRetrieval:
    """Tests de récupération de version"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = VersionManager()
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_get_project_version_default(self):
        """Test get_project_version() retourne version par défaut si fichier inexistant"""
        version = self.manager.get_project_version(self.temp_dir)
        assert version == "0.1.0"
    
    def test_get_project_version_from_file(self):
        """Test get_project_version() lit version depuis fichier"""
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        version_file.write_text(
            json.dumps({"version": "1.2.3"}),
            encoding='utf-8'
        )
        
        version = self.manager.get_project_version(self.temp_dir)
        assert version == "1.2.3"
    
    def test_get_project_version_handles_corrupt_file(self):
        """Test get_project_version() gère fichier corrompu"""
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        version_file.write_text("invalid json", encoding='utf-8')
        
        version = self.manager.get_project_version(self.temp_dir)
        assert version == "0.1.0"
    
    def test_get_project_version_handles_missing_version_key(self):
        """Test get_project_version() gère clé version manquante"""
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        version_file.write_text(
            json.dumps({"mission_id": "test"}),
            encoding='utf-8'
        )
        
        version = self.manager.get_project_version(self.temp_dir)
        assert version == "0.1.0"


class TestVersionIncrement:
    """Tests d'incrémentation de version"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.manager = VersionManager()
    
    def test_increment_version_major(self):
        """Test increment_version() pour MAJOR"""
        assert self.manager.increment_version("1.2.3", "major") == "2.0.0"
        assert self.manager.increment_version("0.1.0", "major") == "1.0.0"
        assert self.manager.increment_version("5.10.20", "major") == "6.0.0"
    
    def test_increment_version_minor(self):
        """Test increment_version() pour MINOR"""
        assert self.manager.increment_version("1.2.3", "minor") == "1.3.0"
        assert self.manager.increment_version("0.1.0", "minor") == "0.2.0"
        assert self.manager.increment_version("5.10.20", "minor") == "5.11.0"
    
    def test_increment_version_patch(self):
        """Test increment_version() pour PATCH"""
        assert self.manager.increment_version("1.2.3", "patch") == "1.2.4"
        assert self.manager.increment_version("0.1.0", "patch") == "0.1.1"
        assert self.manager.increment_version("5.10.20", "patch") == "5.10.21"
    
    def test_increment_version_default_to_minor(self):
        """Test increment_version() utilise MINOR par défaut"""
        assert self.manager.increment_version("1.2.3", "unknown") == "1.3.0"
        assert self.manager.increment_version("1.2.3", "") == "1.3.0"
    
    def test_increment_version_handles_invalid_version(self):
        """Test increment_version() gère version invalide"""
        result = self.manager.increment_version("invalid", "minor")
        assert result == "0.2.0"  # Reset à 0.1.0 puis incrémente


class TestVersionSave:
    """Tests de sauvegarde de version"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = VersionManager()
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_save_version_creates_file(self):
        """Test save_version() crée le fichier"""
        self.manager.save_version(
            self.temp_dir,
            "1.0.0",
            "test_mission_001"
        )
        
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        assert version_file.exists()
    
    def test_save_version_saves_all_fields(self):
        """Test save_version() sauvegarde tous les champs"""
        self.manager.save_version(
            self.temp_dir,
            "1.2.3",
            "test_mission_002",
            ["file1.py", "file2.py"]
        )
        
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        data = json.loads(version_file.read_text(encoding='utf-8'))
        
        assert data["version"] == "1.2.3"
        assert data["mission_id"] == "test_mission_002"
        assert "updated_at" in data
        assert data["files_modified"] == ["file1.py", "file2.py"]
        assert data["created_by"] == "JARVIS 2.0"
    
    def test_save_version_handles_no_files(self):
        """Test save_version() gère absence de fichiers modifiés"""
        self.manager.save_version(
            self.temp_dir,
            "1.0.0",
            "test_mission_003"
        )
        
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        data = json.loads(version_file.read_text(encoding='utf-8'))
        
        assert data["files_modified"] == []
    
    def test_save_version_overwrites_existing(self):
        """Test save_version() écrase fichier existant"""
        # Première sauvegarde
        self.manager.save_version(self.temp_dir, "1.0.0", "mission_001")
        
        # Deuxième sauvegarde
        self.manager.save_version(self.temp_dir, "2.0.0", "mission_002")
        
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        data = json.loads(version_file.read_text(encoding='utf-8'))
        
        assert data["version"] == "2.0.0"
        assert data["mission_id"] == "mission_002"


class TestChangeTypeDetection:
    """Tests de détection de type de changement"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.manager = VersionManager()
    
    def test_detect_change_type_major(self):
        """Test detect_change_type() détecte MAJOR"""
        major_requests = [
            "Refonte complète de l'architecture",
            "Réécrire tout le code",
            "Recommencer from scratch",
            "Changement breaking change important"
        ]
        
        for request in major_requests:
            change_type = self.manager.detect_change_type(request)
            assert change_type == "major", f"'{request}' devrait être major"
    
    def test_detect_change_type_patch(self):
        """Test detect_change_type() détecte PATCH"""
        patch_requests = [
            "Corrige le bug d'authentification",
            "Fix l'erreur de validation",
            "Répare le problème de connexion",
            "Hotfix pour le crash au démarrage",
            "Correction d'une typo dans le code"
        ]
        
        for request in patch_requests:
            change_type = self.manager.detect_change_type(request)
            assert change_type == "patch", f"'{request}' devrait être patch"
    
    def test_detect_change_type_minor(self):
        """Test detect_change_type() détecte MINOR"""
        minor_requests = [
            "Ajoute une nouvelle fonctionnalité",
            "Implémente l'export PDF",
            "Crée un système de notifications",
            "Améliore les performances",
            "Étend l'API avec de nouveaux endpoints"
        ]
        
        for request in minor_requests:
            change_type = self.manager.detect_change_type(request)
            assert change_type == "minor", f"'{request}' devrait être minor"
    
    def test_detect_change_type_default_to_minor(self):
        """Test detect_change_type() utilise MINOR par défaut"""
        neutral_request = "Modifie quelque chose"
        change_type = self.manager.detect_change_type(neutral_request)
        assert change_type == "minor"


class TestVersionHistory:
    """Tests de récupération d'historique"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = VersionManager()
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_get_version_history_no_file(self):
        """Test get_version_history() retourne dict par défaut si pas de fichier"""
        history = self.manager.get_version_history(self.temp_dir)
        
        assert history["version"] == "0.1.0"
        assert history["mission_id"] is None
        assert history["updated_at"] is None
        assert history["files_modified"] == []
    
    def test_get_version_history_from_file(self):
        """Test get_version_history() lit historique depuis fichier"""
        self.manager.save_version(
            self.temp_dir,
            "1.2.3",
            "test_mission",
            ["file1.py", "file2.py"]
        )
        
        history = self.manager.get_version_history(self.temp_dir)
        
        assert history["version"] == "1.2.3"
        assert history["mission_id"] == "test_mission"
        assert history["updated_at"] is not None
        assert len(history["files_modified"]) == 2
    
    def test_get_version_history_handles_corrupt_file(self):
        """Test get_version_history() gère fichier corrompu"""
        version_file = Path(self.temp_dir) / ".jarvis_version.json"
        version_file.write_text("invalid json", encoding='utf-8')
        
        history = self.manager.get_version_history(self.temp_dir)
        
        assert history["version"] == "0.1.0"
        assert history["mission_id"] is None


class TestVersionWorkflow:
    """Tests de workflow complet de versioning"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = VersionManager()
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        shutil.rmtree(self.temp_dir)
    
    def test_workflow_initial_version(self):
        """Test workflow : version initiale"""
        # Récupérer version (devrait être 0.1.0)
        current = self.manager.get_project_version(self.temp_dir)
        assert current == "0.1.0"
        
        # Sauvegarder version initiale
        self.manager.save_version(self.temp_dir, current, "mission_001")
        
        # Vérifier sauvegarde
        saved = self.manager.get_project_version(self.temp_dir)
        assert saved == "0.1.0"
    
    def test_workflow_minor_update(self):
        """Test workflow : mise à jour MINOR"""
        # Version initiale
        self.manager.save_version(self.temp_dir, "0.1.0", "mission_001")
        
        # Détecter type changement
        change_type = self.manager.detect_change_type("Ajoute nouvelle feature")
        assert change_type == "minor"
        
        # Incrémenter version
        current = self.manager.get_project_version(self.temp_dir)
        new_version = self.manager.increment_version(current, change_type)
        assert new_version == "0.2.0"
        
        # Sauvegarder nouvelle version
        self.manager.save_version(self.temp_dir, new_version, "mission_002")
        
        # Vérifier
        assert self.manager.get_project_version(self.temp_dir) == "0.2.0"
    
    def test_workflow_patch_update(self):
        """Test workflow : mise à jour PATCH"""
        # Version initiale
        self.manager.save_version(self.temp_dir, "1.0.0", "mission_001")
        
        # Détecter type changement
        change_type = self.manager.detect_change_type("Corrige bug critique")
        assert change_type == "patch"
        
        # Incrémenter version
        current = self.manager.get_project_version(self.temp_dir)
        new_version = self.manager.increment_version(current, change_type)
        assert new_version == "1.0.1"
        
        # Sauvegarder
        self.manager.save_version(self.temp_dir, new_version, "mission_002")
        
        # Vérifier
        assert self.manager.get_project_version(self.temp_dir) == "1.0.1"
    
    def test_workflow_major_update(self):
        """Test workflow : mise à jour MAJOR"""
        # Version initiale
        self.manager.save_version(self.temp_dir, "1.5.3", "mission_001")
        
        # Détecter type changement
        change_type = self.manager.detect_change_type("Refonte complète")
        assert change_type == "major"
        
        # Incrémenter version
        current = self.manager.get_project_version(self.temp_dir)
        new_version = self.manager.increment_version(current, change_type)
        assert new_version == "2.0.0"
        
        # Sauvegarder
        self.manager.save_version(self.temp_dir, new_version, "mission_002")
        
        # Vérifier
        assert self.manager.get_project_version(self.temp_dir) == "2.0.0"
