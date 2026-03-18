# Pattern : API REST FastAPI

**Type** : Architecture  
**Langage** : Python  
**Framework** : FastAPI  
**Cas d'usage** : API REST, backend web, microservices

---

## Structure Fichiers

```
api_project/
├── models.py       # Modèles Pydantic
├── storage.py      # Persistence
├── api.py          # Endpoints FastAPI
├── main.py         # Point d'entrée
└── test_api.py     # Tests API
```

---

## Code Complet

### models.py

```python
from pydantic import BaseModel, Field
from typing import Optional


class TaskCreate(BaseModel):
    """Schéma création tâche."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    """Schéma mise à jour tâche."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    completed: Optional[bool] = None


class Task(BaseModel):
    """Modèle tâche."""
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
```

### storage.py

```python
import json
from pathlib import Path
from typing import List, Optional
from models import Task


class TaskStorage:
    """Persistence JSON pour les tâches."""
    
    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = Path(filepath)
        self.tasks = self.load()
    
    def save(self) -> None:
        """Sauvegarde les tâches en JSON."""
        data = [task.model_dump() for task in self.tasks]
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> List[Task]:
        """Charge les tâches depuis JSON."""
        if not self.filepath.exists():
            return []
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [Task.model_validate(item) for item in data]
    
    def get_all(self) -> List[Task]:
        """Retourne toutes les tâches."""
        return self.tasks
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Récupère une tâche par ID."""
        return next((t for t in self.tasks if t.id == task_id), None)
    
    def create(self, title: str, description: Optional[str] = None) -> Task:
        """Crée une nouvelle tâche."""
        task_id = max([t.id for t in self.tasks], default=0) + 1
        task = Task(id=task_id, title=title, description=description)
        self.tasks.append(task)
        self.save()
        return task
    
    def update(self, task_id: int, title: Optional[str] = None, 
               description: Optional[str] = None, completed: Optional[bool] = None) -> Optional[Task]:
        """Met à jour une tâche."""
        task = self.get_by_id(task_id)
        if not task:
            return None
        
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if completed is not None:
            task.completed = completed
        
        self.save()
        return task
    
    def delete(self, task_id: int) -> bool:
        """Supprime une tâche."""
        task = self.get_by_id(task_id)
        if task:
            self.tasks.remove(task)
            self.save()
            return True
        return False
```

### api.py

```python
from fastapi import FastAPI, HTTPException, status
from typing import List
from models import Task, TaskCreate, TaskUpdate
from storage import TaskStorage

app = FastAPI(title="Task API", version="1.0.0")
storage = TaskStorage()


@app.get("/tasks", response_model=List[Task], tags=["tasks"])
async def list_tasks():
    """Liste toutes les tâches."""
    return storage.get_all()


@app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"])
async def get_task(task_id: int):
    """Récupère une tâche par ID."""
    task = storage.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, tags=["tasks"])
async def create_task(task_data: TaskCreate):
    """Crée une nouvelle tâche."""
    task = storage.create(title=task_data.title, description=task_data.description)
    return task


@app.put("/tasks/{task_id}", response_model=Task, tags=["tasks"])
async def update_task(task_id: int, task_data: TaskUpdate):
    """Met à jour une tâche."""
    task = storage.update(
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        completed=task_data.completed
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
async def delete_task(task_id: int):
    """Supprime une tâche."""
    if not storage.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
```

### main.py

```python
import uvicorn
from api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### test_api.py

```python
import pytest
from fastapi.testclient import TestClient
from api import app, storage
from models import Task


@pytest.fixture
def client():
    """Fixture client de test."""
    storage.tasks = []  # Reset storage
    return TestClient(app)


def test_list_tasks_empty(client):
    """Test liste vide."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_task(client):
    """Test création tâche."""
    response = client.post("/tasks", json={"title": "Test task"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test task"
    assert data["id"] == 1


def test_create_task_with_description(client):
    """Test création avec description."""
    response = client.post("/tasks", json={
        "title": "Task",
        "description": "Description"
    })
    assert response.status_code == 201
    assert response.json()["description"] == "Description"


def test_create_task_invalid_title(client):
    """Test création avec titre invalide."""
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422


def test_get_task(client):
    """Test récupération tâche."""
    create_response = client.post("/tasks", json={"title": "Task"})
    task_id = create_response.json()["id"]
    
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Task"


def test_get_task_not_found(client):
    """Test récupération tâche inexistante."""
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_update_task(client):
    """Test mise à jour tâche."""
    create_response = client.post("/tasks", json={"title": "Original"})
    task_id = create_response.json()["id"]
    
    response = client.put(f"/tasks/{task_id}", json={"title": "Updated"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_update_task_not_found(client):
    """Test mise à jour tâche inexistante."""
    response = client.put("/tasks/999", json={"title": "Updated"})
    assert response.status_code == 404


def test_delete_task(client):
    """Test suppression tâche."""
    create_response = client.post("/tasks", json={"title": "Task"})
    task_id = create_response.json()["id"]
    
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    
    # Vérifier suppression
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_task_not_found(client):
    """Test suppression tâche inexistante."""
    response = client.delete("/tasks/999")
    assert response.status_code == 404
```

---

## Règles Strictes

1. **Validation Pydantic** : Utiliser `Field()` pour contraintes
2. **Codes HTTP** : 200 (OK), 201 (Created), 204 (No Content), 404 (Not Found), 422 (Validation Error)
3. **HTTPException** : Lever pour erreurs (404, etc.)
4. **TestClient** : Utiliser `TestClient(app)` pour tests
5. **Reset storage** : Nettoyer storage entre tests
6. **Tags** : Grouper endpoints par tags
7. **response_model** : Spécifier pour validation réponse

---

## Cas d'usage

- ✅ API REST CRUD
- ✅ Backend web
- ✅ Microservices
- ✅ API publique
