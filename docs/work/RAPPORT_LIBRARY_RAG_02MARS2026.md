# Rapport Complet : Bibliothèque et RAG - JARVIS 2.0

**Date** : 2 mars 2026  
**Statut** : Analyse complète  
**Auteur** : Cascade AI

---

## 📋 Résumé Exécutif

Le système JARVIS 2.0 dispose de **deux systèmes de gestion de connaissances distincts** :

1. **Library (Knowledge Base)** : Base SQLite intégrée au backend principal
2. **RAG (Retrieval-Augmented Generation)** : API Flask standalone avec ChromaDB

**État actuel** :
- ✅ Library : **FONCTIONNELLE** (12 documents seed, API complète, frontend opérationnel)
- ⚠️ RAG : **STANDALONE NON INTÉGRÉ** (API indépendante, jamais indexée, non utilisée en production)
- ✅ Enrichissement RAG : **CODE PRÉSENT** mais jamais testé (API RAG jamais lancée)

---

## 🏗️ Architecture Actuelle

### 1. Library (Knowledge Base) - SYSTÈME PRINCIPAL

#### Backend (`backend/db/`)

**Base de données** : SQLite (`jarvis_data.db`)
- Table `library_documents` (schema.sql ligne 40-52)
- Catégories : `libraries`, `methodologies`, `prompts`, `personal`
- Champs : id, category, name, icon, description, content, tags, agents

**Seed data** : `library_seed.json` (12 documents)
- FastAPI, Pytest, Pydantic, aiosqlite, Flutter
- Méthodologies (Audit > Plan > Exécution, Gouvernance doc)
- Templates de prompts (Délégation CODEUR, Vérification BASE)
- Conventions personnelles (code, stack technique)

**Fonctions disponibles** (`database.py` lignes 303-520) :
- `create_library_document()`
- `get_library_document(doc_id)`
- `list_library_documents(category, agent, tag, search)`
- `update_library_document()`
- `delete_library_document()`
- `seed_library_if_empty()` ← Appelée au démarrage de l'app

#### API Routes (`backend/api.py` lignes 517-604)

```
GET    /api/library                    → Liste documents (avec filtres)
GET    /api/library/{doc_id}           → Récupère un document
POST   /api/library                    → Crée un document
PUT    /api/library/{doc_id}           → Met à jour un document
DELETE /api/library/{doc_id}           → Supprime un document
```

#### Frontend (`frontend/js/views/library-enhanced.js`)

- Vue complète avec filtres par catégorie
- Affichage en grille avec cartes par catégorie
- Modal de détail avec contenu markdown
- **État** : ✅ Fonctionnel, charge depuis API `/api/library`

#### Function Calling (`backend/services/function_executor.py`)

Agents BASE et JARVIS_Maître ont accès à :
- `get_library_document(name, category)` : Recherche par nom
- `get_library_list(category, agent)` : Liste documents

**Limitation** : Recherche par **nom exact uniquement**, pas de recherche sémantique.

---

### 2. RAG (Retrieval-Augmented Generation) - SYSTÈME STANDALONE

#### Architecture (`RAG/`)

**API Flask indépendante** (`RAG/src/main.py`)
- Port : **5001** (différent du backend principal sur 8000)
- Base vectorielle : **ChromaDB** (persistée dans `RAG/data/rag_db/`)
- Embeddings : **Sentence Transformers** (`all-MiniLM-L6-v2`)
- Text splitting : **LangChain** (chunks 1000 chars, overlap 200)

**Routes disponibles** (`RAG/doc/RAG_ROUTES.md`) :
```
GET    /rag/health                     → État du système
GET    /rag/formats                    → Formats supportés
POST   /rag/documents                  → Ajouter document (file_path ou text)
POST   /rag/documents/upload           → Upload fichier
POST   /rag/search                     → Recherche sémantique
POST   /rag/context                    → Contexte formaté pour LLM
GET    /rag/collection/info            → Info collection
DELETE /rag/collection/delete          → Supprimer collection
```

**Formats supportés** : `.txt`, `.md`, `.pdf`, `.docx`

#### Configuration (`RAG/.env.example`)

```env
RAG_COLLECTION_NAME=jarvis_library
RAG_PERSIST_DIR=./data/rag_db
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_DEVICE=cpu
```

#### Dépendances (`RAG/requirements.txt`)

- Flask 3.0.0 + flask-cors
- PyTorch 2.2.0 (ROCm 5.7)
- sentence-transformers 2.7.0
- chromadb 0.5.0
- langchain 0.3.0
- pypdf, python-docx (parsing documents)

