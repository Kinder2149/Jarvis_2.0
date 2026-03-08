# PLAN D'EXÉCUTION FINAL — JARVIS 2.0 OPTIMISATION COMPLÈTE

**Date** : 7 mars 2026  
**Statut** : ✅ VALIDÉ À 100% - PRÊT POUR EXÉCUTION  
**Objectif** : Implémentation complète système 5 agents + missions + RAG optimisé

---

## 🎯 CONTEXTE EXÉCUTION

**Exécuteur** : IA (Cascade)  
**Superviseur** : Valentin (validation uniquement)  
**Principe** : Suppression complète ancien système, nouvelle base propre

**Règles d'exécution** :
1. **Cycle ARRF** : Analyse → Réflexion → Remise en Question → Fixation
2. **Honnêteté > Satisfaction** : Signaler impossibilités, proposer alternatives
3. Configs agents dans `agent_config.py` uniquement (pas fichiers séparés)
4. Tester chaque composant après création
5. Pas de code incomplet ou commenté "TODO"
6. Commit Git après chaque phase complétée

**Décisions validées** :
- ✅ Gemini exclusif (Mistral/OpenRouter supprimés)
- ✅ Suppression complète ancien workflow (pas de migration)
- ✅ Tests existants supprimés, batterie complète recréée
- ✅ 5 agents actifs : JARVIS_Maître, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR
- ✅ BASE conservé comme template uniquement
- ✅ JARVIS_Maître fonctionne comme conversation actuelle (explications non-techniques)
- ✅ Versioning simplifié (adapté situation actuelle)
- ✅ Pas de modes rapide/complet (JARVIS décide complexité)

---

## 📋 PHASES D'EXÉCUTION

**Total estimé** : 20-25h (réaliste)

### PHASE 0 : NETTOYAGE & PRÉPARATION (1-2h)

#### 0.1 Suppression Ancien Système

**Objectif** : Nettoyer complètement traces ancien workflow

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
- ✅ Ancien système supprimé
- ✅ Tests nettoyés
- ✅ Base propre

#### 0.2 Créer Structure Dossiers

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

# Migrer profil utilisateur
cp "docs/JARVIS CONFIG/KEAMDER_PROFILE.md" RAG/library/rules/keamder_profile.md
```

**Validation Phase 0** :
```bash
# Vérifier structure
ls -R RAG/library/
ls backend/models/
ls backend/services/

# Commit
git add .
git commit -m "Phase 0: Nettoyage complet + structure dossiers"
```

---

### PHASE 1 : SYSTÈME MISSIONS & ÉTATS (2-3h)

#### 1.1 Créer Modèle Mission

**Fichier** : `backend/models/__init__.py`
```python
# Package marker
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
    VALIDATING = "validating"  # Attente validation USER
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

#### 1.2 Créer MissionManager

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
        if not self.storage_path.exists():
            return {}
        data = json.loads(self.storage_path.read_text())
        return {mid: Mission(**mdata) for mid, mdata in data.items()}
    
    def _save_missions(self):
        data = {mid: mission.model_dump() for mid, mission in self.missions.items()}
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))
    
    def create_mission(self, mission_id: str, user_request: str, project_path: str) -> Mission:
        mission = Mission(
            mission_id=mission_id,
            user_request=user_request,
            project_path=project_path
        )
        self.missions[mission_id] = mission
        self._save_missions()
        return mission
    
    def get_mission(self, mission_id: str) -> Optional[Mission]:
        return self.missions.get(mission_id)
    
    def update_mission(self, mission: Mission):
        self.missions[mission.mission_id] = mission
        self._save_missions()
```

#### 1.3 Endpoint API Validation Asynchrone

**Fichier** : `backend/api.py` (ajout)
```python
from fastapi import APIRouter, HTTPException
from backend.services.mission_manager import MissionManager
from backend.models.mission import MissionStatus

mission_router = APIRouter(prefix="/mission", tags=["mission"])

