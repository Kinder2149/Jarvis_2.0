# MISSION : RÉORGANISATION COMPLÈTE LIBRAIRIE RAG — JARVIS 2.0

**Date** : 5 mars 2026  
**Statut** : WORK  
**Objectif** : Audit complet, remise en question et réorganisation personnalisée de la librairie RAG

---

## 📋 SOMMAIRE

1. [Analyse Technique du Système Actuel](#1-analyse-technique-du-système-actuel)
2. [Inventaire Complet des Documents](#2-inventaire-complet-des-documents)
3. [Contexte Utilisateur : Val C.](#3-contexte-utilisateur--val-c)
4. [Audit Critique de l'Organisation Actuelle](#4-audit-critique-de-lorganisation-actuelle)
5. [Proposition de Réorganisation Complète](#5-proposition-de-réorganisation-complète)
6. [Plan d'Action](#6-plan-daction)

---

## 1. ANALYSE TECHNIQUE DU SYSTÈME ACTUEL

### 1.1 Architecture RAG

**Composants identifiés** :

#### Backend JARVIS (FastAPI)
- **`backend/db/database.py`** : Couche SQLite async
  - Table `library_documents` (id, category, name, icon, description, content, tags, agents, created_at, updated_at)
  - CRUD complet : create, get, list (avec filtres), update, delete
  - Seed automatique depuis `library_seed.json` au premier démarrage
  
- **`backend/db/library_seed.json`** : 12 documents initiaux
  - 5 libraries (FastAPI, Pytest, Pydantic, aiosqlite, Flutter)
  - 3 methodologies (Audit>Plan>Exécution, Gouvernance doc, Revue code)
  - 3 prompts (Délégation CODEUR, Vérification BASE, Création projet)
  - 2 personal (Conventions code, Stack technique)

- **`backend/api.py`** : Routes REST
  - `GET /api/library` : Liste documents (filtres : category, agent, tag, search)
  - `GET /api/library/{doc_id}` : Récupère un document
  - `POST /api/library` : Crée un document
  - `PUT /api/library/{doc_id}` : Met à jour un document
  - `DELETE /api/library/{doc_id}` : Supprime un document

- **`backend/services/function_executor.py`** : Fonctions pour agents
  - `get_library_document(name, category)` : Recherche par nom (exact ou proche)
  - `get_library_list(category, agent)` : Liste documents filtrés
  - Utilisé par BASE via function calling

- **`backend/services/rag_service.py`** : Client API RAG externe
  - `check_health()` : Vérifie disponibilité API RAG (localhost:5001)
  - `search_documents(query, n_results, filter_metadata)` : Recherche vectorielle
  - `get_context(query, n_results, filter_metadata)` : Contexte formaté
  - `enrich_instruction(instruction, n_results, filter_metadata)` : Enrichit instruction avec contexte
  - **Utilisé dans orchestration** : Enrichit instructions CODEUR si API RAG disponible

#### API RAG Standalone (Flask)
- **`RAG/src/rag.py`** : Gestionnaire RAG complet
  - **DocumentLoader** : Charge .txt, .md, .pdf, .docx
  - **TextSplitter** : Découpe en chunks (1000 chars, overlap 200)
  - **RAGManager** : ChromaDB + SentenceTransformer (all-MiniLM-L6-v2)
  - Méthodes : add_document, add_text, search, get_context_for_query

- **`RAG/src/main.py`** : API Flask (port 5001)
  - Routes : `/`, `/rag/search`, `/rag/context`, `/rag/documents`, `/rag/collection/*`
  - Initialisation : collection `jarvis_library`, persist `./data/rag_db`

- **`RAG/index_jarvis_library.py`** : Script d'indexation
  - Lit `backend/db/library_seed.json`
  - Indexe chaque document dans ChromaDB via API
  - Métadonnées : name, category, agent, tags

#### Frontend (JavaScript vanilla)
- **`frontend/js/views/library.js`** : Page Librairie
  - Données hardcodées (LIBRARY_CATEGORIES) — **DOUBLON avec library_seed.json**
  - 4 catégories : libraries, methodologies, prompts, personal
  - Filtres par catégorie
  - Modal de détail pour chaque document
  - **Pas de connexion à l'API backend** — données statiques uniquement

### 1.2 Flux de Données

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR (Frontend)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌────────────────┐      ┌────────────────┐
│  Page Library  │      │  Mode Projet   │
│  (statique)    │      │  (API /chat)   │
└────────────────┘      └────────┬───────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Backend FastAPI       │
                    │  /api/chat             │
                    └────────┬───────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────┐    ┌──────────────────────┐
    │ Orchestration     │    │ Function Executor    │
    │ (JARVIS_Maître)   │    │ (BASE agent)         │
    └────────┬──────────┘    └──────────┬───────────┘
             │                           │
             │ enrich_instruction()      │ get_library_document()
             │                           │ get_library_list()
             ▼                           ▼
    ┌──────────────────┐       ┌──────────────────┐
    │  RAG Service     │       │  Database        │
    │  (API externe)   │       │  (SQLite)        │
    └──────────────────┘       └──────────────────┘
             │                           │
             ▼                           ▼
    ┌──────────────────┐       ┌──────────────────┐
    │  ChromaDB        │       │ library_documents│
    │  (vectoriel)     │       │ (12 docs seed)   │
    └──────────────────┘       └──────────────────┘
```

### 1.3 Utilisation Actuelle

**Agents qui utilisent la librairie** :

1. **BASE** (via function calling)
   - `get_library_document` : Recherche un document par nom
   - `get_library_list` : Liste documents filtrés
   - Cas d'usage : Consulter méthodologies, conventions, prompts

2. **CODEUR** (via enrichissement RAG)
   - Orchestration enrichit automatiquement les instructions avec contexte RAG
   - Filtre : `{"agent": "CODEUR"}`
   - Top 3 documents pertinents ajoutés au prompt
   - **Condition** : API RAG disponible (localhost:5001)

3. **JARVIS_Maître** (indirect)
   - Ne consulte pas directement la librairie
   - Délègue à BASE pour consultation

**Utilisateur** :
- Page Library frontend (lecture seule, données statiques)
- Aucune édition possible via UI

---

## 2. INVENTAIRE COMPLET DES DOCUMENTS

### 2.1 Documents dans library_seed.json (12 total)

#### Catégorie : libraries (5 docs)
| Nom | Icon | Tags | Agents | Contenu |
|-----|------|------|--------|---------|
| FastAPI | ⚡ | python, web, api | CODEUR, BASE | Installation, app base, middleware, query params, tests |
| Pytest | 🧪 | python, testing | CODEUR, BASE | Installation, tests basiques, fixtures, tmp_path, parametrize |
| Pydantic | 📋 | python, validation | CODEUR | Modèle base, utilisation, validators (Pydantic v2) |
| aiosqlite | 🗃️ | python, database, async | CODEUR | Installation, connexion, requêtes async |
| Flutter | 🐦 | flutter, dart, mobile | CODEUR | Nouveau projet, widgets stateless/stateful, navigation, HTTP |

#### Catégorie : methodologies (3 docs)
| Nom | Icon | Tags | Agents | Contenu |
|-----|------|------|--------|---------|
| Audit > Plan > Exécution | 🎯 | process, core | JARVIS_Maitre | 5 phases : Audit, Plan, Validation, Exécution, Documentation |
| Gouvernance documentaire | 📁 | process, documentation | JARVIS_Maitre, BASE | Arborescence docs/, règles entrée/sortie, conventions |
| Revue de code | 🔍 | process, quality | BASE | Checklist : structure, qualité, tests, complétude |

#### Catégorie : prompts (3 docs)
| Nom | Icon | Tags | Agents | Contenu |
|-----|------|------|--------|---------|
| Délégation au CODEUR | ➡️ | inter-agent, delegation | JARVIS_Maitre | Format marqueur [DEMANDE_CODE_CODEUR: ...], règles, exemple |
| Vérification par BASE | ✅ | inter-agent, verification | JARVIS_Maitre | Format marqueur [DEMANDE_VALIDATION_BASE: ...], réponse attendue |
| Création de projet | 🆕 | user, project | JARVIS_Maitre | Template prompt création projet, conseils |

#### Catégorie : personal (2 docs)
| Nom | Icon | Tags | Agents | Contenu |
|-----|------|------|--------|---------|
| Conventions de code | 📝 | style, rules | CODEUR, JARVIS_Maitre, BASE | Python, JavaScript, structure projet, tests |
| Stack technique | 🛠️ | tech, preferences | JARVIS_Maitre, CODEUR | Backend (Python, FastAPI), Frontend (vanilla JS), Mobile (Flutter), Outils |

### 2.2 Documents Hardcodés dans Frontend (12 total)

**CONSTAT** : Doublon exact avec library_seed.json
- Même structure, mêmes contenus
- Frontend ne lit PAS la base de données
- Maintenance en double nécessaire

### 2.3 Documents dans ChromaDB (si indexés)

**État inconnu** — nécessite vérification :
- API RAG disponible ?
- Documents indexés ?
- Dernière indexation ?

---

## 3. CONTEXTE UTILISATEUR : VAL C.

### 3.1 Profil Technique

**Compétences** :
- **Python** : Niveau avancé (FastAPI, async, Pydantic v2, pytest)
- **JavaScript** : Vanilla JS, ES6 modules, pas de frameworks
- **Flutter/Dart** : En apprentissage
- **Bases de données** : SQLite, aiosqlite
- **IA/LLM** : Intégration Gemini, OpenRouter, architecture multi-agents
- **Outils** : Git, VS Code/Windsurf, Windows

**Stack préférée** :
- Backend : Python 3.11+, FastAPI, SQLite
- Frontend : HTML/CSS/JS vanilla (pas React/Vue/Angular)
- Mobile : Flutter (apprentissage)
- IA : Gemini (orchestration), OpenRouter (workers)
- Hébergement : Local uniquement (localhost:8000)

### 3.2 Méthodes de Travail

**Méthodologie stricte** :
1. **Audit** : Analyse existant, dette technique, fichiers impactés
2. **Plan** : Décomposition étapes, fichiers, dépendances, risques
3. **Validation** : Attente accord explicite avant exécution
4. **Exécution** : Étape par étape, tests après chaque étape
5. **Documentation** : MAJ docs, archivage obsolètes, CHANGELOG

**Gouvernance documentaire** :
- `docs/reference/` : Source de vérité (gelé, versionné)
- `docs/work/` : Documents en cours (YYYYMMDD_NOM.md)
- `docs/history/` : Archive lecture seule
- `docs/_meta/` : Index, règles, changelog
- **Principe** : 1 sujet = 1 document de référence

**Conventions code** :
- Python : Imports absolus simples, PascalCase classes, snake_case fonctions, type hints, docstrings
- JavaScript : ES6, camelCase, const par défaut, template literals
- Tests : pytest, fixtures, tmp_path, nommage test_[module].py
- Structure : src/, tests/, docs/, requirements.txt

### 3.3 Besoins et Objectifs

**Vision JARVIS 2.0** :
- Cockpit personnel no-code pour construire des projets logiciels
- 2 modes : Chat (conversation libre) / Projet (workflow structuré)
- Orchestration multi-agents (JARVIS_Maître, BASE, CODEUR, VALIDATEUR)
- Garde-fou méthodologique (pas de décision autonome)

**Besoins librairie** :
1. **Personnalisation** : Refléter mes méthodes, conventions, stack
2. **Accessibilité** : Agents doivent consulter facilement
3. **Évolutivité** : Ajouter/modifier documents simplement
4. **Cohérence** : Une seule source de vérité
5. **Performance** : Recherche rapide et pertinente

**Ce que je fais faire à l'IA** :
- Génération de code (CODEUR)
- Validation complétude (BASE)
- Orchestration workflow (JARVIS_Maître)
- Respect méthodologie et conventions
- Pas de décisions architecturales sans validation

### 3.4 Habitudes et Préférences

**Organisation** :
- Clarté > Complexité
- Documentation structurée et versionnée
- Pas de redondance (DRY pour les docs aussi)
- Traçabilité complète (logs, changelog, history)

**Communication IA** :
- Français uniquement
- Factuel, structuré, sans extrapolation
- Jamais de décision autonome
- Challenge si ambiguïté
- Exécution disciplinée (pas d'initiative)

**Workflow** :
- Travail par sessions (docs work/ datés)
- Consolidation régulière (work → reference)
- Archivage systématique (reference → history)
- Tests avant validation

---

## 4. AUDIT CRITIQUE DE L'ORGANISATION ACTUELLE

### 4.1 Points Forts ✅

1. **Architecture technique solide**
   - Séparation claire backend/RAG/frontend
   - API REST complète et fonctionnelle
   - ChromaDB pour recherche vectorielle
   - Function calling pour agents

2. **Seed initial cohérent**
   - 12 documents bien catégorisés
   - Contenu pertinent et utile
   - Métadonnées (tags, agents) exploitables

3. **Intégration orchestration**
   - Enrichissement automatique CODEUR
   - Consultation BASE via functions
   - Filtre par agent fonctionnel

### 4.2 Problèmes Critiques ❌

#### P1 : DOUBLON FRONTEND/BACKEND
**Gravité** : 🔴 CRITIQUE  
**Impact** : Maintenance double, incohérence garantie

- Frontend hardcode les 12 documents
- Backend stocke les mêmes en BDD
- Aucune synchronisation
- Modification = 2 endroits à changer

**Conséquence** :
- Risque de désynchronisation
- Perte de temps
- Source de bugs

#### P2 : FRONTEND DÉCONNECTÉ
**Gravité** : 🔴 CRITIQUE  
**Impact** : Page Library inutilisable pour gestion

- Page Library = lecture seule statique
- Pas d'appel API backend
- Impossible d'ajouter/modifier documents via UI
- Utilisateur ne voit pas les vrais documents BDD

**Conséquence** :
- Gestion manuelle obligatoire (SQL ou seed.json)
- Pas d'interface utilisateur fonctionnelle
- Frustration utilisateur

#### P3 : API RAG EXTERNE NON FIABLE
**Gravité** : 🟠 ÉLEVÉE  
**Impact** : Enrichissement CODEUR aléatoire

- API RAG = processus séparé (localhost:5001)
- Doit être lancée manuellement
- Si non disponible : enrichissement désactivé silencieusement
- Pas de monitoring/alerte

**Conséquence** :
- CODEUR reçoit contexte incomplet
- Qualité code variable selon état API
- Debugging difficile

#### P4 : CATÉGORISATION LIMITÉE
**Gravité** : 🟡 MOYENNE  
**Impact** : Organisation peu flexible

- 4 catégories fixes (libraries, methodologies, prompts, personal)
- Pas de sous-catégories
- Pas de hiérarchie
- Difficile d'organiser >50 documents

**Conséquence** :
- Scalabilité limitée
- Recherche moins précise
- Organisation rigide

#### P5 : CONTENU INCOMPLET
**Gravité** : 🟡 MOYENNE  
**Impact** : Librairie pas personnalisée

**Manque** :
- Règles absolues (Storage JSON, Pydantic v2, Cohérence, Tests)
- Méthodologie documentaire complète
- Templates projets (Calculator, TODO, MiniBlog)
- Patterns récurrents (error handling, async, etc.)
- Contexte Val C. (profil, objectifs, contraintes)
- Historique décisions architecturales

**Conséquence** :
- Agents manquent de contexte
- Répétition erreurs connues
- Pas de mémoire projet

#### P6 : MÉTADONNÉES SOUS-EXPLOITÉES
**Gravité** : 🟡 MOYENNE  
**Impact** : Recherche peu intelligente

- Tags présents mais pas utilisés pour recherche
- Pas de priorité/importance
- Pas de date dernière utilisation
- Pas de compteur utilisation
- Pas de feedback qualité

**Conséquence** :
- Recherche basique
- Pas d'amélioration continue
- Pas de métriques

### 4.3 Opportunités Manquées 💡

1. **Pas de versioning documents**
   - Impossible de revenir en arrière
   - Pas d'historique modifications
   - Pas de diff

2. **Pas de templates réutilisables**
   - Chaque document créé from scratch
   - Pas de structure standard
   - Pas de validation format

3. **Pas de liens entre documents**
   - Documents isolés
   - Pas de graphe de connaissances
   - Pas de "voir aussi"

4. **Pas d'analytics**
   - Quels documents utilisés ?
   - Lesquels utiles ?
   - Lesquels obsolètes ?

5. **Pas d'import/export**
   - Difficile de partager
   - Pas de backup facile
   - Pas de migration

---

## 5. PROPOSITION DE RÉORGANISATION COMPLÈTE

### 5.1 Principes Directeurs

1. **Source unique de vérité** : Backend SQLite = référence
2. **Frontend connecté** : Lecture/écriture via API
3. **RAG intégré** : Pas de processus externe
4. **Personnalisation maximale** : Refléter Val C.
5. **Évolutivité** : Scalable à 100+ documents
6. **Traçabilité** : Versioning, logs, métriques

### 5.2 Architecture Cible

```
┌──────────────────────────────────────────────────────────┐
│                  UTILISATEUR (Frontend)                   │
│  - Page Library (CRUD complet)                           │
│  - Recherche vectorielle intégrée                        │
│  - Prévisualisation markdown                             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Backend FastAPI           │
        │  - API REST /api/library   │
        │  - RAG Service intégré     │
        │  - Versioning documents    │
        └────────┬───────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌─────────────────┐   ┌──────────────────┐
│  SQLite         │   │  ChromaDB        │
│  - Documents    │   │  - Embeddings    │
│  - Versions     │   │  - Search        │
│  - Métriques    │   │  (intégré)       │
└─────────────────┘   └──────────────────┘
```

### 5.3 Nouvelle Structure Documents

#### Catégories Principales (7)

1. **`core`** : Règles absolues, principes fondamentaux
2. **`methodologies`** : Processus, workflows, méthodologies
3. **`libraries`** : Documentation librairies/frameworks
4. **`patterns`** : Patterns code, architectures, best practices
5. **`templates`** : Templates projets, fichiers types
6. **`prompts`** : Prompts agents, instructions types
7. **`context`** : Contexte Val C., décisions, historique

#### Sous-catégories (exemples)

- `core/rules` : Règles absolues
- `core/conventions` : Conventions code
- `methodologies/project` : Méthodologies projet
- `methodologies/documentation` : Méthodologies doc
- `libraries/python` : Librairies Python
- `libraries/javascript` : Librairies JavaScript
- `patterns/python` : Patterns Python
- `patterns/architecture` : Patterns architecture
- `templates/projects` : Templates projets complets
- `templates/files` : Templates fichiers individuels
- `prompts/inter-agent` : Communication agents
- `prompts/user` : Prompts utilisateur
- `context/profile` : Profil Val C.
- `context/decisions` : Décisions architecturales

### 5.4 Schéma BDD Amélioré

```sql
-- Table principale (existante + ajouts)
CREATE TABLE library_documents (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    subcategory TEXT,  -- NOUVEAU
    name TEXT NOT NULL,
    icon TEXT,
    description TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,  -- JSON array
    agents TEXT,  -- JSON array
    priority INTEGER DEFAULT 5,  -- NOUVEAU (1=max, 10=min)
    version INTEGER DEFAULT 1,  -- NOUVEAU
    parent_id TEXT,  -- NOUVEAU (pour versioning)
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_used_at TEXT,  -- NOUVEAU
    usage_count INTEGER DEFAULT 0,  -- NOUVEAU
    FOREIGN KEY (parent_id) REFERENCES library_documents(id)
);

-- Table versions (NOUVEAU)
CREATE TABLE library_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT,  -- 'user' ou 'agent_name'
    change_summary TEXT,
    FOREIGN KEY (document_id) REFERENCES library_documents(id),
    UNIQUE(document_id, version)
);

-- Table métriques (NOUVEAU)
CREATE TABLE library_metrics (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    used_at TEXT NOT NULL,
    context TEXT,  -- Contexte utilisation
    helpful BOOLEAN,  -- Feedback optionnel
    FOREIGN KEY (document_id) REFERENCES library_documents(id)
);

-- Index
CREATE INDEX idx_category ON library_documents(category);
CREATE INDEX idx_subcategory ON library_documents(subcategory);
CREATE INDEX idx_priority ON library_documents(priority);
CREATE INDEX idx_last_used ON library_documents(last_used_at);
CREATE INDEX idx_metrics_doc ON library_metrics(document_id);
CREATE INDEX idx_metrics_agent ON library_metrics(agent_name);
```

### 5.5 Contenu Initial Proposé (30+ documents)

#### CORE (6 docs)

1. **Règles Absolues**
   - Storage JSON (constructeur, save, load)
   - Pydantic v2 (model_dump, model_validate, model_copy)
   - Cohérence (imports, constructeurs, méthodes)
   - Tests (pas de tests pour fonctionnalités non implémentées)

2. **Conventions Code Python**
   - Imports absolus simples
   - PascalCase/snake_case
   - Type hints, docstrings
   - Newline fin fichier

3. **Conventions Code JavaScript**
   - ES6 modules
   - camelCase/PascalCase
   - const/let, template literals

4. **Structure Projet Standard**
   - src/, tests/, docs/
   - requirements.txt / package.json
   - README, .gitignore

5. **Stack Technique Val C.**
   - Backend : Python, FastAPI, SQLite
   - Frontend : Vanilla JS
   - Mobile : Flutter
   - IA : Gemini, OpenRouter

6. **Profil Val C.**
   - Compétences, préférences
   - Objectifs JARVIS 2.0
   - Contraintes (local, no-cloud)

#### METHODOLOGIES (8 docs)

7. **Audit > Plan > Validation > Exécution > Documentation**
8. **Gouvernance Documentaire**
9. **Revue de Code**
10. **Workflow Confirmation Actions**
11. **Gestion Dette Technique**
12. **Tests Strategy**
13. **Versioning & Changelog**
14. **Session Management**

#### LIBRARIES (6 docs)

15. **FastAPI** (existant)
16. **Pytest** (existant)
17. **Pydantic v2** (existant)
18. **aiosqlite** (existant)
19. **Flutter** (existant)
20. **Gemini API** (NOUVEAU)

#### PATTERNS (4 docs)

21. **Error Handling Python**
22. **Async/Await Patterns**
23. **Factory Pattern**
24. **Dependency Injection**

#### TEMPLATES (4 docs)

25. **Template Calculator** (code complet)
26. **Template TODO App** (code complet)
27. **Template MiniBlog** (code complet)
28. **Template FastAPI Service** (structure)

#### PROMPTS (3 docs)

29. **Délégation CODEUR** (existant)
30. **Vérification BASE** (existant)
31. **Création Projet** (existant)

#### CONTEXT (2 docs)

32. **Décisions Architecturales JARVIS**
33. **Historique Problèmes Résolus**

### 5.6 Fonctionnalités Frontend

**Page Library Améliorée** :

1. **Vue Liste**
   - Filtres : catégorie, sous-catégorie, agent, tag, priorité
   - Recherche texte full-text
   - Tri : nom, date, usage, priorité
   - Badges : nouveau, populaire, récent

2. **Vue Détail**
   - Rendu markdown
   - Métadonnées complètes
   - Historique versions
   - Métriques utilisation

3. **Édition**
   - Formulaire création/modification
   - Prévisualisation markdown live
   - Validation format
   - Sauvegarde brouillon

4. **Recherche Vectorielle**
   - Barre recherche sémantique
   - Résultats pertinents (score)
   - Highlight termes

5. **Import/Export**
   - Export JSON/Markdown
   - Import batch
   - Backup complet

### 5.7 Intégration RAG

**RAG Intégré Backend** :

```python
# backend/services/rag_manager.py
class IntegratedRAGManager:
    """RAG intégré au backend, pas de processus externe."""
    
    def __init__(self, db: Database):
        self.db = db
        self.chroma_client = chromadb.PersistentClient(
            path="./data/chroma_db"
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = self.chroma_client.get_or_create_collection(
            name="jarvis_library",
            embedding_function=SentenceTransformerEmbeddingFunction(
                self.embedding_model
            )
        )
    
    async def index_document(self, doc_id: str):
        """Indexe un document dans ChromaDB."""
        doc = await self.db.get_library_document(doc_id)
        if not doc:
            return
        
        # Découper en chunks
        chunks = self._split_text(doc['content'])
        
        # Indexer
        for i, chunk in enumerate(chunks):
            self.collection.add(
                ids=[f"{doc_id}_chunk_{i}"],
                documents=[chunk],
                metadatas=[{
                    "doc_id": doc_id,
                    "name": doc['name'],
                    "category": doc['category'],
                    "agents": ",".join(doc['agents']),
                    "chunk_index": i
                }]
            )
    
    async def search(self, query: str, filter_agent: str = None, n_results: int = 5):
        """Recherche vectorielle."""
        where = {"agents": {"$contains": filter_agent}} if filter_agent else None
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        return results
    
    async def enrich_instruction(self, instruction: str, agent: str = None):
        """Enrichit instruction avec contexte."""
        results = await self.search(instruction, filter_agent=agent, n_results=3)
        
        if not results['documents'] or not results['documents'][0]:
            return instruction
        
        context = "\n\n".join(results['documents'][0])
        return f"""{instruction}

---
CONTEXTE LIBRARY (pertinent pour cette tâche) :

{context}
---

Utilise le contexte Library ci-dessus pour respecter les standards et patterns recommandés.
"""
```

**Avantages** :
- Pas de processus externe
- Toujours disponible
- Indexation automatique
- Synchronisation garantie

---

## 6. PLAN D'ACTION

### Phase 1 : Correction Doublons (PRIORITÉ 1)

**Objectif** : Éliminer doublon frontend/backend

**Actions** :
1. ✅ Modifier `frontend/js/views/library.js`
   - Supprimer LIBRARY_CATEGORIES hardcodé
   - Ajouter appel API `GET /api/library`
   - Afficher documents depuis BDD

2. ✅ Tester page Library
   - Vérifier affichage 12 documents
   - Vérifier filtres
   - Vérifier modal détail

**Durée** : 1h  
**Validation** : Page Library affiche documents BDD

### Phase 2 : Ajout CRUD Frontend (PRIORITÉ 1)

**Objectif** : Permettre gestion documents via UI

**Actions** :
1. ✅ Ajouter bouton "Nouveau document"
2. ✅ Créer formulaire création/édition
3. ✅ Implémenter POST /api/library
4. ✅ Implémenter PUT /api/library/{id}
5. ✅ Implémenter DELETE /api/library/{id}
6. ✅ Ajouter confirmation suppression

**Durée** : 2-3h  
**Validation** : Créer/modifier/supprimer document via UI

### Phase 3 : Migration BDD (PRIORITÉ 2)

**Objectif** : Ajouter colonnes versioning/métriques

**Actions** :
1. ✅ Créer script migration `backend/db/migrations/003_library_enhanced.sql`
2. ✅ Ajouter colonnes : subcategory, priority, version, parent_id, last_used_at, usage_count
3. ✅ Créer tables : library_versions, library_metrics
4. ✅ Créer index
5. ✅ Tester migration

**Durée** : 1h  
**Validation** : BDD migrée sans perte données

### Phase 4 : Enrichissement Contenu (PRIORITÉ 2)

**Objectif** : Ajouter 20+ documents manquants

**Actions** :
1. ✅ Créer documents CORE (6)
2. ✅ Créer documents METHODOLOGIES (5 nouveaux)
3. ✅ Créer documents PATTERNS (4)
4. ✅ Créer documents TEMPLATES (4)
5. ✅ Créer documents CONTEXT (2)
6. ✅ Mettre à jour library_seed.json
7. ✅ Tester seed

**Durée** : 4-5h  
**Validation** : 30+ documents en BDD

### Phase 5 : RAG Intégré (PRIORITÉ 3)

**Objectif** : Intégrer RAG au backend

**Actions** :
1. ✅ Créer `backend/services/rag_manager.py`
2. ✅ Implémenter IntegratedRAGManager
3. ✅ Ajouter indexation auto lors création/modification document
4. ✅ Modifier orchestration pour utiliser RAG intégré
5. ✅ Supprimer dépendance API RAG externe
6. ✅ Tester enrichissement CODEUR

**Durée** : 3-4h  
**Validation** : CODEUR reçoit contexte enrichi

### Phase 6 : Fonctionnalités Avancées (PRIORITÉ 4)

**Objectif** : Versioning, métriques, analytics

**Actions** :
1. ✅ Implémenter versioning documents
2. ✅ Implémenter tracking utilisation
3. ✅ Créer dashboard métriques
4. ✅ Ajouter export/import
5. ✅ Ajouter recherche vectorielle frontend

**Durée** : 5-6h  
**Validation** : Fonctionnalités avancées opérationnelles

---

## 7. RÉCAPITULATIF

### Problèmes Identifiés

1. ❌ Doublon frontend/backend (données hardcodées)
2. ❌ Frontend déconnecté (pas d'API)
3. ❌ API RAG externe non fiable
4. ⚠️ Catégorisation limitée
5. ⚠️ Contenu incomplet (manque 20+ documents)
6. ⚠️ Métadonnées sous-exploitées

### Solutions Proposées

1. ✅ Frontend connecté API backend
2. ✅ CRUD complet via UI
3. ✅ RAG intégré backend (pas externe)
4. ✅ Catégories + sous-catégories
5. ✅ 30+ documents personnalisés Val C.
6. ✅ Versioning, métriques, analytics

### Bénéfices Attendus

- **Cohérence** : Source unique vérité
- **Productivité** : Gestion via UI
- **Fiabilité** : RAG toujours disponible
- **Personnalisation** : Reflet exact méthodes Val C.
- **Évolutivité** : Scalable 100+ documents
- **Traçabilité** : Versioning, métriques

### Effort Total Estimé

- Phase 1 : 1h
- Phase 2 : 2-3h
- Phase 3 : 1h
- Phase 4 : 4-5h
- Phase 5 : 3-4h
- Phase 6 : 5-6h

**Total** : 16-20h de développement

---

## 8. PROCHAINES ÉTAPES

**Validation utilisateur requise** :

1. ✅ Approuver architecture cible ?
2. ✅ Approuver structure documents (7 catégories) ?
3. ✅ Approuver schéma BDD amélioré ?
4. ✅ Approuver contenu initial (30+ docs) ?
5. ✅ Approuver plan d'action (6 phases) ?

**Après validation** :

- Démarrer Phase 1 (correction doublons)
- Créer document de travail par phase
- Tests après chaque phase
- Consolidation finale

---

**FIN DU DOCUMENT**