**⚠️ Problème** : Dépendances RAG **NON installées** dans le venv principal.

---

### 3. Intégration RAG → Backend Principal

#### Service RAG (`backend/services/rag_service.py`)

**Classe** : `RAGService`
- URL API : `http://localhost:5000` ← **ERREUR** (devrait être 5001)
- Méthodes :
  - `check_health()` : Vérifie disponibilité API
  - `search(query, n_results)` : Recherche documents
  - `get_context(query, n_results)` : Contexte formaté
  - `enrich_instruction(instruction)` : Enrichit instruction CODEUR

#### Orchestration (`backend/services/orchestration.py` lignes 444-463)

**Enrichissement automatique pour CODEUR** :
```python
if agent_name == "CODEUR":
    rag_service = get_rag_service()
    is_available = await rag_service.check_health()
    if is_available:
        instruction = await rag_service.enrich_instruction(
            instruction,
            n_results=3,
            filter_metadata={"agent": "CODEUR"}
        )
```

**État** : ✅ Code présent, ❌ Jamais testé (API RAG jamais lancée)

#### Script d'indexation (`RAG/index_jarvis_library.py`)

**Fonction** : Indexe `library_seed.json` dans ChromaDB
- Lit les 12 documents de la Library
- Les découpe en chunks
- Génère embeddings
- Stocke dans ChromaDB

**État** : ❌ Jamais exécuté

---

## 🔍 État Détaillé des Composants

### ✅ Library (Knowledge Base) - OPÉRATIONNELLE

| Composant | État | Détails |
|-----------|------|---------|
| Table SQLite | ✅ Créée | `library_documents` dans `jarvis_data.db` |
| Seed data | ✅ Chargé | 12 documents au démarrage (`seed_library_if_empty()`) |
| API Routes | ✅ Fonctionnelles | 5 endpoints CRUD complets |
| Frontend | ✅ Opérationnel | Vue avec filtres, modal détail |
| Function calling | ✅ Disponible | `get_library_document`, `get_library_list` |
| Recherche | ⚠️ Limitée | Nom exact uniquement, pas de recherche sémantique |

**Test rapide** :
```bash
curl http://localhost:8000/api/library
```

### ⚠️ RAG - STANDALONE NON INTÉGRÉ

| Composant | État | Détails |
|-----------|------|---------|
| API Flask | ❌ Non lancée | Port 5001, jamais démarrée |
| ChromaDB | ❌ Vide | Base existe (`RAG/data/rag_db/`) mais vide |
| Indexation | ❌ Jamais faite | `index_jarvis_library.py` jamais exécuté |
| Dépendances | ❌ Non installées | `RAG/requirements.txt` non installé dans venv |
| Service backend | ⚠️ Présent | Code existe mais URL incorrecte (5000 au lieu de 5001) |
| Enrichissement CODEUR | ⚠️ Non testé | Code présent mais jamais activé |

**Problèmes identifiés** :
1. URL incorrecte dans `rag_service.py` (5000 au lieu de 5001)
2. Dépendances RAG non installées
3. API RAG jamais lancée
4. ChromaDB jamais indexée

---

## 📊 Comparaison Library vs RAG

| Critère | Library (SQLite) | RAG (ChromaDB) |
|---------|------------------|----------------|
| **Type de recherche** | Nom exact, filtres SQL | Recherche sémantique |
| **Performance** | Instantanée | Dépend du modèle embedding |
| **Complexité** | Simple (SQL) | Complexe (embeddings, chunking) |
| **Intégration** | Native backend | API standalone |
| **État actuel** | ✅ Fonctionnelle | ❌ Non utilisée |
| **Maintenance** | Facile | Nécessite serveur séparé |
| **Cas d'usage** | Recherche exacte, filtres | Recherche par similarité |

---

## 🚨 Problèmes Identifiés

### 1. Duplication de Systèmes

**Problème** : Deux systèmes pour gérer la même chose (documents de connaissance)
- Library : 12 documents en SQLite
- RAG : Vide, jamais utilisé

**Impact** : Confusion, maintenance double, complexité inutile

### 2. RAG Non Opérationnel

**Problèmes techniques** :
- ❌ API RAG jamais lancée (port 5001)
- ❌ URL incorrecte dans `rag_service.py` (5000 au lieu de 5001)
- ❌ Dépendances RAG non installées dans venv principal
- ❌ ChromaDB jamais indexée
- ❌ Script d'indexation jamais exécuté

