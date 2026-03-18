# Pattern : Pydantic Models v2

**Type** : Modèles de données  
**Langage** : Python  
**Framework** : Pydantic v2  
**Cas d'usage** : Validation de données, API, configuration

---

## Règles Absolues Pydantic v2

**API Pydantic v2** (✅ UTILISER) :
- `.model_dump()` au lieu de `.dict()`
- `.model_validate()` au lieu de `.parse_obj()`
- `.model_copy()` au lieu de `.copy()`
- `.model_dump_json()` au lieu de `.json()`
- `.model_validate_json()` au lieu de `.parse_raw()`

**API Pydantic v1** (❌ NE JAMAIS UTILISER) :
- ❌ `.dict()` → OBSOLÈTE
- ❌ `.parse_obj()` → OBSOLÈTE
- ❌ `.copy()` → OBSOLÈTE
- ❌ `.json()` → OBSOLÈTE

---

## Code Complet

### Modèle Simple

```python
from pydantic import BaseModel


class User(BaseModel):
    """Modèle utilisateur simple."""
    id: int
    name: str
    email: str
    active: bool = True


# Utilisation
user = User(id=1, name="Alice", email="alice@example.com")

# Pydantic v2 : model_dump()
user_dict = user.model_dump()  # ✅ CORRECT
# user_dict = user.dict()  # ❌ OBSOLÈTE

# Pydantic v2 : model_validate()
user_from_dict = User.model_validate({"id": 1, "name": "Bob", "email": "bob@example.com"})  # ✅ CORRECT
# user_from_dict = User.parse_obj({...})  # ❌ OBSOLÈTE
```

### Modèle avec Validation

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Task(BaseModel):
    """Modèle tâche avec validation."""
    id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(default=1, ge=1, le=5)
    completed: bool = False
    
    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        """Valide que le titre n'est pas vide."""
        if not v or not v.strip():
            raise ValueError('title ne peut pas être vide')
        return v.strip()
    
    @field_validator('priority')
    @classmethod
    def priority_must_be_valid(cls, v: int) -> int:
        """Valide que la priorité est entre 1 et 5."""
        if not 1 <= v <= 5:
            raise ValueError('priority doit être entre 1 et 5')
        return v


# Utilisation
task = Task(id=1, title="Important task", priority=3)

# Validation automatique
try:
    invalid_task = Task(id=2, title="", priority=10)
except ValueError as e:
    print(f"Validation error: {e}")
```

### Modèle Nested

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Address(BaseModel):
    """Adresse."""
    street: str
    city: str
    country: str
    postal_code: str


class Contact(BaseModel):
    """Contact."""
    email: str
    phone: Optional[str] = None


class Person(BaseModel):
    """Personne avec adresse et contact."""
    id: int
    name: str
    address: Address
    contact: Contact
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)


# Utilisation
person = Person(
    id=1,
    name="Alice",
    address=Address(
        street="123 Main St",
        city="Paris",
        country="France",
        postal_code="75001"
    ),
    contact=Contact(
        email="alice@example.com",
        phone="+33123456789"
    ),
    tags=["developer", "python"]
)

# Pydantic v2 : model_dump() avec nested
person_dict = person.model_dump()  # ✅ CORRECT
# Résultat : dict avec address et contact comme dicts
```

### Modèle avec Config

```python
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Modèle avec configuration."""
    model_config = ConfigDict(
        str_strip_whitespace=True,  # Trim whitespace
        validate_assignment=True,    # Valider lors de l'assignation
        frozen=False,                # Permettre modification
        extra='forbid'               # Interdire champs extra
    )
    
    id: int
    name: str
    email: str


# Utilisation
user = User(id=1, name="  Alice  ", email="alice@example.com")
print(user.name)  # "Alice" (whitespace trimmed)

# Validation lors de l'assignation
user.name = "  Bob  "
print(user.name)  # "Bob" (whitespace trimmed)
```

### Sérialisation JSON

```python
from pydantic import BaseModel
from typing import List


class Task(BaseModel):
    id: int
    title: str
    completed: bool = False


class TaskList(BaseModel):
    tasks: List[Task]


# Créer instance
task_list = TaskList(tasks=[
    Task(id=1, title="Task 1"),
    Task(id=2, title="Task 2", completed=True)
])

# Pydantic v2 : model_dump_json()
json_str = task_list.model_dump_json(indent=2)  # ✅ CORRECT
# json_str = task_list.json()  # ❌ OBSOLÈTE

# Pydantic v2 : model_validate_json()
loaded = TaskList.model_validate_json(json_str)  # ✅ CORRECT
# loaded = TaskList.parse_raw(json_str)  # ❌ OBSOLÈTE

print(loaded.tasks[0].title)  # "Task 1"
```

### Copie de Modèle

```python
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    email: str


user = User(id=1, name="Alice", email="alice@example.com")

# Pydantic v2 : model_copy()
user_copy = user.model_copy()  # ✅ CORRECT
# user_copy = user.copy()  # ❌ OBSOLÈTE

# Copie avec modifications
user_modified = user.model_copy(update={"name": "Bob"})  # ✅ CORRECT
print(user_modified.name)  # "Bob"
```

---

## Règles Strictes

1. **Toujours Pydantic v2** : Utiliser `.model_dump()`, `.model_validate()`, etc.
2. **Field()** : Utiliser pour contraintes (min_length, max_length, ge, le)
3. **field_validator** : Utiliser `@field_validator` pour validation custom
4. **ConfigDict** : Utiliser `model_config = ConfigDict(...)` pour configuration
5. **Type hints** : Toujours typer les attributs
6. **Optional** : Utiliser `Optional[T]` pour valeurs nullables
7. **default_factory** : Utiliser pour valeurs par défaut dynamiques (datetime.now, list, dict)

---

## Exemples Validation

### Validation Email

```python
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    email: EmailStr  # Validation email automatique
```

### Validation URL

```python
from pydantic import BaseModel, HttpUrl

class Website(BaseModel):
    url: HttpUrl  # Validation URL automatique
```

### Validation Custom

```python
from pydantic import BaseModel, field_validator

class Product(BaseModel):
    name: str
    price: float
    
    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('price doit être positif')
        return v
```

---

## Cas d'usage

- ✅ Modèles de données
- ✅ Validation API (FastAPI)
- ✅ Configuration
- ✅ Sérialisation JSON
- ✅ ORM (avec SQLModel)
