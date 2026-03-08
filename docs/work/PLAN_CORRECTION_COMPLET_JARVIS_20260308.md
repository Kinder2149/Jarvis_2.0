# PLAN DE CORRECTION COMPLET - JARVIS 2.0

**Date** : 08 mars 2026  
**Objectif** : Corriger tous les problèmes identifiés pour atteindre 100% succès  
**Priorité** : Améliorer qualité code CRUD, intégrer RAG, établir fil rouge mission

---

## 🔍 PROBLÈMES IDENTIFIÉS

### 1. ❌ RAG NON UTILISÉ PAR LES AGENTS

**Constat** :
- RAG existe et fonctionne (serveur sur port 5001)
- Librairie patterns existe (`RAG/library/patterns/storage_json.md`)
- **MAIS** : Aucun agent n'utilise le RAG pour enrichir son contexte
- `orchestration.py` : RAG utilisé UNIQUEMENT pour indexation finale (ligne 730-742)
- Agents CODEUR, TESTEUR, VALIDATEUR : **Aucun appel RAG**

**Impact** :
- CODEUR ne bénéficie pas des patterns de la librairie
- CODEUR réinvente le pattern Storage JSON à chaque fois
- Pas de réutilisation des bonnes pratiques documentées

**Preuve** :
```python
# backend/services/orchestration.py ligne 147-149
codeur_messages = [
    {"role": "system", "content": codeur.system_prompt},
    {"role": "user", "content": f"{mission.user_request}..."}
]
# ❌ Aucun enrichissement RAG avant l'appel
```

---

### 2. ❌ LIBRAIRIE RAG INSUFFISANTE

**Contenu actuel** :
- `RAG/library/patterns/` : **1 seul fichier** (`storage_json.md`)
- `RAG/library/rules/` : 1 fichier profil utilisateur
- `RAG/library/templates/` : Vide

**Manques critiques** :
- ❌ Pas de pattern CRUD complet (models + storage + logic)
- ❌ Pas de pattern API REST (FastAPI endpoints)
- ❌ Pas de pattern tests pytest (fixtures, mocks)
- ❌ Pas d'exemples TODO/CRUD validés
- ❌ Pas de checklist validation par type de projet

**Impact** :
- Même si RAG était utilisé, il n'aurait pas assez de contenu
- CODEUR manque d'exemples concrets pour projets CRUD

---

### 3. ❌ FEEDBACK VALIDATEUR INCOMPLET

**Format actuel** (ligne 224-226 orchestration.py) :
```
STATUT: VALIDE | INVALIDE
[Si INVALIDE : liste des corrections ligne par ligne]
```

**Problèmes** :
- ❌ Pas de structure stricte pour les corrections
- ❌ Pas de numéro de ligne obligatoire
- ❌ Pas de code AVANT/APRÈS
- ❌ Pas de priorisation des erreurs

**Exemple feedback actuel** (test TODO) :
```
STATUT: INVALIDE
Fichiers manquants: `todo.py` (requis par les tests)
```

**Ce qu'il faudrait** :
```
STATUT: INVALIDE

CORRECTIONS OBLIGATOIRES (par ordre de priorité) :

1. [CRITIQUE] todo.py ligne 1 : Fichier manquant
   AVANT : (fichier n'existe pas)
   APRÈS : Créer fichier todo.py avec classe TodoManager
   
2. [BLOQUANT] todo.py ligne 5 : Import manquant
   AVANT : # (vide)
   APRÈS : from typing import List, Optional
   
3. [BLOQUANT] todo.py ligne 12 : Méthode add_task non définie
   AVANT : # (vide)
   APRÈS : 
   def add_task(self, title: str) -> Task:
       task = Task(id=len(self.tasks), title=title)
       self.tasks.append(task)
       return task
```

---

### 4. ❌ PAS DE FIL ROUGE MISSION PERSISTANT

**Problème actuel** :
- Chaque agent reçoit seulement le `user_request` initial
- Pas de contexte partagé entre agents
- CODEUR ne voit pas ce que ARCHITECTE a décidé
- VALIDATEUR ne voit pas l'architecture prévue
- Corrections en boucle sans mémoire des tentatives précédentes

