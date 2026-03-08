# PLAN D'EXÉCUTION IA — JARVIS 2.0 OPTIMISATION COMPLÈTE

**Date** : 7 mars 2026  
**Statut** : Plan d'exécution pour IA  
**Objectif** : Implémentation complète système 5 agents + missions + RAG optimisé

---

## 🎯 CONTEXTE EXÉCUTION

**Exécuteur** : IA (Cascade)  
**Superviseur** : Valentin (validation uniquement)  
**Principe** : Implémentation progressive, testée, sans travaux inachevés

**Règles d'exécution** :
1. **Cycle ARRF** : Analyse → Réflexion → Remise en Question → Fixation
2. Vérifier code existant AVANT toute modification
3. Tester chaque composant après création
4. Pas de code incomplet ou commenté "TODO"
5. **Honnêteté > Satisfaction** : Signaler impossibilités, proposer alternatives
6. Configs agents dans `agent_config.py` uniquement (pas fichiers séparés)
7. Commit Git après chaque phase complétée

---

## 📋 PHASES D'EXÉCUTION RÉVISÉES

**Total estimé** : 20-25h (réaliste)
**Principe** : Suppression complète ancien système, nouvelle base propre

### PHASE 0 : NETTOYAGE & PRÉPARATION (1-2h)

#### 0.1 Suppression Ancien Système
**Objectif** : Nettoyer complètement traces ancien workflow Mistral

**Actions** :
```bash
# Supprimer ancien orchestration
rm backend/services/orchestration.py

# Supprimer tous tests existants
rm -rf tests/*
mkdir tests
touch tests/__init__.py

# Supprimer providers Mistral/OpenRouter si existants
rm -f backend/ia/providers/mistral_provider.py
rm -f backend/ia/providers/openrouter_provider.py

# Vérifier qu'il ne reste que gemini_provider.py
ls backend/ia/providers/
```

**Livrables** :
- Ancien système supprimé
- Tests nettoyés
- Base propre

#### 0.2 Créer Structure Dossiers
**Objectif** : Préparer arborescence avant implémentation

**Actions** :
```bash
# Structure Library RAG
mkdir -p RAG/library/templates/python
mkdir -p RAG/library/templates/javascript
mkdir -p RAG/library/templates/flutter
mkdir -p RAG/library/patterns
mkdir -p RAG/library/rules
mkdir -p RAG/library/assets
mkdir -p RAG/projects

# Structure backend
mkdir -p backend/models
mkdir -p backend/services
```

**Livrables** :
- Arborescence complète créée
- Fichiers `.gitkeep` si nécessaire

---

### PHASE 1 : SYSTÈME MISSIONS & ÉTATS (2-3h)

#### 1.1 Créer Modèle Mission

**Objectif** : Système missions avec phases et états asynchrones

**Fichier** : `backend/models/mission.py`

```python
from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class MissionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"  # Attente validation USER
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MissionPhase(str, Enum):
    ANALYSE = "analyse"              # JARVIS_Maître analyse
    ARCHITECTURE = "architecture"    # ARCHITECTE propose
    VALIDATION_ARCHI = "validation_architecture"
    GENERATION_CODE = "generation_code"
    GENERATION_TESTS = "generation_tests"
    VALIDATION_CODE = "validation_code"
    CORRECTION = "correction"
    FINALISATION = "finalisation"

class Mission(BaseModel):
    mission_id: str
    user_request: str
    project_path: str
    status: MissionStatus = MissionStatus.PENDING
    current_phase: Optional[MissionPhase] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    architecture_validated: bool = False
    code_validated: bool = False
    tests_validated: bool = False
    pending_validation: Optional[dict] = None
    error_count: int = 0
    
    def is_complete(self) -> bool:
        return (
            self.architecture_validated and
            self.code_validated and
            self.tests_validated and
            len(self.files_created) > 0
        )
    
    def mark_completed(self):
        self.status = MissionStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def mark_failed(self, reason: str):
        self.status = MissionStatus.FAILED
        self.error_count += 1
```

**Workflow Mode Complet** :
```
1. JARVIS_Maître (ANALYSE)
   → Analyse demande utilisateur
   → Détecte complexité (simple/medium/complex)
   → Si complex : continue, sinon mode rapide
   
2. ARCHITECTE (ARCHITECTURE)
   → Propose architecture technique
   → Génère architecture.md
   → Liste fichiers à créer
   
3. JARVIS_Maître (VALIDATION_ARCHI)
   → Remet en question architecture
   → Identifie manques/incohérences
   → Mission.status = VALIDATING
   → Attend validation USER via API
   
4. USER valide → Mission.status = IN_PROGRESS

5. CODEUR (GENERATION_CODE)
   → Génère code selon architecture
   → Enrichi par RAG (templates, patterns)
   → Mission.files_created = [...]
   
6. TESTEUR (GENERATION_TESTS)
   → Génère tests exhaustifs
   → Mission.files_created += [tests]
   
7. VALIDATEUR (VALIDATION_CODE)
   → Valide code + tests + cohérence architecture
   → Si VALIDE : Mission.code_validated = True
   → Si INVALIDE : retour CODEUR (max 3 tentatives)
   
8. JARVIS_Maître (FINALISATION)
   → Vérifie Mission.is_complete()
   → Mission.status = COMPLETED
   → Déclenche auto-indexation RAG
```

**Workflow Mode Rapide (≤3 fichiers)** :
```
1. JARVIS_Maître (ANALYSE) → Détecte simple
2. CODEUR (GENERATION_CODE) → Génère directement
3. TESTEUR (GENERATION_TESTS)
4. VALIDATEUR (VALIDATION_CODE)
5. JARVIS_Maître (FINALISATION)
```

#### 1.2 Modifier orchestration.py

**Fichier** : `backend/services/orchestration.py`

