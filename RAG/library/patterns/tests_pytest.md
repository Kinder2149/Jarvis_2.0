# Pattern : Tests Pytest

**Type** : Tests  
**Langage** : Python  
**Framework** : pytest  
**Cas d'usage** : Tests unitaires, tests d'intégration

---

## Structure Fichiers

```
project/
├── src/
│   ├── calculator.py
│   └── storage.py
└── tests/
    ├── conftest.py          # Fixtures partagées
    ├── test_calculator.py   # Tests unitaires
    └── test_integration.py  # Tests d'intégration
```

---

## Code Complet

### conftest.py

```python
import pytest
from pathlib import Path


@pytest.fixture
def temp_file(tmp_path):
    """Fixture fichier temporaire."""
    return tmp_path / "test_data.json"


@pytest.fixture
def sample_data():
    """Fixture données de test."""
    return {
        "items": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ]
    }
```

### test_calculator.py

```python
import pytest
from calculator import Calculator


@pytest.fixture
def calc():
    """Fixture calculatrice."""
    return Calculator()


class TestBasicOperations:
    """Tests opérations de base."""
    
    def test_addition(self, calc):
        """Test addition."""
        assert calc.add(2, 3) == 5
        assert calc.add(-1, 1) == 0
        assert calc.add(0, 0) == 0
    
    def test_subtraction(self, calc):
        """Test soustraction."""
        assert calc.subtract(5, 3) == 2
        assert calc.subtract(0, 5) == -5
    
    def test_multiplication(self, calc):
        """Test multiplication."""
        assert calc.multiply(3, 4) == 12
        assert calc.multiply(0, 5) == 0
        assert calc.multiply(-2, 3) == -6
    
    def test_division(self, calc):
        """Test division."""
        assert calc.divide(10, 2) == 5
        assert calc.divide(7, 2) == 3.5


class TestEdgeCases:
    """Tests cas limites."""
    
    def test_division_by_zero(self, calc):
        """Test division par zéro."""
        with pytest.raises(ValueError, match="division par zéro"):
            calc.divide(10, 0)
    
    def test_large_numbers(self, calc):
        """Test grands nombres."""
        result = calc.add(10**10, 10**10)
        assert result == 2 * 10**10
    
    def test_float_precision(self, calc):
        """Test précision float."""
        result = calc.add(0.1, 0.2)
        assert pytest.approx(result, rel=1e-9) == 0.3


class TestParametrized:
    """Tests paramétrés."""
    
    @pytest.mark.parametrize("a,b,expected", [
        (2, 3, 5),
        (0, 0, 0),
        (-1, 1, 0),
        (10, -5, 5),
    ])
    def test_addition_parametrized(self, calc, a, b, expected):
        """Test addition avec paramètres."""
        assert calc.add(a, b) == expected
    
    @pytest.mark.parametrize("a,b,expected", [
        (10, 2, 5),
        (7, 2, 3.5),
        (-10, 2, -5),
    ])
    def test_division_parametrized(self, calc, a, b, expected):
        """Test division avec paramètres."""
        assert calc.divide(a, b) == expected


class TestTypeValidation:
    """Tests validation types."""
    
    def test_invalid_type_string(self, calc):
        """Test type invalide (string)."""
        with pytest.raises(TypeError):
            calc.add("2", 3)
    
    def test_invalid_type_none(self, calc):
        """Test type invalide (None)."""
        with pytest.raises(TypeError):
            calc.add(None, 3)
```

### test_integration.py

```python
import pytest
import json
from pathlib import Path
from storage import Storage
from calculator import Calculator


@pytest.fixture
def storage(tmp_path):
    """Fixture storage avec fichier temporaire."""
    filepath = tmp_path / "data.json"
    return Storage(str(filepath))


def test_save_and_load(storage):
    """Test sauvegarde et chargement."""
    data = {"result": 42, "operation": "add"}
    storage.save(data)
    
    loaded = storage.load()
    assert loaded == data


def test_persistence_across_instances(tmp_path):
    """Test persistence entre instances."""
    filepath = tmp_path / "data.json"
    
    # Instance 1 : Sauvegarde
    storage1 = Storage(str(filepath))
    storage1.save({"value": 100})
    
    # Instance 2 : Chargement
    storage2 = Storage(str(filepath))
    loaded = storage2.load()
    assert loaded["value"] == 100


def test_calculator_with_storage(storage):
    """Test calculatrice avec storage."""
    calc = Calculator()
    result = calc.add(10, 20)
    
    storage.save({"result": result, "operation": "add"})
    loaded = storage.load()
    
    assert loaded["result"] == 30
    assert loaded["operation"] == "add"


@pytest.mark.asyncio
async def test_async_operation():
    """Test opération asynchrone."""
    # Exemple test async
    import asyncio
    result = await asyncio.sleep(0.1, result=42)
    assert result == 42
```

---

## Règles Strictes

1. **Fixtures** : Utiliser `@pytest.fixture` pour setup/teardown
2. **Classes de tests** : Grouper tests liés dans des classes
3. **Nommage** : `test_*` pour fonctions, `Test*` pour classes
4. **Assertions** : Utiliser `assert` simple
5. **Exceptions** : `pytest.raises(ExceptionType, match="message")`
6. **Parametrize** : `@pytest.mark.parametrize` pour tests multiples
7. **Approx** : `pytest.approx()` pour comparaisons float
8. **Async** : `@pytest.mark.asyncio` pour tests async
9. **tmp_path** : Fixture pytest pour fichiers temporaires
10. **Isolation** : Chaque test doit être indépendant

---

## Patterns Courants

### Test avec Mock

```python
from unittest.mock import Mock, patch

def test_with_mock():
    mock_service = Mock()
    mock_service.get_data.return_value = {"id": 1}
    
    result = mock_service.get_data()
    assert result["id"] == 1
    mock_service.get_data.assert_called_once()
```

### Test avec Patch

```python
@patch('module.external_api_call')
def test_with_patch(mock_api):
    mock_api.return_value = {"status": "ok"}
    
    result = function_that_calls_api()
    assert result["status"] == "ok"
```

### Test Fichier Temporaire

```python
def test_file_operations(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")
    
    assert file.read_text() == "content"
```

---

## Cas d'usage

- ✅ Tests unitaires
- ✅ Tests d'intégration
- ✅ Tests API (avec TestClient)
- ✅ Tests async
- ✅ Tests avec mocks
