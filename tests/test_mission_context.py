"""
Tests pour MissionContext
"""

import pytest
from datetime import datetime
from backend.models.mission_context import MissionContext, ArchitectureDecision, ValidationAttempt


def test_mission_context_creation():
    """Test création MissionContext."""
    context = MissionContext(
        mission_id="test-001",
        user_request="Créer app TODO",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    assert context.mission_id == "test-001"
    assert context.user_request == "Créer app TODO"
    assert context.architecture is None
    assert len(context.files_created) == 0
    assert len(context.validation_history) == 0
    assert context.current_status == "PENDING"


def test_add_file():
    """Test ajout de fichier."""
    context = MissionContext(
        mission_id="test-001",
        user_request="Test",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    context.add_file("models.py", "class Task: pass")
    
    assert "models.py" in context.files_created
    assert context.files_created["models.py"] == "class Task: pass"


def test_add_file_removes_from_pending():
    """Test que add_file retire de files_pending."""
    context = MissionContext(
        mission_id="test-001",
        user_request="Test",
        files_pending=["models.py", "storage.py"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    context.add_file("models.py", "code")
    
    assert "models.py" not in context.files_pending
    assert "storage.py" in context.files_pending


def test_add_validation_attempt():
    """Test ajout tentative validation."""
    context = MissionContext(
        mission_id="test-001",
        user_request="Test",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    context.add_validation_attempt("INVALID", ["Error 1", "Error 2"])
    
    assert len(context.validation_history) == 1
    assert context.validation_history[0].status == "INVALID"
    assert len(context.validation_history[0].errors) == 2
    assert context.current_status == "INVALID"


def test_get_summary():
    """Test génération résumé."""
    context = MissionContext(
        mission_id="test-001",
        user_request="Créer app TODO",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    context.architecture = ArchitectureDecision(
        files_to_create=["models.py", "storage.py"],
        stack={"backend": "Python"},
        patterns=["CRUD"],
        file_specs={},
        justification="Test"
    )
    
    context.add_file("models.py", "code")
    context.add_validation_attempt("INVALID", ["Error 1"])
    
    summary = context.get_summary()
    
    assert "test-001" in summary
    assert "Créer app TODO" in summary
    assert "models.py" in summary
    assert "1/2" in summary  # 1 fichier créé sur 2
    assert "Tentative 1: INVALID" in summary


def test_architecture_decision():
    """Test ArchitectureDecision."""
    decision = ArchitectureDecision(
        files_to_create=["models.py"],
        stack={"backend": "Python"},
        patterns=["CRUD"],
        file_specs={"models.py": {"classes": []}},
        justification="Simple architecture"
    )
    
    assert len(decision.files_to_create) == 1
    assert decision.stack["backend"] == "Python"


def test_validation_attempt():
    """Test ValidationAttempt."""
    attempt = ValidationAttempt(
        attempt_number=1,
        timestamp=datetime.now(),
        status="INVALID",
        errors=["Error 1", "Error 2"]
    )
    
    assert attempt.attempt_number == 1
    assert attempt.status == "INVALID"
    assert len(attempt.errors) == 2