**Ajouts** :
```python
from backend.models.mission import Mission, MissionStatus, MissionPhase
from backend.services.mission_manager import MissionManager

class SimpleOrchestrator:
    
    @staticmethod
    async def execute_mission(mission: Mission, session_state: SessionState):
        """Exécute mission complète avec workflow 5 agents"""
        mission_manager = MissionManager()
        
        # Phase 1 : ANALYSE
        mission.current_phase = MissionPhase.ANALYSE
        complexity = await SimpleOrchestrator.analyze_request(
            mission.user_request, session_state
        )
        
        if complexity == "SIMPLE":
            return await SimpleOrchestrator.execute_fast_mode(mission, session_state)
        else:
            return await SimpleOrchestrator.execute_complete_mode(mission, session_state)
    
    @staticmethod
    async def analyze_request(user_request: str, session_state: SessionState) -> str:
        """JARVIS_Maître analyse demande et détermine complexité"""
        jarvis = get_agent("JARVIS_Maître")
        
        analysis_prompt = f"""
Analyse cette demande et détermine la complexité du projet :

{user_request}

Réponds UNIQUEMENT par : SIMPLE, MEDIUM ou COMPLEX

Critères :
- SIMPLE : ≤3 fichiers, pas d'architecture complexe
- MEDIUM : 4-10 fichiers, architecture standard
- COMPLEX : >10 fichiers, architecture avancée, multiples modules
"""
        
        response = await jarvis.handle([{"role": "user", "content": analysis_prompt}])
        
        if "SIMPLE" in response.upper():
            return "SIMPLE"
        elif "COMPLEX" in response.upper():
            return "COMPLEX"
        else:
            return "MEDIUM"
    
    @staticmethod
    async def execute_complete_mode(mission: Mission, session_state: SessionState):
        """Mode complet avec ARCHITECTE"""
        mission_manager = MissionManager()
        
        # Phase 2 : ARCHITECTURE
        mission.current_phase = MissionPhase.ARCHITECTURE
        mission_manager.update_mission(mission)
        
        architecture = await SimpleOrchestrator.delegate_to_architecte(
            mission.user_request, session_state
        )
        
        # Phase 3 : VALIDATION ARCHITECTURE
        mission.current_phase = MissionPhase.VALIDATION_ARCHI
        mission.status = MissionStatus.VALIDATING
        mission.pending_validation = {
            "type": "architecture",
            "content": architecture
        }
        mission_manager.update_mission(mission)
        
        # Retourner pour attente validation USER
        return {
            "status": "awaiting_validation",
            "mission_id": mission.mission_id,
            "architecture": architecture,
            "message": "Architecture proposée. Valide via /mission/{id}/validate"
        }
```

**Fichier** : `config_agents/ARCHITECTE.md`

**Contenu** :
```markdown
# AGENT ARCHITECTE — Conception Architecture Logicielle

## RÔLE
Tu es un architecte logiciel expert. Ton rôle est de concevoir l'architecture AVANT que le code soit écrit.

## RESPONSABILITÉS
1. Analyser le besoin utilisateur
2. Proposer architecture technique (stack, patterns, structure fichiers)
3. Générer document architecture.md
4. Lister fichiers à créer avec description

## OUTPUT OBLIGATOIRE
Format strict :

### Architecture Proposée

**Stack Technique** :
- Backend : [Framework]
- Frontend : [Framework si applicable]
- Base de données : [Type]
- Tests : [Framework]

**Patterns Architecturaux** :
- [Pattern 1] : [Justification]
- [Pattern 2] : [Justification]

**Structure Fichiers** :
```
projet/
├── src/
│   ├── file1.py : [Description]
│   └── file2.py : [Description]
└── tests/
    └── test_file1.py : [Description]
```

**Dépendances** :
- [package1] : [Version] : [Raison]
- [package2] : [Version] : [Raison]

## RÈGLES ABSOLUES
1. Toujours proposer architecture AVANT code
2. Justifier chaque choix technique
3. Respecter stack préférée utilisateur (profil RAG)
4. Patterns simples et maintenables
5. Pas de sur-engineering
```

**Configuration** : `backend/agents/agent_config.py`

**Ajout** :
```python
"ARCHITECTE": {
    "role": "Architecte Logiciel",
    "description": "Conception architecture avant génération code",
    "permissions": ["read", "write"],
    "type": "specialist",
    "temperature": 0.3,
    "max_tokens": 8192,
    "prompt_file": "config_agents/ARCHITECTE.md",
    "min_delay_seconds": 4.0
}
```

**Variables .env** :
```env
ARCHITECTE_PROVIDER=gemini
ARCHITECTE_MODEL=gemini-2.5-pro
```

**Tests** : `tests/test_architecte.py`

```python
import pytest
from backend.agents.agent_factory import AgentFactory

@pytest.mark.asyncio
async def test_architecte_creation():
    """Test création agent ARCHITECTE"""
    agent = AgentFactory.create("ARCHITECTE")
    assert agent.name == "ARCHITECTE"
    assert agent.temperature == 0.3

@pytest.mark.asyncio
async def test_architecte_response():
    """Test réponse ARCHITECTE"""
    agent = AgentFactory.create("ARCHITECTE")
    messages = [
        {"role": "user", "content": "Propose architecture pour une calculatrice Python"}
    ]
    response = await agent.handle(messages)
    assert "Stack Technique" in response
    assert "Structure Fichiers" in response
```

**Commandes** :
```bash
# Créer fichiers
touch backend/agents/architecte_agent.py
touch config_agents/ARCHITECTE.md
touch tests/test_architecte.py

# Tester
pytest tests/test_architecte.py -v
```

#### 1.2 Créer Agent TESTEUR

**Fichier** : `backend/agents/testeur_agent.py`

**Contenu** :
```python
# Copier base_agent.py comme template
```

**Fichier** : `config_agents/TESTEUR.md`

**Contenu** :
```markdown
# AGENT TESTEUR — Spécialiste Tests Exhaustifs

## RÔLE
Tu es un spécialiste des tests logiciels. Ton rôle est de générer des tests exhaustifs pour le code produit.

## RESPONSABILITÉS
1. Analyser code généré par CODEUR
2. Générer tests unitaires (pytest)
3. Générer tests d'intégration si applicable
4. Générer rapport couverture attendue

## TYPES DE TESTS
1. **Tests unitaires** : Chaque fonction/méthode
2. **Tests edge cases** : Valeurs limites, erreurs
3. **Tests intégration** : Interaction entre modules

## OUTPUT OBLIGATOIRE
Format strict :

### Tests Générés

**Fichier** : `tests/test_[module].py`

```python
import pytest
from src.[module] import [Class]