**Impact** : Enrichissement CODEUR jamais activé, code mort

### 3. Recherche Library Limitée

**Problème** : `get_library_document()` cherche par **nom exact uniquement**
- Pas de recherche par mots-clés
- Pas de recherche sémantique
- Pas de ranking par pertinence

**Impact** : Agents doivent connaître le nom exact du document

### 4. Confusion Architecturale

**Problème** : Pas de documentation claire sur quel système utiliser
- Quand utiliser Library ?
- Quand utiliser RAG ?
- Pourquoi deux systèmes ?

---

## 🎯 Recommandations

### Option A : Supprimer RAG (RECOMMANDÉ)

**Justification** :
- Library fonctionne bien pour 12 documents
- Recherche sémantique non nécessaire pour ce volume
- Simplification architecture
- Moins de maintenance

**Actions** :
1. Supprimer dossier `RAG/`
2. Supprimer `backend/services/rag_service.py`
3. Retirer enrichissement RAG de `orchestration.py`
4. Améliorer recherche Library (LIKE, full-text search SQLite)

**Avantages** :
- ✅ Architecture simplifiée
- ✅ Moins de dépendances
- ✅ Pas de serveur séparé à gérer
- ✅ Maintenance réduite

**Inconvénients** :
- ❌ Pas de recherche sémantique (mais pas nécessaire pour 12 docs)

---

### Option B : Activer RAG (Si vraiment nécessaire)

**Justification** :
- Recherche sémantique utile si Library > 100 documents
- Permet recherche par similarité
- Enrichissement contexte pour CODEUR

**Actions** :

#### 1. Installer dépendances RAG
```bash
cd RAG
pip install -r requirements.txt
```

#### 2. Corriger URL dans `rag_service.py`
```python
RAG_API_URL = "http://localhost:5001"  # Au lieu de 5000
```

#### 3. Créer fichier `.env` pour RAG
```bash
cp RAG/.env.example RAG/.env
```

#### 4. Lancer API RAG
```bash
cd RAG
python run.py
```

#### 5. Indexer la Library
```bash
python RAG/index_jarvis_library.py
```

#### 6. Tester enrichissement
```bash
# Créer un projet et demander du code
# Vérifier logs : "Orchestration: instruction CODEUR enrichie avec RAG"
```

**Avantages** :
- ✅ Recherche sémantique
- ✅ Enrichissement automatique CODEUR
- ✅ Scalable (peut gérer 1000+ documents)

**Inconvénients** :
- ❌ Complexité accrue
- ❌ Serveur séparé à gérer
- ❌ Dépendances lourdes (PyTorch, ChromaDB)
- ❌ Maintenance double

---

### Option C : Fusionner Library + RAG (Compromis)

**Justification** :
- Garder Library comme source de vérité
- Ajouter recherche sémantique via ChromaDB intégré
- Un seul système, deux modes de recherche

**Actions** :
1. Intégrer ChromaDB directement dans backend principal
2. Indexer automatiquement les documents Library
3. Ajouter endpoint `/api/library/search-semantic`
4. Garder endpoints existants pour compatibilité

**Avantages** :
- ✅ Un seul système
- ✅ Deux modes de recherche (exact + sémantique)
- ✅ Pas de serveur séparé

**Inconvénients** :
- ❌ Complexité backend accrue
- ❌ Dépendances lourdes dans backend principal

---

## 📝 Plan d'Action Recommandé

### Phase 1 : Décision Architecturale (URGENT)

**Question** : Avez-vous besoin de recherche sémantique ?

**Si NON** → **Option A : Supprimer RAG**
- Temps : 1h
- Risque : Faible
- Impact : Simplification majeure

**Si OUI** → **Option B : Activer RAG** ou **Option C : Fusionner**
- Temps : 4-8h
- Risque : Moyen
- Impact : Complexité accrue

### Phase 2 : Amélioration Library (Indépendant)

Quelle que soit l'option choisie, améliorer la recherche Library :

1. **Ajouter recherche par mots-clés** (`database.py`)
   ```python
   async def search_library_documents(self, query: str):
       # Recherche LIKE sur name, description, content, tags
   ```

2. **Ajouter endpoint de recherche** (`api.py`)
   ```python
   GET /api/library/search?q=fastapi
   ```

3. **Améliorer function calling**
   ```python
   get_library_search(query: str, category: str = None)
   ```

### Phase 3 : Documentation

1. Documenter le système choisi dans `docs/reference/LIBRARY_ARCHITECTURE.md`
2. Mettre à jour README avec instructions claires
3. Archiver ce rapport dans `docs/history/`