**Exemple** (ligne 147-149 orchestration.py) :
```python
codeur_messages = [
    {"role": "system", "content": codeur.system_prompt},
    {"role": "user", "content": f"{mission.user_request}..."}
]
# ❌ CODEUR ne voit pas l'architecture ARCHITECTE
# ❌ CODEUR ne voit pas les fichiers déjà créés
# ❌ CODEUR ne voit pas les tentatives précédentes
```

**Ce qu'il faudrait** :
```python
# Fil rouge mission (contexte partagé)
mission_context = {
    "user_request": "Créer app TODO",
    "architecture": {
        "files": ["models.py", "storage.py", "todo.py", "test_todo.py"],
        "decisions": ["Utiliser Pydantic", "Storage JSON", "CLI simple"]
    },
    "files_created": ["models.py", "storage.py"],
    "files_pending": ["todo.py", "test_todo.py"],
    "validation_history": [
        {"attempt": 1, "status": "INVALID", "errors": ["Import manquant"]},
        {"attempt": 2, "status": "INVALID", "errors": ["Méthode manquante"]}
    ]
}

# Chaque agent enrichit le contexte
codeur_messages = [
    {"role": "system", "content": codeur.system_prompt},
    {"role": "user", "content": f"""
CONTEXTE MISSION :
{json.dumps(mission_context, indent=2)}

ARCHITECTURE PRÉVUE :
{architecture_response}

FICHIERS DÉJÀ CRÉÉS :
{existing_files}

TA TÂCHE :
{user_request}
"""}
]
```

---

### 5. ❌ CODEUR PREND DES DÉCISIONS (alors qu'il ne devrait pas)

**Problème** :
- Prompt CODEUR ligne 76 : "Tu NE PRENDS AUCUNE décision architecturale"
- **MAIS** : En pratique, CODEUR décide des noms de fichiers, de la structure, des classes
- Exemple : Demande "classe TodoManager" → CODEUR crée "class TodoList" (variation)

**Cause** :
- Instructions trop vagues : "Créer app TODO"
- Pas d'architecture détaillée fournie au CODEUR
- CODEUR doit deviner la structure

**Solution** :
- ARCHITECTE doit fournir spécifications COMPLÈTES
- CODEUR doit UNIQUEMENT exécuter les specs
- Format strict : "Créer fichier todo.py avec classe TodoManager(BaseModel) avec méthodes add_task, remove_task, list_tasks"

---

### 6. ❌ DOUBLONS ET INCOHÉRENCES ENTRE AGENTS

**Problème** :
- ARCHITECTE propose `models.py` avec classe `Task`
- CODEUR crée `models.py` avec classe `TodoItem` (nom différent)
- TESTEUR importe `Task` (suit ARCHITECTE)
- VALIDATEUR détecte `ImportError: cannot import name 'Task'`

**Cause** :
- Pas de vérification de cohérence entre agents
- Pas de contrat strict entre ARCHITECTE et CODEUR
- Pas de versioning des décisions

---

## 🎯 PLAN DE CORRECTION COMPLET

### PHASE 1 : INTÉGRATION RAG (Priorité CRITIQUE)

#### 1.1 Enrichir Librairie RAG

**Action** : Créer patterns manquants dans `RAG/library/patterns/`

**Fichiers à créer** :
1. `crud_complete.md` : Pattern CRUD complet (models + storage + logic + tests)
2. `api_rest_fastapi.md` : Pattern API REST avec FastAPI
3. `tests_pytest.md` : Pattern tests pytest (fixtures, mocks, parametrize)
4. `pydantic_models.md` : Pattern Pydantic v2 (BaseModel, validation)
5. `todo_app_example.md` : Exemple TODO complet validé

**Contenu type** (`crud_complete.md`) :
```markdown
# Pattern : CRUD Complet

## Structure Fichiers
- models.py : Modèles Pydantic
- storage.py : Persistence JSON
- manager.py : Logique métier
- test_*.py : Tests pytest

## Code Complet

### models.py
```python
from pydantic import BaseModel
from typing import Optional

