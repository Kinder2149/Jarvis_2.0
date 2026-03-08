# Pattern : CRUD Complet

**Type** : Architecture  
**Langage** : Python  
**Cas d'usage** : Applications TODO, gestion de données, CRUD simple

---

## Structure Fichiers

```
project/
├── models.py       # Modèles Pydantic
├── storage.py      # Persistence JSON
├── manager.py      # Logique métier
└── test_*.py       # Tests pytest
```

---

## Code Complet

### models.py

```python
from pydantic import BaseModel
from typing import Optional


class Task(BaseModel):
    """Modèle de tâche."""
    id: int
    title: str
    completed: bool = False
    description: Optional[str] = None
```

### storage.py

```python
import json
from pathlib import Path
from typing import List
from models import Task


class TaskStorage:
    """Persistence JSON pour les tâches."""
    
    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = Path(filepath)
    
    def save(self, tasks: List[Task]) -> None:
        """Sauvegarde la liste de tâches en JSON."""
        data = [task.model_dump() for task in tasks]
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> List[Task]:
        """Charge les tâches depuis JSON. Retourne [] si fichier inexistant."""
        if not self.filepath.exists():
            return []
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [Task.model_validate(item) for item in data]
```

### manager.py

```python
from typing import List, Optional
from models import Task
from storage import TaskStorage


class TaskManager:
    """Gestionnaire de tâches avec CRUD complet."""
    
    def __init__(self, storage: TaskStorage):
        self.storage = storage
        self.tasks = storage.load()
    
    def add_task(self, title: str, description: Optional[str] = None) -> Task:
        """Ajoute une nouvelle tâche."""
        if not title or not isinstance(title, str):
            raise ValueError("title doit être une chaîne non vide")
        
        task_id = max([t.id for t in self.tasks], default=0) + 1
        task = Task(id=task_id, title=title, description=description)
        self.tasks.append(task)
        self.storage.save(self.tasks)
        return task
    
    def remove_task(self, task_id: int) -> bool:
        """Retire une tâche par ID. Retourne True si trouvée."""
        if not isinstance(task_id, int):
            raise ValueError("task_id doit être un entier")
        
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self.storage.save(self.tasks)
            return True
        return False
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Récupère une tâche par ID."""
        return next((t for t in self.tasks if t.id == task_id), None)
    
    def list_tasks(self) -> List[Task]:
        """Retourne toutes les tâches."""
        return self.tasks
    
    def mark_completed(self, task_id: int) -> bool:
        """Marque une tâche comme complétée."""
        task = self.get_task(task_id)
        if task:
            task.completed = True
            self.storage.save(self.tasks)
            return True
        return False
    
    def update_task(self, task_id: int, title: Optional[str] = None, 
                    description: Optional[str] = None) -> bool:
        """Met à jour une tâche."""
        task = self.get_task(task_id)
        if not task:
            return False
        
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        
        self.storage.save(self.tasks)
        return True
```

### test_manager.py

```python
import pytest
from pathlib import Path
from models import Task
from storage import TaskStorage
from manager import TaskManager


@pytest.fixture
def temp_storage(tmp_path):
    """Fixture storage temporaire."""
    return TaskStorage(str(tmp_path / "test_tasks.json"))


@pytest.fixture
def manager(temp_storage):
    """Fixture manager avec storage temporaire."""
    return TaskManager(temp_storage)


def test_add_task(manager):
    """Test ajout de tâche."""
    task = manager.add_task("Test task")
    assert task.id == 1
    assert task.title == "Test task"
    assert not task.completed


def test_add_task_with_description(manager):
    """Test ajout avec description."""
    task = manager.add_task("Task", description="Description")
    assert task.description == "Description"


def test_add_task_invalid_title(manager):
    """Test ajout avec titre invalide."""
    with pytest.raises(ValueError):
        manager.add_task("")


def test_list_tasks(manager):
    """Test liste des tâches."""
    manager.add_task("Task 1")
    manager.add_task("Task 2")
    tasks = manager.list_tasks()
    assert len(tasks) == 2


def test_remove_task(manager):
    """Test suppression de tâche."""
    task = manager.add_task("Task to remove")
    assert manager.remove_task(task.id)
    assert len(manager.list_tasks()) == 0


def test_remove_task_not_found(manager):
    """Test suppression tâche inexistante."""
    assert not manager.remove_task(999)


def test_mark_completed(manager):
    """Test marquer comme complétée."""
    task = manager.add_task("Task")
    assert manager.mark_completed(task.id)
    assert manager.get_task(task.id).completed


def test_update_task(manager):
    """Test mise à jour tâche."""
    task = manager.add_task("Original")
    assert manager.update_task(task.id, title="Updated")
    assert manager.get_task(task.id).title == "Updated"


def test_persistence(temp_storage):
    """Test persistence entre instances."""
    manager1 = TaskManager(temp_storage)
    manager1.add_task("Persistent task")
    
    manager2 = TaskManager(temp_storage)
    tasks = manager2.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "Persistent task"
```

---

## Règles Strictes

1. **Séparation responsabilités** : models → storage → manager
2. **Pydantic v2** : Utiliser `.model_dump()` et `.model_validate()`
3. **Validation types** : Toujours valider avec `isinstance()`
4. **Gestion erreurs** : Lever `ValueError` si paramètres invalides
5. **Persistence** : Sauvegarder après chaque modification
6. **Fichier inexistant** : `load()` retourne `[]` si fichier n'existe pas
7. **ID auto-incrémenté** : `max([t.id for t in self.tasks], default=0) + 1`

---

## Cas d'usage

- ✅ Application TODO
- ✅ Gestion de contacts
- ✅ Liste de courses
- ✅ Gestion de notes
- ✅ Tout CRUD simple avec persistence JSON