@mission_router.get("/{mission_id}")
async def get_mission_status(mission_id: str):
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
async def validate_mission(mission_id: str, approved: bool):
    manager = MissionManager()
    mission = manager.get_mission(mission_id)
    
    if not mission or mission.status != MissionStatus.VALIDATING:
        raise HTTPException(400, "Mission not in VALIDATING state")
    
    if approved:
        mission.architecture_validated = True
        mission.status = MissionStatus.IN_PROGRESS
        mission.pending_validation = None
        manager.update_mission(mission)
        return {"message": "Architecture validée, génération code en cours"}
    else:
        mission.status = MissionStatus.IN_PROGRESS
        mission.current_phase = MissionPhase.ARCHITECTURE
        manager.update_mission(mission)
        return {"message": "Architecture refusée, nouvelle proposition nécessaire"}

app.include_router(mission_router)
```

**Validation Phase 1** :
```bash
pytest tests/test_mission.py -v
git add .
git commit -m "Phase 1: Système missions + états asynchrones"
```

---

### PHASE 2 : CONCEPTION PROMPTS AGENTS (4-6h)

**Objectif** : Créer prompts ultra-détaillés inspirés de `docs/JARVIS CONFIG/`

#### 2.1 Analyser Documents Référence

**Documents à étudier** :
- `KEAMDER_PROFILE.md` : Mode communication non-technique
- `KEAMDER_WORKFLOW.md` : Méthodologie cycle ARRF
- `config_agents/CODEUR.md` : Exemple prompt détaillé existant
- `config_agents/JARVIS_MAITRE.md` : Prompt orchestrateur actuel

**Éléments à extraire** :
- Structure sections (Rôle, Responsabilités, Règles Absolues, Exemples)
- Format output attendu
- Règles spécifiques (Pydantic v2, Storage JSON)
- Style communication

#### 2.2 Créer Prompt JARVIS_Maître (Réécriture Complète)

**Fichier** : `config_agents/JARVIS_MAITRE.md`

**Longueur cible** : 800-1000 lignes

**Structure** :
```markdown
# AGENT JARVIS_Maître — Orchestrateur & Guide Conversationnel

## RÔLE

Tu es JARVIS_Maître, l'orchestrateur principal de JARVIS 2.0.