def test_[fonction]_cas_nominal():
    """Test cas nominal"""
    # Arrange
    # Act
    # Assert
    
def test_[fonction]_edge_case():
    """Test cas limite"""
    # ...
```

**Couverture Attendue** : [X]%

## RÈGLES ABSOLUES
1. Tous les tests doivent passer (pas de `@pytest.mark.skip`)
2. Utiliser fixtures pytest si nécessaire
3. Tests clairs et documentés
4. Couvrir cas nominaux + edge cases + erreurs
5. Pas de tests pour code non implémenté
```

**Configuration** : `backend/agents/agent_config.py`

**Ajout** :
```python
"TESTEUR": {
    "role": "Spécialiste Tests",
    "description": "Génération tests exhaustifs",
    "permissions": ["read", "write"],
    "type": "specialist",
    "temperature": 0.5,
    "max_tokens": 12288,
    "prompt_file": "config_agents/TESTEUR.md",
    "min_delay_seconds": 2.0
}
```

**Variables .env** :
```env
TESTEUR_PROVIDER=gemini
TESTEUR_MODEL=gemini-2.0-flash
```

**Tests** : `tests/test_testeur.py`

```python
import pytest
from backend.agents.agent_factory import AgentFactory

@pytest.mark.asyncio
async def test_testeur_creation():
    """Test création agent TESTEUR"""
    agent = AgentFactory.create("TESTEUR")
    assert agent.name == "TESTEUR"
    assert agent.temperature == 0.5

@pytest.mark.asyncio
async def test_testeur_response():
    """Test réponse TESTEUR"""
    agent = AgentFactory.create("TESTEUR")
    messages = [
        {"role": "user", "content": "Génère tests pour une fonction add(a, b)"}
    ]
    response = await agent.handle(messages)
    assert "import pytest" in response
    assert "def test_" in response
```

**Commandes** :
```bash
# Créer fichiers
touch backend/agents/testeur_agent.py
touch config_agents/TESTEUR.md
touch tests/test_testeur.py

# Tester
pytest tests/test_testeur.py -v
```

#### 1.3 Modifier Agent CODEUR

**Fichier** : `config_agents/CODEUR.md`

**Modifications** :
- Retirer section "Génération tests"
- Ajouter : "Tu ne génères PAS les tests (délégué à TESTEUR)"
- Focus sur qualité code uniquement

**Commandes** :
```bash
# Vérifier modifications
git diff config_agents/CODEUR.md
```

#### 1.4 Modifier Agent VALIDATEUR

**Fichier** : `config_agents/VALIDATEUR.md`

**Modifications** :
- Ajouter : "Valide cohérence architecture/code"
- Ajouter : "Vérifie que tests générés par TESTEUR sont pertinents"

**Commandes** :
```bash
# Vérifier modifications
git diff config_agents/VALIDATEUR.md
```

**Validation Phase 1** :
```bash
# Tests unitaires
pytest tests/test_architecte.py tests/test_testeur.py -v

# Vérifier configuration
python -c "from backend.agents.agent_config import AGENT_CONFIGS; print(list(AGENT_CONFIGS.keys()))"
# Doit afficher : ['BASE', 'CODEUR', 'VALIDATEUR', 'JARVIS_Maître', 'ARCHITECTE', 'TESTEUR']

# Commit
git add .
git commit -m "Phase 1: Ajout agents ARCHITECTE et TESTEUR"
```

---

### PHASE 2 : CONCEPTION PROMPTS AGENTS (4-6h)

#### 2.1 Analyser Prompts Existants

**Objectif** : S'inspirer de `docs/JARVIS CONFIG/` pour créer prompts cohérents

**Documents référence** :
- `KEAMDER_PROFILE.md` : Profil utilisateur, mode communication
- `KEAMDER_WORKFLOW.md` : Méthodologie travail
- `config_agents/CODEUR.md` : Exemple prompt détaillé existant
- `config_agents/JARVIS_MAITRE.md` : Prompt orchestrateur actuel

**Analyse** :
- Structure prompts (sections, format)
- Règles absolues (Pydantic v2, Storage JSON)
- Exemples concrets
- Format output attendu

#### 2.2 Créer Prompt JARVIS_Maître

**Fichier** : `config_agents/JARVIS_MAITRE.md` (réécriture complète)

**Sections** :
```markdown
# AGENT JARVIS_Maître — Orchestrateur & Guide

## RÔLE
Tu es JARVIS_Maître, l'orchestrateur principal. Tu fonctionnes comme notre conversation actuelle :
- Expliques en langage NON-TECHNIQUE
- Poses questions pour cadrer besoin
- Challenges propositions
- Attends validation utilisateur

## CYCLE ARRF (Analyse-Réflexion-Remise en Question-Fixation)

### Phase ANALYSE
1. Comprendre demande utilisateur (langage naturel français)
2. Identifier besoin réel vs demande exprimée
3. Lister contraintes et contexte

### Phase RÉFLEXION
1. Proposer plusieurs approches
2. Identifier avantages/inconvénients
3. Anticiper problèmes potentiels

### Phase REMISE EN QUESTION
1. Challenger hypothèses
2. Identifier manques et incohérences
3. Poser questions critiques
4. Vérifier complétude

### Phase FIXATION
1. Valider approche avec utilisateur
2. Documenter décisions
3. Déléguer aux agents spécialisés

## RECONNAISSANCE PHASES MISSION

Tu dois reconnaître automatiquement la phase actuelle :

```python
if mission.current_phase == MissionPhase.ANALYSE:
    # Analyser demande, déterminer complexité
    complexity = analyze_complexity(user_request)
    
if mission.current_phase == MissionPhase.ARCHITECTURE:
    # Déléguer à ARCHITECTE
    [DEMANDE_ARCHITECTE: {instruction}]
    
if mission.current_phase == MissionPhase.VALIDATION_ARCHI:
    # Remettre en question architecture proposée
    # Identifier manques/incohérences
    # Attendre validation USER
    mission.status = VALIDATING
