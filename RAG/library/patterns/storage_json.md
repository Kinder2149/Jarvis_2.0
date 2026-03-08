# Pattern : Storage JSON

**Type** : Pattern de persistence  
**Langage** : Python  
**Cas d'usage** : Sauvegarder/charger données simples en JSON

---

## Description

Pattern pour gérer la persistence de données en JSON avec une classe dédiée.

---

## Structure

```python
import json
from pathlib import Path
from typing import List

class JsonStorage:
    """Storage JSON avec constructeur, save ET load."""
    
    def __init__(self, filepath: str = "data.json"):
        """IMPORTANT : Toujours inclure un constructeur."""
        self.filepath = Path(filepath)
    
    def save(self, items: List[dict]) -> None:
        """IMPORTANT : save() est obligatoire pour la persistance."""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    
    def load(self) -> List[dict]:
        """IMPORTANT : load() doit gérer le cas fichier inexistant."""
        if not self.filepath.exists():
            return []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
```

---

## Règles Absolues

1. **Constructeur obligatoire** : `__init__(self, filepath: str)`
2. **Méthode save obligatoire** : `save(self, data)`
3. **Méthode load obligatoire** : `load(self) -> data`
4. **Gestion fichier inexistant** : `load()` retourne `[]` ou `{}` si fichier n'existe pas
5. **Encoding UTF-8** : Toujours spécifier `encoding='utf-8'`
6. **ensure_ascii=False** : Pour supporter caractères spéciaux

---

## Exemple Utilisation

```python
# Créer storage
storage = JsonStorage("todos.json")

# Sauvegarder données
todos = [
    {"id": 1, "title": "Task 1", "completed": False},
    {"id": 2, "title": "Task 2", "completed": True}
]
storage.save(todos)

# Charger données
loaded_todos = storage.load()
print(loaded_todos)  # [{"id": 1, ...}, {"id": 2, ...}]
```

---

## Intégration avec Pydantic

```python
from pydantic import BaseModel
from typing import List

class Todo(BaseModel):
    id: int
    title: str
    completed: bool

class TodoStorage(JsonStorage):
    def save(self, todos: List[Todo]) -> None:
        data = [todo.model_dump() for todo in todos]
        super().save(data)
    
    def load(self) -> List[Todo]:
        data = super().load()
        return [Todo.model_validate(item) for item in data]
```

---

## Tests

```python
import pytest
from pathlib import Path

def test_save_creates_file(tmp_path):
    storage = JsonStorage(str(tmp_path / "test.json"))
    storage.save([{"key": "value"}])
    assert (tmp_path / "test.json").exists()

def test_load_returns_empty_list_when_file_not_exists(tmp_path):
    storage = JsonStorage(str(tmp_path / "nonexistent.json"))
    assert storage.load() == []

def test_save_and_load_roundtrip(tmp_path):
    storage = JsonStorage(str(tmp_path / "test.json"))
    data = [{"id": 1, "name": "Test"}]
    storage.save(data)
    loaded = storage.load()
    assert loaded == data
```

---

## Erreurs Courantes

❌ **Oublier le constructeur**
```python
class JsonStorage:
    def save(self, data):  # ❌ Pas de __init__, pas de self.filepath
        ...
```

❌ **Oublier gestion fichier inexistant**
```python
def load(self):
    with open(self.filepath) as f:  # ❌ FileNotFoundError si fichier n'existe pas
        return json.load(f)
```

❌ **Oublier encoding UTF-8**
```python
with open(self.filepath, 'w') as f:  # ❌ Problèmes avec caractères spéciaux
    json.dump(data, f)
```

✅ **Correct**
```python
def load(self):
    if not self.filepath.exists():
        return []
    with open(self.filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
```

---

## Quand Utiliser

✅ **Utiliser Storage JSON si** :
- Données simples (listes, dicts)
- Pas de relations complexes
- Pas de concurrence
- Projet dev/prototype

❌ **Ne PAS utiliser si** :
- Données volumineuses (>10 MB)
- Besoin transactions
- Besoin requêtes complexes
- Production avec forte charge

→ Utiliser SQLite, PostgreSQL, ou MongoDB à la place

---

## Alternatives

- **SQLite** : Pour données relationnelles
- **Pickle** : Pour objets Python complexes (non portable)
- **CSV** : Pour données tabulaires simples
- **YAML** : Pour configuration (plus lisible que JSON)