class Task(BaseModel):
    id: int
    title: str
    completed: bool = False
```

### storage.py
```python
import json
from pathlib import Path
from typing import List
from models import Task

class TaskStorage:
    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = Path(filepath)
    
    def save(self, tasks: List[Task]) -> None:
        data = [task.model_dump() for task in tasks]
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> List[Task]:
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
    def __init__(self, storage: TaskStorage):
        self.storage = storage
        self.tasks = storage.load()
    
    def add_task(self, title: str) -> Task:
        task_id = max([t.id for t in self.tasks], default=0) + 1
        task = Task(id=task_id, title=title)
        self.tasks.append(task)
        self.storage.save(self.tasks)
        return task
    
    def remove_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self.storage.save(self.tasks)
            return True
        return False
    
    def get_task(self, task_id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)
    
    def list_tasks(self) -> List[Task]:
        return self.tasks
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
    return TaskStorage(str(tmp_path / "test_tasks.json"))

@pytest.fixture
def manager(temp_storage):
    return TaskManager(temp_storage)

def test_add_task(manager):
    task = manager.add_task("Test task")
    assert task.id == 1
    assert task.title == "Test task"
    assert not task.completed

def test_list_tasks(manager):
    manager.add_task("Task 1")
    manager.add_task("Task 2")
    tasks = manager.list_tasks()
    assert len(tasks) == 2

def test_remove_task(manager):
    task = manager.add_task("Task to remove")
    assert manager.remove_task(task.id)
    assert len(manager.list_tasks()) == 0

def test_persistence(temp_storage):
    manager1 = TaskManager(temp_storage)
    manager1.add_task("Persistent task")
    
    manager2 = TaskManager(temp_storage)
    tasks = manager2.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "Persistent task"
```
```

**Durée estimée** : 1 jour

---

#### 1.2 Intégrer RAG dans Orchestration

**Action** : Modifier `backend/services/orchestration.py` pour enrichir contexte agents

**Fichier** : `backend/services/orchestration.py`

**Modifications** :

```python
# Ligne 12 : Ajouter import
from backend.services.rag_client import RAGClient

# Ligne 36 : Initialiser client RAG
self.rag_client = RAGClient()

# Ligne 147-149 : AVANT appel CODEUR, enrichir contexte
async def execute_fast_mode(...):
    # ...
    
    # NOUVEAU : Enrichir contexte avec RAG
    rag_context = await self.rag_client.search(
        query=f"pattern CRUD {user_request}",
        top_k=3
    )
    
    codeur_messages = [
        {"role": "system", "content": codeur.system_prompt},
        {"role": "user", "content": f"""CONTEXTE RAG (patterns validés) :
{rag_context}

DEMANDE UTILISATEUR :
{mission.user_request}

Utilise les patterns RAG ci-dessus comme référence pour générer le code."""}
    ]
```

**Créer** : `backend/services/rag_client.py`

```python
import httpx
import logging

logger = logging.getLogger(__name__)

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
    
    async def search(self, query: str, top_k: int = 3) -> str:
        """
        Recherche dans la librairie RAG.
        
        Args:
            query: Requête de recherche
            top_k: Nombre de résultats
        
        Returns:
            Contexte enrichi (patterns, exemples)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={"query": query, "top_k": top_k},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    context = "\n\n".join([
                        f"=== {r['source']} ===\n{r['content']}"
                        for r in results.get("results", [])
                    ])
                    logger.info(f"RAG: {len(results.get('results', []))} résultats trouvés")
                    return context
                else:
                    logger.warning(f"RAG: Erreur {response.status_code}")
                    return ""
        except Exception as e:
            logger.error(f"RAG: Erreur connexion - {e}")
            return ""
```

**Durée estimée** : 1 jour

---

### PHASE 2 : AMÉLIORER FEEDBACK VALIDATEUR (Priorité HAUTE)

#### 2.1 Modifier Prompt VALIDATEUR

**Fichier** : `config_agents/VALIDATEUR.md`

**Ajouter section** :

```markdown
## FORMAT DE RÉPONSE STRICT (CORRECTIONS)

Si INVALIDE, tu DOIS fournir les corrections dans ce format EXACT :

```
STATUT: INVALIDE