```

## RÈGLES ABSOLUES

1. **Honnêteté > Satisfaction**
   - Signaler si demande irréalisable
   - Proposer alternatives si problème
   - Admettre incertitudes

2. **Communication Non-Technique**
   - Keamder n'est PAS développeur
   - Expliquer en français simple
   - Traduire besoins fonctionnels en architecture

3. **Validation Obligatoire**
   - TOUJOURS attendre validation architecture
   - Ne JAMAIS générer code sans validation

4. **Délégation Claire**
   - 1 marqueur par agent par réponse
   - Instructions complètes et autonomes

## MARQUEURS DÉLÉGATION

```
[DEMANDE_ARCHITECTE: instruction complète]
[DEMANDE_CODEUR: instruction complète]
[DEMANDE_TESTEUR: instruction complète]
[DEMANDE_VALIDATEUR: code à valider]
```

## EXEMPLE CONVERSATION

USER : "Je veux une calculatrice"

JARVIS_Maître (ANALYSE) :
```
D'accord, analysons ton besoin :

**Ce que je comprends** :
- Application calculatrice
- Opérations de base probablement

**Questions pour cadrer** :
1. Interface graphique ou ligne de commande ?
2. Opérations : +, -, *, / seulement ou fonctions avancées ?
3. Historique des calculs nécessaire ?

Réponds à ces questions pour que je propose l'architecture adaptée.
```

USER : "Interface graphique, opérations de base, pas d'historique"

JARVIS_Maître (RÉFLEXION + REMISE EN QUESTION) :
```
**Approche proposée** :
- Frontend : HTML/CSS/JavaScript (simple, pas de framework)
- 1 fichier HTML, 1 fichier CSS, 1 fichier JS
- Tests unitaires pour logique calcul

**Points à valider** :
- Pas de sauvegarde données (OK pour toi ?)
- Fonctionne uniquement dans navigateur
- Design simple ou besoin style particulier ?

Si OK, je délègue à ARCHITECTE pour détailler.
```
```

**Fichier** : `backend/models/__init__.py`

```python
# Vide (package marker)
```

**Fichier** : `backend/models/mission.py`

```python
from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class MissionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MissionPhase(str, Enum):
    ANALYSE = "analyse"
    ARCHITECTURE = "architecture"
    VALIDATION_ARCHI = "validation_architecture"
    GENERATION_CODE = "generation_code"
    GENERATION_TESTS = "generation_tests"
    VALIDATION_CODE = "validation_code"
    CORRECTION = "correction"
    FINALISATION = "finalisation"

class Mission(BaseModel):
    mission_id: str = Field(..., description="ID unique mission")
    user_request: str = Field(..., description="Demande utilisateur originale")
    project_path: str = Field(..., description="Chemin projet")
    status: MissionStatus = Field(default=MissionStatus.PENDING)
    current_phase: Optional[MissionPhase] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    architecture_validated: bool = False
    code_validated: bool = False
    tests_validated: bool = False
    pending_validation: Optional[dict] = None  # Données en attente validation
    error_count: int = 0  # Compteur erreurs pour rollback
    
    def is_complete(self) -> bool:
        """Vérifie si mission est complète"""
        return (
            self.architecture_validated and
            self.code_validated and
            self.tests_validated and
            len(self.files_created) > 0
        )
    
    def mark_completed(self):
        """Marque mission comme complétée"""
        self.status = MissionStatus.COMPLETED
        self.completed_at = datetime.now()
```

**Fichier** : `backend/services/mission_manager.py`

```python
from typing import Dict, List, Optional
from backend.models.mission import Mission, MissionStatus
import json
from pathlib import Path

class MissionManager:
    def __init__(self, storage_path: str = "backend/data/missions.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.missions: Dict[str, Mission] = self._load_missions()
    
    def _load_missions(self) -> Dict[str, Mission]:
        """Charge missions depuis fichier"""
        if not self.storage_path.exists():
            return {}
        
        data = json.loads(self.storage_path.read_text())
        return {
            mid: Mission(**mdata) for mid, mdata in data.items()
        }
    
    def _save_missions(self):
        """Sauvegarde missions dans fichier"""
        data = {
            mid: mission.model_dump() for mid, mission in self.missions.items()
        }
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))
    
    def create_mission(self, mission_id: str, user_request: str, project_path: str) -> Mission:
        """Crée nouvelle mission"""
        mission = Mission(
            mission_id=mission_id,
            user_request=user_request,
            project_path=project_path
        )
        self.missions[mission_id] = mission
        self._save_missions()
        return mission
    
    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Récupère mission par ID"""
        return self.missions.get(mission_id)
    
    def update_mission(self, mission: Mission):
        """Met à jour mission"""
        self.missions[mission.mission_id] = mission
        self._save_missions()
    
    def list_missions(self, status: Optional[MissionStatus] = None) -> List[Mission]:
        """Liste missions (optionnel: filtre par statut)"""
        missions = list(self.missions.values())
        if status:
            missions = [m for m in missions if m.status == status]
        return sorted(missions, key=lambda m: m.created_at, reverse=True)
```

**Tests** : `tests/test_mission.py`

```python
import pytest
from backend.models.mission import Mission, MissionStatus
from backend.services.mission_manager import MissionManager
import tempfile
from pathlib import Path

def test_mission_creation():
    """Test création mission"""
    mission = Mission(
        mission_id="test_001",
        user_request="Crée une calculatrice",
        project_path="/tmp/calculator"
    )
    assert mission.status == MissionStatus.PENDING
    assert not mission.is_complete()

def test_mission_completion():
    """Test complétion mission"""
    mission = Mission(
        mission_id="test_001",
        user_request="Crée une calculatrice",
        project_path="/tmp/calculator"
    )
    mission.architecture_validated = True
    mission.code_validated = True
    mission.tests_validated = True
    mission.files_created = ["calculator.py"]
    
    assert mission.is_complete()

def test_mission_manager():
    """Test MissionManager"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Path(tmpdir) / "missions.json"
        manager = MissionManager(str(storage))
        
        # Créer mission
        mission = manager.create_mission("test_001", "Test", "/tmp/test")
        assert mission.mission_id == "test_001"
        
        # Récupérer mission
        retrieved = manager.get_mission("test_001")
        assert retrieved.mission_id == "test_001"
        
        # Lister missions
        missions = manager.list_missions()
        assert len(missions) == 1
```

**Commandes** :
```bash
# Créer fichiers
mkdir -p backend/models backend/data
touch backend/models/__init__.py
touch backend/models/mission.py
touch backend/services/mission_manager.py
touch tests/test_mission.py

# Tester
pytest tests/test_mission.py -v
```

