"""
Tests pour ValidationParser
"""

import pytest
from backend.services.validation_parser import ValidationParser


def test_parse_corrections_valid_format():
    """Test parsing de corrections au format VALIDATEUR."""
    parser = ValidationParser()
    feedback = """
STATUT: INVALIDE

=== VALIDATION CODE ===
- [models.py] : ❌ INVALIDE
  PROBLÈMES DÉTECTÉS:
  • Ligne 5 : Import manquant (from pydantic import BaseModel)
  • Ligne 12 : Attribut 'id' non défini

- [storage.py] : ❌ INVALIDE
  PROBLÈMES DÉTECTÉS:
  • Ligne 20 : Méthode save() manquante
"""
    corrections = parser.parse_corrections(feedback)
    
    assert len(corrections) == 3
    assert corrections[0]["file"] == "models.py"
    assert corrections[0]["line"] == 5
    assert "Import manquant" in corrections[0]["description"]
    
    assert corrections[1]["file"] == "models.py"
    assert corrections[1]["line"] == 12
    
    assert corrections[2]["file"] == "storage.py"
    assert corrections[2]["line"] == 20


def test_parse_corrections_no_corrections():
    """Test parsing sans corrections."""
    parser = ValidationParser()
    feedback = "STATUT: VALIDE\n\nTout est OK"
    corrections = parser.parse_corrections(feedback)
    assert len(corrections) == 0


def test_is_valid_true():
    """Test détection VALIDE."""
    parser = ValidationParser()
    feedback = "STATUT: VALIDE\n\nCode validé avec succès"
    assert parser.is_valid(feedback) is True


def test_is_valid_false():
    """Test détection INVALIDE."""
    parser = ValidationParser()
    feedback = "STATUT: INVALIDE\n\nProblèmes détectés"
    assert parser.is_valid(feedback) is False


def test_is_valid_statut_final():
    """Test détection avec STATUT FINAL."""
    parser = ValidationParser()
    feedback = "STATUT FINAL: VALIDE\n\nValidation complète"
    assert parser.is_valid(feedback) is True