---

## 🧪 Tests à Effectuer

### Tests Library (Actuels)

```bash
# 1. Vérifier seed
curl http://localhost:8000/api/library

# 2. Récupérer un document
curl http://localhost:8000/api/library/{doc_id}

# 3. Filtrer par catégorie
curl "http://localhost:8000/api/library?category=libraries"

# 4. Filtrer par agent
curl "http://localhost:8000/api/library?agent=CODEUR"
```

### Tests RAG (Si activé)

```bash
# 1. Vérifier API RAG
curl http://localhost:5001/rag/health

# 2. Vérifier collection
curl http://localhost:5001/rag/collection/info

# 3. Recherche sémantique
curl -X POST http://localhost:5001/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "comment créer une API FastAPI", "n_results": 3}'

# 4. Contexte formaté
curl -X POST http://localhost:5001/rag/context \
  -H "Content-Type: application/json" \
  -d '{"query": "tests pytest", "n_results": 2}'
```

### Tests Enrichissement CODEUR (Si RAG activé)

1. Créer un projet via frontend
2. Demander "Crée une API FastAPI avec tests pytest"
3. Vérifier logs backend :
   - `Orchestration: enrichissement RAG activé pour CODEUR`
   - `Orchestration: instruction CODEUR enrichie avec RAG`
4. Vérifier que le code généré utilise les bonnes pratiques de la Library

---

## 📚 Documentation Existante

### RAG
- `RAG/README.md` : Présentation générale (vide ou obsolète)
- `RAG/doc/setup.md` : Installation (obsolète, parle de LLM local)
- `RAG/doc/API_DOCUMENTATION.md` : Routes API LLM (non pertinent)
- `RAG/doc/RAG_ROUTES.md` : Routes RAG complètes ✅

### Library
- `backend/db/library_seed.json` : Seed data ✅
- `backend/db/schema.sql` : Schéma table ✅
- Pas de doc dédiée ❌

**Action** : Créer `docs/reference/LIBRARY_ARCHITECTURE.md`

---

## 🎬 Conclusion

### État Actuel

**Library** : ✅ **Fonctionnelle et utilisée**
- 12 documents seed
- API complète
- Frontend opérationnel
- Function calling disponible
- Recherche limitée (nom exact)

**RAG** : ❌ **Standalone non intégré**
- API jamais lancée
- ChromaDB vide
- Code d'enrichissement présent mais jamais testé
- Dépendances non installées
- URL incorrecte dans service

### Recommandation Finale

**Pour un projet avec 12 documents** : **Option A - Supprimer RAG**

**Justification** :
- Recherche sémantique non nécessaire pour ce volume
- Library fonctionne bien
- Simplification architecture
- Moins de maintenance
- Améliorer recherche Library suffit (LIKE, full-text)

**Si besoin de scalabilité future** : **Option C - Fusionner**
- Intégrer ChromaDB dans backend principal
- Indexation automatique Library
- Un seul système, deux modes de recherche

**Éviter** : **Option B - Activer RAG standalone**
- Trop complexe pour le besoin actuel
- Maintenance double
- Serveur séparé à gérer

---

## 📎 Annexes

### Fichiers Clés

**Library** :
- `backend/db/schema.sql` (lignes 40-57)
- `backend/db/database.py` (lignes 303-520)
- `backend/db/library_seed.json` (12 documents)
- `backend/api.py` (lignes 517-604)
- `backend/services/function_executor.py` (lignes 60-176)
- `frontend/js/views/library-enhanced.js`

**RAG** :
- `RAG/src/main.py` (API Flask)
- `RAG/src/rag.py` (RAGManager)
- `RAG/requirements.txt` (dépendances)
- `RAG/index_jarvis_library.py` (script indexation)
- `backend/services/rag_service.py` (intégration)
- `backend/services/orchestration.py` (lignes 444-463)

### Commandes Utiles

```bash
# Vérifier Library
curl http://localhost:8000/api/library | jq

# Compter documents
sqlite3 jarvis_data.db "SELECT COUNT(*) FROM library_documents;"

# Lister catégories
sqlite3 jarvis_data.db "SELECT DISTINCT category FROM library_documents;"

# Vérifier ChromaDB
ls -la RAG/data/rag_db/

# Tester API RAG (si lancée)
curl http://localhost:5001/rag/health
```

---

**Prochaine étape** : Décider quelle option choisir (A, B ou C) et exécuter le plan correspondant.