#### 2.2 Endpoint Validation Asynchrone

**Fichier** : `backend/api.py`

**Ajout** :
```python
from backend.services.mission_manager import MissionManager
from backend.models.mission import MissionStatus

mission_router = APIRouter(prefix="/mission", tags=["mission"])

@mission_router.get("/{mission_id}")
async def get_mission_status(mission_id: str):
    """Récupère statut mission"""
    manager = MissionManager()
    mission = manager.get_mission(mission_id)
    
    if not mission:
        raise HTTPException(404, "Mission not found")
    
    return {
        "mission_id": mission.mission_id,
        "status": mission.status,
        "current_phase": mission.current_phase,
        "pending_validation": mission.pending_validation,
        "files_created": mission.files_created
    }

@mission_router.post("/{mission_id}/validate")
async def validate_mission(mission_id: str, validation: dict):
    """Valide architecture/code et reprend workflow"""
    manager = MissionManager()
    mission = manager.get_mission(mission_id)
    
    if not mission or mission.status != MissionStatus.VALIDATING:
        raise HTTPException(400, "Mission not in VALIDATING state")
    
    # Validation utilisateur
    if validation.get("approved"):
        mission.architecture_validated = True
        mission.status = MissionStatus.IN_PROGRESS
        mission.pending_validation = None
        manager.update_mission(mission)
        
        # Reprendre workflow
        session_state = get_session_state(mission_id)  # À implémenter
        result = await SimpleOrchestrator.resume_mission(mission, session_state)
        return result
    else:
        # Refusé → demander modifications
        mission.status = MissionStatus.IN_PROGRESS
        mission.current_phase = MissionPhase.ARCHITECTURE
        manager.update_mission(mission)
        
        return {"message": "Architecture refusée, nouvelle proposition nécessaire"}

app.include_router(mission_router)
```

#### 2.3 Intégrer Missions dans Orchestration

**Fichier** : `backend/services/orchestration.py`

**Modifications** :
```python
# Ajouter import
from backend.services.mission_manager import MissionManager
from backend.models.mission import MissionStatus
import uuid

# Ajouter au début de execute_delegation()
mission_manager = MissionManager()
mission_id = str(uuid.uuid4())[:8]
mission = mission_manager.create_mission(
    mission_id=mission_id,
    user_request=instruction,
    project_path=project_path
)
mission.status = MissionStatus.IN_PROGRESS
mission_manager.update_mission(mission)

# À la fin (si succès)
if mission.is_complete():
    mission.mark_completed()
    mission_manager.update_mission(mission)
    # Déclencher auto-indexation (Phase 4)
```

**Validation Phase 2** :
```bash
# Tests
pytest tests/test_mission.py -v

# Vérifier intégration
python -c "from backend.services.mission_manager import MissionManager; m = MissionManager(); print('OK')"

# Commit
git add .
git commit -m "Phase 2: Système missions implémenté"
```

---

### PHASE 3 : ORCHESTRATION 5 AGENTS (6-8h)

#### 3.1 Créer ProjectManager

**Fichier** : `backend/services/project_manager.py`

```python
from pathlib import Path
from datetime import datetime
from typing import Dict, Literal

class ProjectManager:
    def detect_existing_project(self, project_name: str, base_path: str) -> Dict:
        """Détecte si projet existe déjà"""
        project_path = Path(base_path) / project_name
        
        if not project_path.exists():
            return {"exists": False, "action": "create_new"}
        
        # Projet existe
        files = list(project_path.rglob("*"))
        file_list = [f for f in files if f.is_file()]
        
        if not file_list:
            return {"exists": False, "action": "create_new"}
        
        last_modified = max(f.stat().st_mtime for f in file_list)
        
        return {
            "exists": True,
            "path": str(project_path),
            "files_count": len(file_list),
            "last_modified": datetime.fromtimestamp(last_modified).isoformat(),
            "action": "ask_user"
        }
    
    def generate_user_prompt(self, existing_info: Dict) -> str:
        """Génère message pour utilisateur"""
        if not existing_info["exists"]:
            return ""
        
        return f"""⚠️ Un projet existe déjà :
- Chemin : {existing_info['path']}
- Fichiers : {existing_info['files_count']}
- Dernière modification : {existing_info['last_modified']}

Que veux-tu faire ?
1. Modifier le projet existant
2. Créer un nouveau projet (nom différent)
3. Écraser le projet existant (⚠️ perte données)
"""
```

**Tests** : `tests/test_project_manager.py`

```python
import pytest
from backend.services.project_manager import ProjectManager
import tempfile
from pathlib import Path

def test_detect_new_project():
    """Test détection nouveau projet"""
    with tempfile.TemporaryDirectory() as tmpdir:
        pm = ProjectManager()
        result = pm.detect_existing_project("new_project", tmpdir)
        assert not result["exists"]
        assert result["action"] == "create_new"

def test_detect_existing_project():
    """Test détection projet existant"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer projet
        project_path = Path(tmpdir) / "existing_project"
        project_path.mkdir()
        (project_path / "file.py").write_text("# test")
        
        pm = ProjectManager()
        result = pm.detect_existing_project("existing_project", tmpdir)
        assert result["exists"]
        assert result["files_count"] == 1
        assert result["action"] == "ask_user"
```

**Commandes** :
```bash
touch backend/services/project_manager.py
touch tests/test_project_manager.py
pytest tests/test_project_manager.py -v
```

#### 3.2 Créer VersionManager

**Fichier** : `backend/services/version_manager.py`