CORRECTIONS OBLIGATOIRES (par ordre de priorité) :

1. [CRITIQUE|BLOQUANT|MINEUR] fichier.py ligne X : Description courte
   AVANT : 
   ```python
   # code actuel (ou vide si manquant)
   ```
   APRÈS :
   ```python
   # code corrigé
   ```
   EXPLICATION : Pourquoi cette correction est nécessaire

2. [CRITIQUE|BLOQUANT|MINEUR] fichier.py ligne Y : Description courte
   ...
```

**Niveaux de priorité** :
- **CRITIQUE** : Fichier manquant, erreur syntaxe fatale
- **BLOQUANT** : Import manquant, fonction non définie
- **MINEUR** : Style, optimisation (ignorer si prompt demande de les ignorer)

**Exemple** :
```
STATUT: INVALIDE

CORRECTIONS OBLIGATOIRES (par ordre de priorité) :

1. [CRITIQUE] todo.py ligne 1 : Fichier manquant requis par tests
   AVANT : 
   ```python
   # (fichier n'existe pas)
   ```
   APRÈS :
   ```python
   from typing import List, Optional
   from models import Task
   from storage import TaskStorage

   class TodoManager:
       def __init__(self, storage: TaskStorage):
           self.storage = storage
           self.tasks = storage.load()
       
       def add_task(self, title: str) -> Task:
           # ... (voir pattern CRUD)
   ```
   EXPLICATION : Les tests importent TodoManager depuis todo.py

2. [BLOQUANT] models.py ligne 5 : Import manquant
   AVANT :
   ```python
   class Task(BaseModel):
       id: int
   ```
   APRÈS :
   ```python
   from pydantic import BaseModel

   class Task(BaseModel):
       id: int
   ```
   EXPLICATION : BaseModel n'est pas importé
```
```

**Durée estimée** : 2 heures

---

#### 2.2 Modifier Orchestration pour Utiliser Nouveau Format

**Fichier** : `backend/services/orchestration.py`

**Ligne 246-260** : Modifier message correction CODEUR

```python
correction_messages = [
    {"role": "system", "content": codeur.system_prompt},
    {"role": "user", "content": f"""CONTEXTE MISSION :
Fichiers créés : {list(existing_files.keys())}
Tentative correction : {correction_attempts + 1}/{max_corrections}

CODE ACTUEL :
{code_response}

FEEDBACK VALIDATEUR (corrections détaillées) :
{validation_response}

INSTRUCTIONS :
1. Lis CHAQUE correction numérotée
2. Applique EXACTEMENT le code APRÈS fourni
3. Ne modifie RIEN d'autre
4. Conserve la structure existante
5. Vérifie que tous les imports sont présents

Livre le code corrigé complet."""}
]
```

**Durée estimée** : 1 heure

---

### PHASE 3 : FIL ROUGE MISSION PERSISTANT (Priorité HAUTE)

#### 3.1 Créer Modèle MissionContext

**Fichier** : `backend/models/mission_context.py` (NOUVEAU)

