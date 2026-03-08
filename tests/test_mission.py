"""
Tests unitaires pour le modèle Mission
"""

import pytest
from datetime import datetime
from backend.models.mission import Mission, MissionStatus, MissionPhase


class TestMissionCreation:
    """Tests de création de mission"""
    
    def test_mission_creation_minimal(self):
        """Test création mission avec paramètres minimaux"""
        mission = Mission(
            mission_id="test_001",
            user_request="Test request",
            project_path="/test/path"
        )
        
        assert mission.mission_id == "test_001"
        assert mission.user_request == "Test request"
        assert mission.project_path == "/test/path"
        assert mission.status == MissionStatus.PENDING
        assert mission.current_phase is None
        assert mission.created_at is not None
        assert mission.completed_at is None
    
    def test_mission_creation_complete(self):
        """Test création mission avec tous les paramètres"""
        mission = Mission(
            mission_id="test_002",
            user_request="Complete test",
            project_path="/test/path",
            status=MissionStatus.IN_PROGRESS,
            current_phase=MissionPhase.GENERATION_CODE,
            files_created=["test.py"],
            files_modified=["main.py"],
            architecture_validated=True,
            code_validated=False,
            tests_validated=False
        )
        
        assert mission.status == MissionStatus.IN_PROGRESS
        assert mission.current_phase == MissionPhase.GENERATION_CODE
        assert len(mission.files_created) == 1
        assert mission.architecture_validated is True
        assert mission.code_validated is False


class TestMissionStatus:
    """Tests des états de mission"""
    
    def test_mission_is_complete_true(self):
        """Test is_complete() retourne True quand mission complète"""
        mission = Mission(
            mission_id="test_003",
            user_request="Test",
            project_path="/test"
        )
        
        mission.architecture_validated = True
        mission.code_validated = True
        mission.tests_validated = True
        mission.files_created = ["test.py"]
        
        assert mission.is_complete() is True
    
    def test_mission_is_complete_false_no_files(self):
        """Test is_complete() retourne False si pas de fichiers"""
        mission = Mission(
            mission_id="test_004",
            user_request="Test",
            project_path="/test"
        )
        
        mission.architecture_validated = True
        mission.code_validated = True
        mission.tests_validated = True
        # files_created vide
        
        assert mission.is_complete() is False
    
    def test_mission_is_complete_false_validation_missing(self):
        """Test is_complete() retourne False si validation manquante"""
        mission = Mission(
            mission_id="test_005",
            user_request="Test",
            project_path="/test"
        )
        
        mission.architecture_validated = True
        mission.code_validated = False  # Manquant
        mission.tests_validated = True
        mission.files_created = ["test.py"]
        
        assert mission.is_complete() is False
    
    def test_mission_mark_completed(self):
        """Test mark_completed() met à jour statut et date"""
        mission = Mission(
            mission_id="test_006",
            user_request="Test",
            project_path="/test"
        )
        
        mission.architecture_validated = True
        mission.code_validated = True
        mission.tests_validated = True
        mission.files_created = ["test.py"]
        
        mission.mark_completed()
        
        assert mission.status == MissionStatus.COMPLETED
        assert mission.current_phase == MissionPhase.FINALISATION
        assert mission.completed_at is not None
    
    def test_mission_mark_failed(self):
        """Test mark_failed() met à jour statut et erreur"""
        mission = Mission(
            mission_id="test_007",
            user_request="Test",
            project_path="/test"
        )
        
        error_msg = "Test error message"
        mission.mark_failed(error_msg)
        
        assert mission.status == MissionStatus.FAILED
        assert mission.error_count == 1
        assert mission.last_error == error_msg
    
    def test_mission_mark_failed_multiple(self):
        """Test mark_failed() incrémente error_count"""
        mission = Mission(
            mission_id="test_008",
            user_request="Test",
            project_path="/test"
        )
        
        mission.mark_failed("Error 1")
        mission.mark_failed("Error 2")
        
        assert mission.error_count == 2
        assert mission.last_error == "Error 2"


class TestMissionValidation:
    """Tests de validation utilisateur"""
    
    def test_request_validation_architecture(self):
        """Test request_validation() pour architecture"""
        mission = Mission(
            mission_id="test_009",
            user_request="Test",
            project_path="/test"
        )
        
        arch_data = {"files": ["test.py"], "structure": "simple"}
        mission.request_validation("architecture", arch_data)
        
        assert mission.status == MissionStatus.VALIDATING
        assert mission.pending_validation is not None
        assert mission.pending_validation["type"] == "architecture"
        assert mission.pending_validation["data"] == arch_data
    
    def test_approve_validation_architecture(self):
        """Test approve_validation() pour architecture"""
        mission = Mission(
            mission_id="test_010",
            user_request="Test",
            project_path="/test"
        )
        
        mission.request_validation("architecture", {"test": "data"})
        mission.approve_validation()
        
        assert mission.architecture_validated is True
        assert mission.current_phase == MissionPhase.GENERATION_CODE
        assert mission.pending_validation is None
        assert mission.status == MissionStatus.IN_PROGRESS
    
    def test_reject_validation_architecture(self):
        """Test reject_validation() pour architecture"""
        mission = Mission(
            mission_id="test_011",
            user_request="Test",
            project_path="/test"
        )
        
        mission.request_validation("architecture", {"test": "data"})
        mission.reject_validation()
        
        assert mission.architecture_validated is False
        assert mission.current_phase == MissionPhase.ARCHITECTURE
        assert mission.pending_validation is None
        assert mission.status == MissionStatus.IN_PROGRESS
    
    def test_approve_validation_code(self):
        """Test approve_validation() pour code"""
        mission = Mission(
            mission_id="test_012",
            user_request="Test",
            project_path="/test"
        )
        
        mission.request_validation("code", {"test": "data"})
        mission.approve_validation()
        
        assert mission.code_validated is True
        assert mission.current_phase == MissionPhase.GENERATION_TESTS
    
    def test_reject_validation_code(self):
        """Test reject_validation() pour code"""
        mission = Mission(
            mission_id="test_013",
            user_request="Test",
            project_path="/test"
        )
        
        mission.request_validation("code", {"test": "data"})
        mission.reject_validation()
        
        assert mission.code_validated is False
        assert mission.current_phase == MissionPhase.CORRECTION


class TestMissionEnums:
    """Tests des énumérations"""
    
    def test_mission_status_values(self):
        """Test valeurs MissionStatus"""
        assert MissionStatus.PENDING == "pending"
        assert MissionStatus.IN_PROGRESS == "in_progress"
        assert MissionStatus.VALIDATING == "validating"
        assert MissionStatus.COMPLETED == "completed"
        assert MissionStatus.FAILED == "failed"
        assert MissionStatus.CANCELLED == "cancelled"
    
    def test_mission_phase_values(self):
        """Test valeurs MissionPhase"""
        assert MissionPhase.ANALYSE == "analyse"
        assert MissionPhase.ARCHITECTURE == "architecture"
        assert MissionPhase.VALIDATION_ARCHI == "validation_architecture"
        assert MissionPhase.GENERATION_CODE == "generation_code"
        assert MissionPhase.GENERATION_TESTS == "generation_tests"
        assert MissionPhase.VALIDATION_CODE == "validation_code"
        assert MissionPhase.CORRECTION == "correction"
        assert MissionPhase.FINALISATION == "finalisation"