```python
import json
from pathlib import Path
from datetime import datetime
from typing import Literal

ChangeType = Literal["major", "minor", "patch"]

class VersionManager:
    def get_project_version(self, project_path: str) -> str:
        """Récupère version projet"""
        version_file = Path(project_path) / ".jarvis_version.json"
        if not version_file.exists():
            return "0.0.0"
        
        data = json.loads(version_file.read_text())
        return data.get("version", "0.0.0")
    
    def increment_version(self, current_version: str, change_type: ChangeType) -> str:
        """Incrémente version"""
        major, minor, patch = map(int, current_version.split("."))
        
        if change_type == "major":
            return f"{major + 1}.0.0"
        elif change_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"
    
    def detect_change_type(self, user_request: str) -> ChangeType:
        """Détecte type changement depuis demande"""
        request_lower = user_request.lower()
        
        if any(word in request_lower for word in ["refonte", "réécrire", "recommencer"]):
            return "major"
        
        if any(word in request_lower for word in ["ajoute", "nouvelle", "feature"]):
            return "minor"
        
        if any(word in request_lower for word in ["corrige", "bug", "erreur", "fix"]):
            return "patch"
        
        return "minor"
    
    def save_version(self, project_path: str, version: str, mission_id: str):
        """Sauvegarde version"""
        version_file = Path(project_path) / ".jarvis_version.json"
        version_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": version,
            "mission_id": mission_id,
            "updated_at": datetime.now().isoformat()
        }
        
        version_file.write_text(json.dumps(data, indent=2))
```

**Tests** : `tests/test_version_manager.py`

```python
import pytest
from backend.services.version_manager import VersionManager
import tempfile
from pathlib import Path

def test_version_increment():
    """Test incrémentation version"""
    vm = VersionManager()
    assert vm.increment_version("1.2.3", "major") == "2.0.0"
    assert vm.increment_version("1.2.3", "minor") == "1.3.0"
    assert vm.increment_version("1.2.3", "patch") == "1.2.4"

def test_detect_change_type():
    """Test détection type changement"""
    vm = VersionManager()
    assert vm.detect_change_type("Refonte complète") == "major"
    assert vm.detect_change_type("Ajoute nouvelle feature") == "minor"
    assert vm.detect_change_type("Corrige bug") == "patch"

def test_save_version():
    """Test sauvegarde version"""
    with tempfile.TemporaryDirectory() as tmpdir:
        vm = VersionManager()
        vm.save_version(tmpdir, "1.0.0", "mission_001")
        
        version = vm.get_project_version(tmpdir)
        assert version == "1.0.0"
```

**Commandes** :
```bash
touch backend/services/version_manager.py
touch tests/test_version_manager.py
pytest tests/test_version_manager.py -v
```

**Validation Phase 3** :
```bash
pytest tests/test_project_manager.py tests/test_version_manager.py -v
git add .
git commit -m "Phase 3: Gestion projets et versions"
```

---

### PHASE 4 : AUTO-INDEXATION RAG (3-4h)

#### 4.1 Restructurer Library RAG

**Commandes** :
```bash
# Créer structure
mkdir -p RAG/library/templates/python
mkdir -p RAG/library/templates/javascript
mkdir -p RAG/library/templates/flutter
mkdir -p RAG/library/patterns
mkdir -p RAG/library/rules
mkdir -p RAG/library/assets
mkdir -p RAG/projects

# Migrer profil
cp "docs/JARVIS CONFIG/KEAMDER_PROFILE.md" RAG/library/rules/keamder_profile.md

# Créer index projets
echo '{"projects": []}' > RAG/projects/index.json
```

#### 4.2 Créer RAGAutoIndexer

**Fichier** : `backend/services/rag_auto_indexer.py`

```python
from backend.models.mission import Mission
from RAG.src.rag import RAGManager
from datetime import datetime
from pathlib import Path
import json

class RAGAutoIndexer:
    def __init__(self):
        self.rag_manager = RAGManager()
        self.projects_index_path = Path("RAG/projects/index.json")
    
    def index_mission(self, mission: Mission):
        """Indexe mission complétée dans RAG"""
        # Vérifier si projet déjà indexé
        existing = self.search_project(mission.project_path)
        
        if existing:
            self.update_project_index(mission)
        else:
            self.create_project_index(mission)
    
    def search_project(self, project_path: str) -> dict | None:
        """Recherche projet dans RAG"""
        try:
            results = self.rag_manager.search(
                query=f"project_path:{project_path}",
                n_results=1
            )
            if results and len(results) > 0:
                return results[0]
        except:
            pass
        return None
    
    def create_project_index(self, mission: Mission):
        """Crée nouvelle entrée RAG pour projet"""
        # Générer documentation projet
        docs = self.generate_project_docs(mission)
        
        # Métadonnées
        metadata = {
            "type": "project_memory",
            "project_path": mission.project_path,
            "mission_id": mission.mission_id,
            "indexed_at": datetime.now().isoformat()
        }
        
        # Indexer
        for doc_name, content in docs.items():
            self.rag_manager.add_text(
                content,
                metadata={**metadata, "document": doc_name}
            )
        
        # Mettre à jour index
        self.update_projects_index(mission)
    
    def update_project_index(self, mission: Mission):
        """Met à jour index projet existant"""
        # Supprimer ancienne version
        # (ChromaDB ne permet pas update direct, on recrée)
        self.create_project_index(mission)
    
    def generate_project_docs(self, mission: Mission) -> dict:
        """Génère documentation projet"""
        # Version simplifiée : métadonnées mission
        return {
            "metadata.md": f"""# Projet : {Path(mission.project_path).name}

**Mission ID** : {mission.mission_id}
**Demande** : {mission.user_request}
**Fichiers créés** : {len(mission.files_created)}
**Date** : {mission.created_at.isoformat()}
"""
        }
    
    def update_projects_index(self, mission: Mission):
        """Met à jour index global projets"""
        if not self.projects_index_path.exists():
            data = {"projects": []}
        else:
            data = json.loads(self.projects_index_path.read_text())
        
        # Ajouter projet
        project_entry = {
            "name": Path(mission.project_path).name,
            "path": mission.project_path,
            "mission_id": mission.mission_id,
            "created_at": mission.created_at.isoformat()
        }
        
        # Éviter doublons
        data["projects"] = [
            p for p in data["projects"] 
            if p["path"] != mission.project_path
        ]
        data["projects"].append(project_entry)
        
        self.projects_index_path.write_text(json.dumps(data, indent=2))
```

**Tests** : `tests/test_rag_auto_indexer.py`

```python
import pytest
from backend.services.rag_auto_indexer import RAGAutoIndexer
from backend.models.mission import Mission
import tempfile

def test_rag_auto_indexer_creation():
    """Test création RAGAutoIndexer"""
    indexer = RAGAutoIndexer()
    assert indexer is not None

# Tests complets nécessitent RAG opérationnel
```