```python
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class ArchitectureDecision(BaseModel):
    """Décision architecturale prise par ARCHITECTE."""
    files_to_create: List[str]
    stack: Dict[str, str]  # {"backend": "FastAPI", "storage": "JSON"}
    patterns: List[str]  # ["CRUD", "Storage JSON"]
    justification: str

class ValidationAttempt(BaseModel):
    """Tentative de validation."""
    attempt_number: int
    timestamp: datetime
    status: str  # "VALID" | "INVALID"
    errors: List[str]
    corrections_applied: List[str]

class MissionContext(BaseModel):
    """Contexte partagé entre tous les agents d'une mission."""
    mission_id: str
    user_request: str
    
    # Phase ARCHITECTE
    architecture: Optional[ArchitectureDecision] = None
    
    # Phase CODEUR
    files_created: Dict[str, str] = {}  # {filepath: content}
    files_pending: List[str] = []
    
    # Phase TESTEUR
    tests_created: Dict[str, str] = {}
    
    # Phase VALIDATEUR
    validation_history: List[ValidationAttempt] = []
    current_status: str = "PENDING"  # "PENDING" | "IN_PROGRESS" | "VALID" | "INVALID"
    
    # Métadonnées
    created_at: datetime
    updated_at: datetime
    
    def add_file(self, filepath: str, content: str):
        """Ajoute un fichier créé."""
        self.files_created[filepath] = content
        if filepath in self.files_pending:
            self.files_pending.remove(filepath)
        self.updated_at = datetime.now()
    
    def add_validation_attempt(self, status: str, errors: List[str]):
        """Ajoute une tentative de validation."""
        attempt = ValidationAttempt(
            attempt_number=len(self.validation_history) + 1,
            timestamp=datetime.now(),
            status=status,
            errors=errors,
            corrections_applied=[]
        )
        self.validation_history.append(attempt)
        self.current_status = status
        self.updated_at = datetime.now()
    
    def get_summary(self) -> str:
        """Résumé du contexte pour les agents."""
        return f"""
MISSION : {self.mission_id}
DEMANDE : {self.user_request}

ARCHITECTURE :
- Fichiers prévus : {self.architecture.files_to_create if self.architecture else 'Non défini'}
- Stack : {self.architecture.stack if self.architecture else 'Non défini'}

PROGRESSION :
- Fichiers créés : {len(self.files_created)}/{len(self.architecture.files_to_create) if self.architecture else 0}
- Fichiers en attente : {self.files_pending}
- Tentatives validation : {len(self.validation_history)}
- Statut actuel : {self.current_status}

HISTORIQUE VALIDATION :
{chr(10).join([f"  Tentative {v.attempt_number}: {v.status} - {len(v.errors)} erreurs" for v in self.validation_history])}
"""
```

**Durée estimée** : 2 heures

---

#### 3.2 Intégrer MissionContext dans Orchestration

**Fichier** : `backend/services/orchestration.py`

**Modifications** :

```python
# Ligne 10 : Ajouter import
from backend.models.mission_context import MissionContext, ArchitectureDecision

# Ligne 102-107 : Créer contexte au début
async def execute_fast_mode(...):
    # Créer contexte mission
    mission_context = MissionContext(
        mission_id=mission.mission_id,
        user_request=user_request,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # ...

# Ligne 147-149 : Passer contexte à CODEUR
codeur_messages = [
    {"role": "system", "content": codeur.system_prompt},
    {"role": "user", "content": f"""
{mission_context.get_summary()}

TA TÂCHE :
{user_request}

FICHIERS À CRÉER :
{mission_context.files_pending if mission_context.files_pending else 'Tous les fichiers nécessaires'}
"""}
]

# Après réponse CODEUR : Mettre à jour contexte
code_response = await codeur.handle(codeur_messages, ...)
# Parser fichiers créés et mettre à jour contexte
for filepath, content in parsed_files.items():
    mission_context.add_file(filepath, content)

# Ligne 201-227 : Passer contexte à VALIDATEUR
validateur_messages = [
    {"role": "system", "content": validateur.system_prompt},
    {"role": "user", "content": f"""
{mission_context.get_summary()}

CODE À VALIDER :
{code_response}

TESTS :
{tests_response}

ARCHITECTURE PRÉVUE :
{mission_context.architecture.model_dump_json(indent=2) if mission_context.architecture else 'Non défini'}
"""}
]

# Après validation : Mettre à jour contexte
validation_response = await validateur.handle(...)
errors = extract_errors_from_validation(validation_response)
mission_context.add_validation_attempt(
    status="VALID" if "STATUT: VALIDE" in validation_response else "INVALID",
    errors=errors
)
```

**Durée estimée** : 3 heures

---

### PHASE 4 : AMÉLIORER PROMPT CODEUR (Priorité MOYENNE)

#### 4.1 Ajouter Exemples CRUD Complets

**Fichier** : `config_agents/CODEUR.md`

**Ajouter après ligne 242** :