**Ton fonctionnement = Notre conversation actuelle** :
- Expliques en langage NON-TECHNIQUE (Keamder n'est PAS développeur)
- Poses questions pour cadrer besoin
- Challenges propositions pour valider
- Attends validation utilisateur avant exécution

## CYCLE ARRF (Analyse-Réflexion-Remise en Question-Fixation)

### Phase 1 : ANALYSE
1. Comprendre demande utilisateur (langage naturel français)
2. Identifier besoin réel vs demande exprimée
3. Lister contraintes et contexte

**Exemple** :
```
USER : "Je veux une calculatrice"

JARVIS_Maître (ANALYSE) :
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

### Phase 2 : RÉFLEXION
1. Proposer plusieurs approches
2. Identifier avantages/inconvénients
3. Anticiper problèmes potentiels

**Exemple** :
```
USER : "Interface graphique, opérations de base, pas d'historique"

JARVIS_Maître (RÉFLEXION) :
**Approche proposée** :
- Frontend : HTML/CSS/JavaScript (simple, pas de framework)
- 1 fichier HTML, 1 fichier CSS, 1 fichier JS
- Tests unitaires pour logique calcul

**Avantages** :
- Simple à maintenir
- Fonctionne dans navigateur
- Pas de dépendances

**Points à valider** :
- Pas de sauvegarde données (OK pour toi ?)
- Design simple ou besoin style particulier ?

Si OK, je délègue à ARCHITECTE pour détailler.
```

### Phase 3 : REMISE EN QUESTION
1. Challenger hypothèses
2. Identifier manques et incohérences
3. Poser questions critiques
4. Vérifier complétude

**Exemple** :
```
ARCHITECTE propose architecture...

JARVIS_Maître (REMISE EN QUESTION) :
J'ai analysé l'architecture proposée :

**✅ Points forts** :
- Structure claire
- Technologies adaptées

**⚠️ Points à clarifier** :
- Pas de gestion erreurs mentionnée
- Tests : seulement unitaires, pas d'intégration ?

**Questions avant validation** :
1. Comment gérer division par zéro ?
2. Validation inputs utilisateur ?

Réponds pour que je finalise l'architecture.
```

### Phase 4 : FIXATION
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
    [DEMANDE_ARCHITECTE: {instruction complète}]
    
if mission.current_phase == MissionPhase.VALIDATION_ARCHI:
    # Remettre en question architecture proposée
    # Identifier manques/incohérences
    # Attendre validation USER
    mission.status = VALIDATING
    
if mission.current_phase == MissionPhase.GENERATION_CODE:
    # Déléguer à CODEUR
    [DEMANDE_CODEUR: {instruction complète}]
```

## RÈGLES ABSOLUES

### 1. Honnêteté > Satisfaction
- ❌ Ne JAMAIS dire "oui" sans réfléchir
- ✅ Signaler si demande irréalisable
- ✅ Proposer alternatives si problème
- ✅ Admettre incertitudes

**Exemple** :
```
USER : "Crée une app complète en 5 minutes"

JARVIS_Maître :
❌ Impossible en 5 minutes.

**Estimation réaliste** :
- App simple : 2-3h
- App moyenne : 5-8h

**Alternative** :
Je peux proposer un MVP minimal (fonctionnalités essentielles) en 2h.
Veux-tu que je liste les fonctionnalités prioritaires ?
```

### 2. Communication Non-Technique
- Keamder n'est PAS développeur
- Expliquer en français simple
- Traduire besoins fonctionnels en architecture

**Exemple** :
```
❌ "On va utiliser un pattern Repository avec injection de dépendances"

✅ "On va séparer la logique métier de la base de données.
   Ça permet de changer facilement de BDD plus tard."
```

### 3. Validation Obligatoire
- TOUJOURS attendre validation architecture
- Ne JAMAIS générer code sans validation
- Mission.status = VALIDATING pendant attente

### 4. Délégation Claire
- 1 marqueur par agent par réponse
- Instructions complètes et autonomes
- Contexte suffisant pour agent

## MARQUEURS DÉLÉGATION

```
[DEMANDE_ARCHITECTE: instruction complète avec contexte]
[DEMANDE_CODEUR: instruction complète avec architecture validée]
[DEMANDE_TESTEUR: code à tester + couverture attendue]
[DEMANDE_VALIDATEUR: code + tests à valider]
```

## WORKFLOW COMPLET EXEMPLE

[Inclure exemple complet calculatrice avec toutes les phases]

## GESTION ERREURS

Si mission.error_count >= 3:
- Marquer Mission.status = FAILED
- Expliquer problème en langage simple
- Proposer rollback ou correction manuelle

## PROFIL UTILISATEUR (Keamder)

[Résumé KEAMDER_PROFILE.md]
- Non-codeur, pilote IA à 100%
- Communication en français naturel
- Besoin explications simples
- Préfère précision > rapidité
```

#### 2.3 Créer Prompt ARCHITECTE

**Fichier** : `config_agents/ARCHITECTE.md`

**Longueur cible** : 600-800 lignes

**Structure** :
```markdown
# AGENT ARCHITECTE — Conception Architecture Logicielle

## RÔLE
Architecte logiciel expert. Phases ANALYSE + RÉFLEXION du cycle ARRF.

## RESPONSABILITÉS
1. Analyser besoin technique
2. Proposer stack adaptée (référence KEAMDER_PROFILE)
3. Justifier choix
4. Générer documentation architecture

## STACK PRÉFÉRÉE KEAMDER

**Frontend** :
- HTML/CSS/JavaScript (projets simples)
- React + TailwindCSS (projets moyens/complexes)

**Backend** :
- Python + FastAPI (préférence)
- Node.js + Express (si frontend JS/TS)

**Base de données** :
- SQLite (projets simples/locaux)
- PostgreSQL (production)

**Tests** :
- pytest (Python)
- Jest (JavaScript/TypeScript)

## OUTPUT OBLIGATOIRE

Format strict :

### Architecture Proposée

**Complexité détectée** : [SIMPLE / MEDIUM / COMPLEX]

**Stack Technique** :
- Backend : [Framework + version]
- Frontend : [Framework si applicable]
- Base de données : [Type + justification]
- Tests : [Framework]

**Patterns Architecturaux** :
- [Pattern 1] : [Justification]

**Structure Fichiers** :
```
projet/
├── src/
│   ├── file1.py : [Description précise]
│   └── file2.py : [Description précise]
└── tests/
    └── test_file1.py : [Description]
```

**Dépendances** :
- [package1]==[version] : [Raison]

**Fichier architecture.md** :
[Contenu complet architecture.md]

## RÈGLES ABSOLUES
1. Architecture AVANT code
2. Justifier chaque choix
3. Respecter stack préférée
4. Patterns simples
5. Pas de sur-engineering

## EXEMPLES
[3-4 exemples concrets]
```

#### 2.4 Créer Prompt TESTEUR

**Fichier** : `config_agents/TESTEUR.md`

**Longueur cible** : 600-800 lignes

**Structure similaire avec focus tests exhaustifs**

#### 2.5 Modifier Prompts Existants

**CODEUR** : Retirer génération tests, focus code uniquement
**VALIDATEUR** : Ajouter validation architecture + cohérence

**Validation Phase 2** :
```bash
# Vérifier prompts créés
ls -lh config_agents/
wc -l config_agents/*.md

git add .
git commit -m "Phase 2: Prompts agents ultra-détaillés"
```

---

### PHASE 3 : CONFIGURATION AGENTS (1h)

#### 3.1 Ajouter Configs dans agent_config.py

**Fichier** : `backend/agents/agent_config.py`

**Ajouts** :
```python
AGENT_CONFIGS = {
    # ... existants ...
    
    "ARCHITECTE": {
        "name": "ARCHITECTE",
        "role": "Architecte Logiciel",
        "description": "Conception architecture AVANT code (Analyse + Réflexion)",
        "permissions": ["read", "write"],
        "type": "specialist",
        "temperature": 0.3,
        "max_tokens": 8192,
        "prompt_file": "config_agents/ARCHITECTE.md",
        "min_delay_seconds": 4.0
    },
    
    "TESTEUR": {
        "name": "TESTEUR",
        "role": "Spécialiste Tests",
        "description": "Génération tests exhaustifs (Réflexion + Fixation)",
        "permissions": ["read", "write"],
        "type": "specialist",
        "temperature": 0.5,
        "max_tokens": 12288,
        "prompt_file": "config_agents/TESTEUR.md",
        "min_delay_seconds": 2.0
    }
}
```

**Validation Phase 3** :
```bash
python -c "from backend.agents.agent_config import AGENT_CONFIGS; print(list(AGENT_CONFIGS.keys()))"
# Doit afficher : ['BASE', 'CODEUR', 'VALIDATEUR', 'JARVIS_Maître', 'ARCHITECTE', 'TESTEUR']

git add .
git commit -m "Phase 3: Configuration 5 agents"
```

---

### PHASE 4 : ORCHESTRATION 5 AGENTS (6-8h)

#### 4.1 Créer Nouvelle Orchestration

**Fichier** : `backend/services/orchestration.py` (nouveau)

**Contenu** :
```python
import logging
from backend.agents.agent_factory import get_agent
from backend.models.mission import Mission, MissionStatus, MissionPhase
from backend.services.mission_manager import MissionManager
from backend.services.rag_service import get_rag_service
import uuid

logger = logging.getLogger(__name__)

class MissionOrchestrator:
    """Orchestrateur missions avec workflow 5 agents"""
    
    @staticmethod
    async def execute_mission(user_request: str, project_path: str) -> dict:
        """Point d'entrée principal"""
        mission_manager = MissionManager()
        mission_id = str(uuid.uuid4())[:8]
        
        mission = mission_manager.create_mission(
            mission_id=mission_id,
            user_request=user_request,
            project_path=project_path
        )
        
        try:
            # Phase 1 : ANALYSE
            result = await MissionOrchestrator.phase_analyse(mission)
            if result.get("status") == "awaiting_validation":
                return result
            
            # Phase 2 : ARCHITECTURE
            result = await MissionOrchestrator.phase_architecture(mission)
            if result.get("status") == "awaiting_validation":
                return result
            
            # Phase 3 : GÉNÉRATION CODE
            result = await MissionOrchestrator.phase_generation_code(mission)
            
            # Phase 4 : GÉNÉRATION TESTS
            result = await MissionOrchestrator.phase_generation_tests(mission)
            
            # Phase 5 : VALIDATION
            result = await MissionOrchestrator.phase_validation(mission)
            
            # Phase 6 : FINALISATION
            if mission.is_complete():
                mission.mark_completed()
                mission_manager.update_mission(mission)
                return {"status": "completed", "mission_id": mission_id}
            
        except Exception as e:
            mission.mark_failed(str(e))
            mission_manager.update_mission(mission)
            return {"status": "failed", "error": str(e)}
    
    @staticmethod
    async def phase_analyse(mission: Mission) -> dict:
        """Phase ANALYSE par JARVIS_Maître"""
        mission.current_phase = MissionPhase.ANALYSE
        jarvis = get_agent("JARVIS_Maître")
        
        prompt = f"""
Analyse cette demande utilisateur :

{mission.user_request}

Applique la phase ANALYSE du cycle ARRF :
1. Comprendre besoin réel
2. Poser questions pour cadrer
3. Déterminer complexité (SIMPLE/MEDIUM/COMPLEX)

Réponds en langage NON-TECHNIQUE.
"""
        
        response = await jarvis.handle([{"role": "user", "content": prompt}])
        return {"status": "continue", "analysis": response}
    
    @staticmethod
    async def phase_architecture(mission: Mission) -> dict:
        """Phase ARCHITECTURE par ARCHITECTE"""
        mission.current_phase = MissionPhase.ARCHITECTURE
        architecte = get_agent("ARCHITECTE")
        
        # Enrichir avec RAG
        rag_service = get_rag_service()
        context = await rag_service.enrich_instruction(mission.user_request)
        
        prompt = f"""
Conçois l'architecture pour :

{mission.user_request}

Contexte RAG :
{context}

Génère architecture complète selon format obligatoire.
"""
        
        architecture = await architecte.handle([{"role": "user", "content": prompt}])
        
        # Attendre validation USER
        mission.status = MissionStatus.VALIDATING
        mission.current_phase = MissionPhase.VALIDATION_ARCHI
        mission.pending_validation = {"type": "architecture", "content": architecture}
        
        MissionManager().update_mission(mission)
        
        return {
            "status": "awaiting_validation",
            "mission_id": mission.mission_id,
            "architecture": architecture
        }
    
    # ... autres phases ...
```

**Validation Phase 4** :
```bash
pytest tests/test_orchestration.py -v
git add .
git commit -m "Phase 4: Orchestration 5 agents complète"
```

---

### PHASE 5 : INTÉGRATION FRONTEND (3-4h)

**Analyse frontend actuel** :
- ✅ Architecture SPA (Single Page Application)
- ✅ Router existant (`/`, `/chat`, `/projects`, `/agents`, `/library`)
- ✅ Composants modulaires (navbar, views)
- ✅ API client centralisé
- ✅ Thème sombre cohérent

**Intégrations nécessaires** :

#### 5.1 Nouvelle Vue Missions

**Fichier** : `frontend/js/views/missions.js`

```javascript
class MissionsView {
    async render(container) {
        // Liste missions en cours
        // Statut temps réel
        // Bouton validation architecture
    }
    
    async renderMissionDetail(missionId) {
        // Détail mission
        // Phases progression
        // Validation architecture si VALIDATING
    }
}
```

#### 5.2 Modifier Navbar

**Fichier** : `frontend/js/components/navbar.js`

**Ajout** :
```javascript
{ path: '/missions', label: 'Missions', icon: '🎯' }
```

#### 5.3 Modifier Library View

**Fichier** : `frontend/js/views/library.js`

**Ajout** : Édition complète Library (templates, patterns, rules)

**Validation Phase 5** :
```bash
# Tester frontend
# Ouvrir http://localhost:8000

git add .
git commit -m "Phase 5: Intégration frontend missions + library éditable"
```

---

### PHASE 6 : AUTO-INDEXATION RAG (2-3h)

#### 6.1 RAGAutoIndexer

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
            self.rag_manager.add_text(content, metadata={**metadata, "document": doc_name})
        
        # Mettre à jour index
        self.update_projects_index(mission)
```

**Validation Phase 6** :
```bash
pytest tests/test_rag_auto_indexer.py -v
git add .
git commit -m "Phase 6: Auto-indexation RAG"
```

---

### PHASE 7 : VERSIONING SIMPLIFIÉ (1h)

**Fichier** : `backend/services/version_manager.py`

```python
class VersionManager:
    def get_project_version(self, project_path: str) -> str:
        version_file = Path(project_path) / ".jarvis_version.json"
        if not version_file.exists():
            return "1.0.0"
        data = json.loads(version_file.read_text())
        return data.get("version", "1.0.0")
    
    def save_version(self, project_path: str, mission_id: str):
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

---

### PHASE 8 : TESTS COMPLETS (3-4h)

#### 8.1 Créer Batterie Tests

**Tests unitaires** :
- `tests/test_mission.py` : Modèle Mission
- `tests/test_mission_manager.py` : MissionManager
- `tests/test_orchestration.py` : Orchestration 5 agents
- `tests/test_rag_auto_indexer.py` : Auto-indexation
- `tests/test_version_manager.py` : Versioning

**Tests intégration** :
- `tests/integration/test_workflow_complet.py` : Workflow end-to-end

**Tests live** :
- `tests/live/test_live_calculatrice.py` : Projet simple
- `tests/live/test_live_api.py` : Projet moyen

#### 8.2 Exécution Tests Live

**À la toute fin, par Valentin** :
```bash
# Démarrer JARVIS
python start_server.py

# Dans autre terminal
pytest tests/live/ -v -s
```

**Validation Phase 8** :
```bash
pytest tests/ -v --cov=backend --cov-report=html
git add .
git commit -m "Phase 8: Batterie tests complète"
```

---

## ✅ CHECKLIST VALIDATION FINALE

### Configuration
- [ ] 5 agents configurés (JARVIS_Maître, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR)
- [ ] BASE conservé comme template
- [ ] Modèles Gemini répartis
- [ ] .env.example à jour

### Système Missions
- [ ] Modèle Mission implémenté
- [ ] MissionManager opérationnel
- [ ] Endpoints API validation asynchrone

### Prompts
- [ ] JARVIS_Maître : 800-1000 lignes (conversationnel)
- [ ] ARCHITECTE : 600-800 lignes
- [ ] TESTEUR : 600-800 lignes
- [ ] CODEUR : Modifié (pas de tests)
- [ ] VALIDATEUR : Modifié (validation architecture)

### Orchestration
- [ ] Workflow 5 agents implémenté
- [ ] Reconnaissance phases automatique
- [ ] Gestion erreurs + rollback

### Frontend
- [ ] Vue Missions créée
- [ ] Library éditable complète
- [ ] Navbar mise à jour

### RAG
- [ ] Auto-indexation opérationnelle
- [ ] Library restructurée
- [ ] Profil Keamder migré

### Tests
- [ ] Ancien système supprimé
- [ ] Batterie complète créée
- [ ] Tests unitaires passent
- [ ] Tests live validés par Valentin

---

## 🚀 COMMANDES DÉMARRAGE POST-IMPLÉMENTATION

```bash
# Copier .env
cp .env.example .env
# Éditer .env et ajouter GEMINI_API_KEY

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
**Statut** : ✅ PLAN VALIDÉ À 100%  
**Prêt pour exécution** : OUI