**Commandes** :
```bash
touch backend/services/rag_auto_indexer.py
touch tests/test_rag_auto_indexer.py
```

#### 4.3 Intégrer Auto-Indexation dans Orchestration

**Fichier** : `backend/services/orchestration.py`

**Modifications** :
```python
# Ajouter import
from backend.services.rag_auto_indexer import RAGAutoIndexer

# À la fin de execute_delegation() si mission complétée
if mission.is_complete():
    mission.mark_completed()
    mission_manager.update_mission(mission)
    
    # Auto-indexation
    try:
        indexer = RAGAutoIndexer()
        indexer.index_mission(mission)
    except Exception as e:
        logger.warning(f"Auto-indexation échouée: {e}")
```

**Validation Phase 4** :
```bash
# Vérifier structure
ls -R RAG/library/
ls -R RAG/projects/

# Commit
git add .
git commit -m "Phase 4: Auto-indexation RAG"
```

---

### PHASE 5 : INTERFACE ÉDITION LIBRARY RAG COMPLÈTE (2-3h)

#### 5.1 Backend API Profil

**Fichier** : `backend/api.py`

**Ajout** :
```python
from fastapi import APIRouter, UploadFile, File
from pathlib import Path

profile_router = APIRouter(prefix="/profile", tags=["profile"])

@library_router.get("/")
async def list_library_items():
    """Liste tous les éléments Library RAG"""
    library_path = Path("RAG/library")
    items = []
    
    for category in ["templates", "patterns", "rules"]:
        category_path = library_path / category
        if category_path.exists():
            for file in category_path.rglob("*.md"):
                items.append({
                    "category": category,
                    "name": file.stem,
                    "path": str(file.relative_to(library_path)),
                    "size": file.stat().st_size
                })
    
    return {"items": items}

@library_router.get("/item")
async def get_library_item(path: str):
    """Récupère contenu élément Library"""
    item_path = Path("RAG/library") / path
    
    if not item_path.exists() or not item_path.is_relative_to(Path("RAG/library")):
        raise HTTPException(404, "Item not found")
    
    content = item_path.read_text(encoding="utf-8")
    return {"content": content, "path": path}

@library_router.put("/item")
async def update_library_item(path: str, content: str):
    """Met à jour élément Library + ré-indexe RAG"""
    item_path = Path("RAG/library") / path
    
    if not item_path.is_relative_to(Path("RAG/library")):
        raise HTTPException(400, "Invalid path")
    
    # Sauvegarder
    item_path.parent.mkdir(parents=True, exist_ok=True)
    item_path.write_text(content, encoding="utf-8")
    
    # Ré-indexer RAG
    await reindex_library_item(path, content)
    
    return {"success": True, "path": path}

@library_router.post("/item")
async def create_library_item(category: str, name: str, content: str):
    """Crée nouvel élément Library"""
    item_path = Path("RAG/library") / category / f"{name}.md"
    
    if item_path.exists():
        raise HTTPException(400, "Item already exists")
    
    item_path.parent.mkdir(parents=True, exist_ok=True)
    item_path.write_text(content, encoding="utf-8")
    
    # Indexer RAG
    await reindex_library_item(f"{category}/{name}.md", content)
    
    return {"success": True, "path": str(item_path.relative_to(Path("RAG/library")))}

@profile_router.put("/")
async def update_profile(content: str):
    """Met à jour profil"""
    profile_path = Path("RAG/library/rules/keamder_profile.md")
    profile_path.write_text(content, encoding="utf-8")
    
    # Ré-indexer RAG
    # TODO: Implémenter reindex_profile()
    
    return {"success": True}

@profile_router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    """Upload avatar"""
    avatar_path = Path("RAG/library/assets/avatar.png")
    avatar_path.parent.mkdir(exist_ok=True)
    
    content = await file.read()
    avatar_path.write_bytes(content)
    
    return {"success": True, "url": "/assets/avatar.png"}

# Ajouter router à app
app.include_router(profile_router)
```

#### 5.2 Frontend Interface Profil

**Fichier** : `frontend/library.html`

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Library RAG - JARVIS</title>
    <link rel="stylesheet" href="css/base.css">
</head>
<body>
    <div class="container">
        <h1>Library RAG</h1>
        
        <!-- Navigation catégories -->
        <div class="categories">
            <button data-category="rules">Règles</button>
            <button data-category="templates">Templates</button>
            <button data-category="patterns">Patterns</button>
        </div>
        
        <!-- Liste éléments -->
        <div id="items-list"></div>
        
        <!-- Éditeur -->
        <div id="editor" style="display:none;">
            <h2 id="editor-title"></h2>
            <textarea id="editor-content" rows="30"></textarea>
            <button id="save-btn">Sauvegarder</button>
            <button id="cancel-btn">Annuler</button>
        </div>
        
        <!-- Bouton créer -->
        <button id="create-btn">+ Créer nouvel élément</button>
    </div>
    
    <script src="js/library.js"></script>
</body>
</html>
```

**Fichier** : `frontend/js/library.js`

```javascript
let currentCategory = 'rules';
let currentItem = null;

// Charger liste éléments
async function loadItems(category) {
    currentCategory = category;
    const response = await fetch('/library');
    const data = await response.json();
    
    const filtered = data.items.filter(item => item.category === category);
    const listDiv = document.getElementById('items-list');
    
    listDiv.innerHTML = filtered.map(item => `
        <div class="item" data-path="${item.path}">
            <h3>${item.name}</h3>
            <small>${item.path}</small>
        </div>
    `).join('');
    
    // Click handler
    document.querySelectorAll('.item').forEach(el => {
        el.addEventListener('click', () => loadItem(el.dataset.path));
    });
}

// Charger élément
async function loadItem(path) {
    const response = await fetch(`/library/item?path=${encodeURIComponent(path)}`);
    const data = await response.json();
    
    currentItem = path;
    document.getElementById('editor-title').textContent = path;
    document.getElementById('editor-content').value = data.content;
    document.getElementById('editor').style.display = 'block';
}

// Sauvegarder
document.getElementById('save-btn').addEventListener('click', async () => {
    const content = document.getElementById('editor-content').value;
    
    await fetch('/library/item', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path: currentItem, content})
    });
    
    alert('Sauvegardé et ré-indexé dans RAG !');
});