```markdown
## EXEMPLES COMPLETS PAR TYPE DE PROJET

### Exemple 1 : Application TODO (CRUD Complet)

**Demande** : "Créer une application TODO avec persistance JSON"

**Fichiers à créer** :
1. models.py
2. storage.py
3. manager.py
4. (tests générés par TESTEUR)

**Code complet** :

#### models.py
```python
from pydantic import BaseModel
from typing import Optional

class Task(BaseModel):
    id: int
    title: str
    completed: bool = False
```

#### storage.py
```python
import json
from pathlib import Path
from typing import List
from models import Task

class TaskStorage:
    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = Path(filepath)
    
    def save(self, tasks: List[Task]) -> None:
        data = [task.model_dump() for task in tasks]
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> List[Task]:
        if not self.filepath.exists():
            return []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Task.model_validate(item) for item in data]
```

#### manager.py
```python
from typing import List, Optional
from models import Task
from storage import TaskStorage

class TaskManager:
    def __init__(self, storage: TaskStorage):
        self.storage = storage
        self.tasks = storage.load()
    
    def add_task(self, title: str) -> Task:
        if not title or not isinstance(title, str):
            raise ValueError("title doit être une chaîne non vide")
        
        task_id = max([t.id for t in self.tasks], default=0) + 1
        task = Task(id=task_id, title=title)
        self.tasks.append(task)
        self.storage.save(self.tasks)
        return task
    
    def remove_task(self, task_id: int) -> bool:
        if not isinstance(task_id, int):
            raise ValueError("task_id doit être un entier")
        
        task = self.get_task(task_id)
        if task:
            self.tasks.remove(task)
            self.storage.save(self.tasks)
            return True
        return False
    
    def get_task(self, task_id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)
    
    def list_tasks(self) -> List[Task]:
        return self.tasks
    
    def mark_completed(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task:
            task.completed = True
            self.storage.save(self.tasks)
            return True
        return False
```

**RÈGLES STRICTES pour ce type de projet** :
1. TOUJOURS séparer models, storage, manager
2. TOUJOURS valider les types d'entrée (isinstance)
3. TOUJOURS gérer le cas fichier inexistant dans load()
4. TOUJOURS utiliser Pydantic v2 (.model_dump(), .model_validate())
5. TOUJOURS sauvegarder après chaque modification (add, remove, mark_completed)
```

**Durée estimée** : 2 heures

---

### PHASE 5 : NETTOYAGE ET COHÉRENCE (Priorité BASSE)

#### 5.1 Vérifier Cohérence Prompts

**Action** : Vérifier que tous les prompts agents sont cohérents

**Fichiers** :
- `config_agents/ARCHITECTE.md`
- `config_agents/CODEUR.md`
- `config_agents/TESTEUR.md`
- `config_agents/VALIDATEUR.md`

**Vérifications** :
- [ ] Tous les agents connaissent le cycle ARRF
- [ ] Tous les agents connaissent les autres agents
- [ ] Tous les agents utilisent le même format de réponse
- [ ] Pas de contradictions entre prompts

**Durée estimée** : 1 heure

---

#### 5.2 Nettoyer Code Obsolète

**Action** : Supprimer code mort et commentaires obsolètes

**Fichiers** :
- `backend/services/orchestration.py` : Supprimer commentaires TODO
- `backend/agents/*.py` : Supprimer code commenté

**Durée estimée** : 30 minutes

---

## 📊 AUTRES POINTS À RÉGLER

### 1. ⚠️ Tests Batch pytest-asyncio

**Problème** : Event loop closed en mode batch  
**Impact** : Tests batch 8/35 PASSED, individuels 6/7 PASSED  
**Solution** : Documenter workaround (lancer tests un par un)  
**Priorité** : BASSE (workaround fonctionne)

---

### 2. ⚠️ Détection Complexité Projets

**Problème** : Détection SIMPLE/COMPLEX parfois incorrecte  
**Impact** : Workflow COMPLET pas toujours déclenché  
**Solution** : Améliorer regex `_extract_expected_files` (ligne 126-133 orchestration.py)  
**Priorité** : MOYENNE

---

### 3. ⚠️ Gestion Timeout Agents

**Problème** : Pas de timeout global mission  
**Impact** : Mission peut bloquer indéfiniment  
**Solution** : Ajouter timeout 10 min par mission  
**Priorité** : MOYENNE

---

### 4. ⚠️ Logs Trop Verbeux

**Problème** : Logs contiennent réponses complètes (8K+ chars)  
**Impact** : Fichiers logs volumineux  
**Solution** : Tronquer logs à 500 chars + lien vers fichier complet  
**Priorité** : BASSE

---

### 5. ⚠️ Pas de Rollback en Cas d'Échec

**Problème** : Si mission échoue, fichiers partiels restent  
**Impact** : Pollution dossier projet  
**Solution** : Créer dossier temporaire, copier seulement si succès  
**Priorité** : MOYENNE

---

## 📅 PLANNING EXÉCUTION

### Semaine 1 (Priorité CRITIQUE + HAUTE)

**Jour 1-2** : PHASE 1 - Intégration RAG
- Enrichir librairie patterns (1 jour)
- Intégrer RAG dans orchestration (1 jour)

**Jour 3** : PHASE 2 - Feedback VALIDATEUR
- Modifier prompt VALIDATEUR (2h)
- Modifier orchestration (1h)
- Tester sur projet TODO (5h)

**Jour 4-5** : PHASE 3 - Fil Rouge Mission
- Créer MissionContext (2h)
- Intégrer dans orchestration (3h)
- Tester workflow complet (1 jour)

### Semaine 2 (Priorité MOYENNE)

**Jour 6-7** : PHASE 4 - Améliorer CODEUR
- Ajouter exemples CRUD (2h)
- Tester sur 10 projets TODO différents (1.5 jour)

**Jour 8** : PHASE 5 - Nettoyage
- Cohérence prompts (1h)
- Nettoyer code (30min)
- Tests régression (6h)

**Jour 9-10** : Tests E2E et Validation
- Lancer 20+ tests E2E variés
- Mesurer taux de succès (objectif 95%+)
- Documenter cas d'usage validés

---

## 🎯 CRITÈRES DE SUCCÈS

### Objectifs Quantitatifs

- ✅ **95%+ succès** sur projets CRUD/TODO
- ✅ **100% succès** sur projets calculatrice/API REST
- ✅ **≤ 2 corrections** en moyenne (vs 6 actuellement)
- ✅ **RAG utilisé** dans 100% des missions
- ✅ **Fil rouge mission** persistant entre agents

### Objectifs Qualitatifs

- ✅ Code généré suit patterns librairie RAG
- ✅ Feedbacks VALIDATEUR actionnables (ligne + code AVANT/APRÈS)
- ✅ Pas de régression entre tentatives correction
- ✅ CODEUR ne prend aucune décision (exécute specs ARCHITECTE)
- ✅ Cohérence totale entre agents (noms classes, fichiers)

---

## 📝 CHECKLIST VALIDATION

Avant de considérer le plan terminé :

**Intégration RAG** :
- [ ] 5+ patterns créés dans librairie RAG
- [ ] RAGClient implémenté et testé
- [ ] Orchestration enrichit contexte CODEUR avec RAG
- [ ] Tests montrent utilisation effective RAG

**Feedback VALIDATEUR** :
- [ ] Nouveau format strict implémenté
- [ ] Corrections incluent numéro ligne + code AVANT/APRÈS
- [ ] Orchestration parse nouveau format
- [ ] Tests montrent convergence en ≤ 2 tentatives

**Fil Rouge Mission** :
- [ ] MissionContext créé et testé
- [ ] Orchestration maintient contexte entre agents
- [ ] Chaque agent enrichit contexte
- [ ] Tests montrent cohérence entre agents

**Qualité Code** :
- [ ] 20+ tests E2E passent (CRUD, TODO, API, calculatrice)
- [ ] Taux succès ≥ 95%
- [ ] Pas de doublons/incohérences
- [ ] Documentation à jour

---

**Durée totale estimée** : **10 jours** (2 semaines)  
**Effort** : 1 développeur temps plein  
**Risque** : FAIBLE (changements incrémentaux, tests à chaque étape)

---

**Rapport créé le** : 08 mars 2026  
**Auteur** : Cascade (IA)  
**Validation** : En attente utilisateur
