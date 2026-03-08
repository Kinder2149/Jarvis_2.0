"""
Tests pour ArchitectureParser
"""

import pytest
from backend.services.architecture_parser import ArchitectureParser


def test_parse_valid_architecture():
    """Test parsing d'une architecture valide."""
    parser = ArchitectureParser()
    response = '''
### PARTIE 1 : JSON (pour parsing automatique)

```json
{
  "files_to_create": ["models.py", "storage.py"],
  "stack": {"backend": "Python"},
  "file_specs": {
    "models.py": {"classes": [{"name": "Task"}]}
  }
}
```

### PARTIE 2 : Document architecture.md
'''
    result = parser.parse(response)
    
    assert result is not None
    assert "models.py" in result["files_to_create"]
    assert "storage.py" in result["files_to_create"]
    assert result["stack"]["backend"] == "Python"
    assert "models.py" in result["file_specs"]


def test_parse_missing_json():
    """Test parsing sans bloc JSON."""
    parser = ArchitectureParser()
    result = parser.parse("Pas de JSON ici")
    assert result is None


def test_parse_invalid_json():
    """Test parsing avec JSON invalide."""
    parser = ArchitectureParser()
    response = '''
```json
{
  "files_to_create": ["models.py",
  "invalid json
}
```
'''
    result = parser.parse(response)
    assert result is None


def test_parse_missing_required_keys():
    """Test parsing avec clés requises manquantes."""
    parser = ArchitectureParser()
    response = '''
```json
{
  "files_to_create": ["models.py"]
}
```
'''
    result = parser.parse(response)
    assert result is None


def test_extract_markdown():
    """Test extraction du document Markdown."""
    parser = ArchitectureParser()
    response = '''
### PARTIE 2 : Document architecture.md

```markdown
# Architecture TODO

Description du projet
```
'''
    markdown = parser.extract_markdown(response)
    assert markdown is not None
    assert "Architecture TODO" in markdown
    assert "Description du projet" in markdown


def test_extract_markdown_not_found():
    """Test extraction Markdown non trouvé."""
    parser = ArchitectureParser()
    result = parser.extract_markdown("Pas de markdown ici")
    assert result is None