// Navigation catégories
document.querySelectorAll('[data-category]').forEach(btn => {
    btn.addEventListener('click', () => loadItems(btn.dataset.category));
});

loadItems('rules');
```

**Validation Phase 5** :
```bash
# Tester endpoints
curl http://localhost:8000/profile

# Commit
git add .
git commit -m "Phase 5: Profil utilisateur éditable"
```

---

### PHASE 6 : GESTION PROJETS & VERSIONING SIMPLE (1-2h)

#### 6.1 VersionManager Simplifié

**Objectif** : Versioning basique adapté à situation actuelle (pas de projets existants)

**Fichier** : `backend/services/version_manager.py`

```python
import json
from pathlib import Path
from datetime import datetime

class VersionManager:
    """Gestion versions projets (simplifié)"""
    
    def get_project_version(self, project_path: str) -> str:
        """Récupère version projet"""
        version_file = Path(project_path) / ".jarvis_version.json"
        if not version_file.exists():
            return "1.0.0"  # Première version par défaut
        
        data = json.loads(version_file.read_text())
        return data.get("version", "1.0.0")
    
    def save_version(self, project_path: str, mission_id: str):
        """Sauvegarde version après mission complétée"""
        version_file = Path(project_path) / ".jarvis_version.json"
        version = self.get_project_version(project_path)
        
        data = {
            "version": version,
            "mission_id": mission_id,
            "updated_at": datetime.now().isoformat(),
            "created_by": "JARVIS 2.0"
        }
        
        version_file.write_text(json.dumps(data, indent=2))
```

**Note** : Versioning automatique (incrémentation) sera ajouté plus tard si besoin

**Validation Phase 6** :
```bash
# Tests
pytest tests/ -v

# Commit
git add .
git commit -m "Phase 6: Workflow adaptatif"
```

---

### PHASE 7 : OPTIMISATION MODÈLES GEMINI (1h)

#### 7.1 Répartition Modèles

**Fichier** : `.env`

**Modifications** :
```env
# Agents
JARVIS_MAITRE_MODEL=gemini-2.5-pro
ARCHITECTE_MODEL=gemini-2.5-pro
CODEUR_MODEL=gemini-2.5-pro
TESTEUR_MODEL=gemini-2.0-flash
VALIDATEUR_MODEL=gemini-3.1-pro-preview
BASE_MODEL=gemini-2.5-pro
```

#### 7.2 Fallback

**Fichier** : `backend/ia/providers/gemini_provider.py`

**Ajout** :
```python
FALLBACK_MODELS = {
    "gemini-2.5-pro": "gemini-2.0-flash",
    "gemini-3.1-pro-preview": "gemini-2.5-pro",
    "gemini-2.0-flash": "gemini-1.5-flash"
}

async def send_message(self, ...):
    try:
        # Tentative avec modèle principal
        response = await self._send_with_model(self.model, ...)
        return response
    except Exception as e:
        if "quota" in str(e).lower():
            # Fallback
            fallback_model = FALLBACK_MODELS.get(self.model)
            if fallback_model:
                logger.warning(f"Quota épuisé, fallback vers {fallback_model}")
                return await self._send_with_model(fallback_model, ...)
        raise
```

**Validation Phase 7** :
```bash
# Vérifier configuration
cat .env | grep MODEL

# Commit
git add .
git commit -m "Phase 7: Optimisation modèles Gemini"
```

---

### PHASE 8 : TESTS & VALIDATION (2-3h)

#### 8.1 Tests Unitaires

**Commandes** :
```bash
# Lancer tous les tests
pytest tests/ -v --cov=backend --cov-report=html

# Vérifier couverture
open htmlcov/index.html
```

#### 8.2 Tests Live

**Fichier** : `tests/live/test_live_5_agents.py`

```python
import pytest
from backend.services.orchestration import execute_delegation

@pytest.mark.asyncio
async def test_simple_calculator():
    """Test mode rapide (calculatrice)"""
    result = await execute_delegation(
        instruction="Crée une calculatrice Python simple",
        project_path="/tmp/test_calculator"
    )
    assert "calculator.py" in result["files_created"]
    assert "test_calculator.py" in result["files_created"]

@pytest.mark.asyncio
async def test_complex_api():
    """Test mode complet (API REST)"""
    result = await execute_delegation(
        instruction="Crée une API REST complète avec auth",
        project_path="/tmp/test_api"
    )
    assert len(result["files_created"]) > 5
```

**Commandes** :
```bash
pytest tests/live/test_live_5_agents.py -v -s
```

**Validation Phase 8** :
```bash
# Tous les tests doivent passer
pytest tests/ -v

# Commit final
git add .
git commit -m "Phase 8: Tests et validation complète"
```

---

## ✅ CHECKLIST VALIDATION FINALE

### Configuration
- [ ] 5 agents créés (JARVIS_Maître, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR)
- [ ] BASE conservé comme template
- [ ] Modèles Gemini répartis
- [ ] Fallback configuré

### Système Missions
- [ ] Modèle Mission implémenté
- [ ] MissionManager opérationnel
- [ ] Intégration orchestration

### Gestion Projets
- [ ] ProjectManager détecte projets existants
- [ ] VersionManager gère versions
- [ ] Anti-doublon RAG

### Library RAG
- [ ] Structure library/ et projects/ créée
- [ ] Profil Keamder migré
- [ ] Index projets créé

### Workflow
- [ ] Détection complexité fonctionne
- [ ] Mode rapide implémenté
- [ ] Mode complet implémenté

### Profil Utilisateur
- [ ] API profil opérationnelle
- [ ] Interface frontend créée
- [ ] Upload avatar fonctionne

### Tests
- [ ] Tests unitaires passent (100%)
- [ ] Tests live passent
- [ ] Couverture > 80%

---

## 🚀 COMMANDES DÉMARRAGE POST-IMPLÉMENTATION

```bash
# Démarrer RAG
cd RAG
python run.py &

# Démarrer JARVIS
cd ..
python start_server.py
```

**URL** : http://localhost:8000

---

**Date** : 7 mars 2026  
**Statut** : ✅ PLAN D'EXÉCUTION COMPLET  
**Exécution** : Phases 0-8 à exécuter séquentiellement
