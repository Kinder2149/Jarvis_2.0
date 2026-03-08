# PLAN D'ACTION DÉTAILLÉ — RÉORGANISATION LIBRARY RAG

**Date** : 5 mars 2026  
**Statut** : WORK  
**Objectif** : Implémentation complète réorganisation Library avec vérification existant

---

## 📋 ANALYSE DE L'EXISTANT

### ✅ Ce qui existe déjà et fonctionne

#### Backend API (COMPLET)
- **Routes REST** : `@d:\Coding\AppWindows\Jarvis 2.0\backend\api.py:517-608`
  - ✅ `GET /api/library` : Liste avec filtres (category, agent, tag, search)
  - ✅ `GET /api/library/{doc_id}` : Récupère document par ID
  - ✅ `POST /api/library` : Crée nouveau document
  - ✅ `PUT /api/library/{doc_id}` : Met à jour document
  - ✅ `DELETE /api/library/{doc_id}` : Supprime document
  - **Validation** : Pydantic models (LibraryDocument, LibraryDocumentCreate, LibraryDocumentUpdate)

#### Backend Database (COMPLET)
- **Schéma** : `@d:\Coding\AppWindows\Jarvis 2.0\backend\db\schema.sql:40-57`
  - Table `library_documents` avec colonnes : id, category, name, icon, description, content, tags, agents, created_at, updated_at
  - CHECK constraint : category IN ('libraries', 'methodologies', 'prompts', 'personal')
  - Index : category, updated_at, name

- **CRUD** : `@d:\Coding\AppWindows\Jarvis 2.0\backend\db\database.py:303-524`
  - ✅ `create_library_document()` : Insertion avec UUID, JSON tags/agents
  - ✅ `get_library_document()` : Récupération par ID
  - ✅ `list_library_documents()` : Liste avec filtres SQL
  - ✅ `update_library_document()` : Mise à jour
  - ✅ `delete_library_document()` : Suppression
  - ✅ `seed_library_if_empty()` : Peuplement auto depuis library_seed.json

#### Seed Data (COMPLET)
- **Fichier** : `@d:\Coding\AppWindows\Jarvis 2.0\backend\db\library_seed.json`
  - 12 documents structurés (category, name, icon, description, tags, agents, content)
  - Catégories : libraries (5), methodologies (3), prompts (3), personal (2)

#### Migrations (EXISTE)
- **Fichier** : `@d:\Coding\AppWindows\Jarvis 2.0\backend\db\migrations.py`
  - Fonction `migrate_library_data()` existe mais **DOUBLON** avec seed
  - Contient données hardcodées identiques à library_seed.json
  - **Action** : À nettoyer (doublon inutile)

### ❌ Ce qui pose problème

#### Frontend Hardcodé (CRITIQUE)
- **Fichier** : `@d:\Coding\AppWindows\Jarvis 2.0\frontend\js\views\library.js:15-564`
  - Constante `LIBRARY_CATEGORIES` hardcodée (lignes 15-560)
  - **DOUBLON EXACT** avec library_seed.json
  - Aucun appel API backend
  - Données statiques uniquement

#### Pas de CRUD Frontend
- Lecture seule
- Pas de formulaire création/édition
- Pas de bouton suppression
- Pas de modal édition

#### Catégories Figées
- CHECK constraint SQL limite à 4 catégories fixes
- Pas de sous-catégories
- Pas d'évolutivité

#### Pas de Versioning/Métriques
- Pas de colonnes : subcategory, priority, version, parent_id, last_used_at, usage_count
- Pas de tables : library_versions, library_metrics

---

## 🎯 PLAN D'ACTION RÉVISÉ (6 PHASES)

### PHASE 0 : Nettoyage Préalable (NOUVEAU)

**Objectif** : Éliminer doublons et incohérences

**Actions** :

1. **Nettoyer migrations.py**
   - Supprimer fonction `migrate_library_data()` (doublon avec seed)
   - Garder uniquement `migrate_sessions_to_conversations()`
   - Raison : library_seed.json + seed_library_if_empty() suffisent

2. **Vérifier cohérence library_seed.json**
   - Comparer avec données hardcodées frontend
   - S'assurer que seed est la source de vérité
   - Valider structure JSON

3. **Archiver documentation obsolète**
   - Vérifier docs/history/ pour doublons Library
   - Mettre à jour docs/_meta/INDEX.md

**Durée** : 30 min  
**Validation** : Aucun doublon, seed = source unique

---

### PHASE 1 : Connecter Frontend à API Backend

**Objectif** : Supprimer hardcode, charger depuis BDD

**Fichiers impactés** :
- `frontend/js/views/library.js`

**Actions détaillées** :

1. **Supprimer LIBRARY_CATEGORIES hardcodé**
   ```javascript
   // AVANT (lignes 15-560)
   const LIBRARY_CATEGORIES = [ ... ]; // 545 lignes hardcodées
   
   // APRÈS
   // Supprimé - données chargées depuis API
   ```

2. **Ajouter méthode fetchLibraryData()**
   ```javascript
   async fetchLibraryData() {
       try {
           const response = await fetch(`${API_BASE}/api/library`);
           if (!response.ok) throw new Error('Failed to fetch library');
           const documents = await response.json();
           
           // Grouper par catégorie
           this.categories = this.groupByCategory(documents);
       } catch (error) {
           console.error('Error fetching library:', error);
           this.showError('Impossible de charger la librairie');
       }
   }
   
   groupByCategory(documents) {
       const grouped = {};
       documents.forEach(doc => {
           if (!grouped[doc.category]) {
               grouped[doc.category] = {
                   id: doc.category,
                   name: this.getCategoryName(doc.category),
                   icon: this.getCategoryIcon(doc.category),
                   items: []
               };
           }
           grouped[doc.category].items.push(doc);
       });
       return Object.values(grouped);
   }
   ```

3. **Modifier constructor et render()**
   ```javascript
   constructor() {
       this.container = null;
       this.categories = []; // Vide au départ
       this.activeFilter = 'all';
   }
   
   async render(container) {
       this.container = container;
       clearContainer(container);
       
       // Charger données
       await this.fetchLibraryData();
       
       // Afficher
       this.renderLibrary();
   }
   ```

4. **Tester**
   - Démarrer backend : `python -m backend.app`
   - Ouvrir frontend : http://localhost:8000
   - Vérifier page Library affiche 12 documents
   - Vérifier filtres fonctionnent
   - Vérifier modal détail

**Durée** : 1h  
**Validation** : Page Library charge depuis API, 12 documents affichés

---

### PHASE 2 : CRUD Complet Frontend

**Objectif** : Créer/Modifier/Supprimer documents via UI

**Fichiers impactés** :
- `frontend/js/views/library.js`

**Actions détaillées** :

1. **Ajouter bouton "Nouveau document"**
   ```javascript
   renderHeader() {
       return createElement('div', { className: 'library-header' }, [
           createElement('h1', {}, 'Librairie'),
           createElement('button', {
               className: 'btn-primary',
               onclick: () => this.openCreateModal()
           }, '+ Nouveau document')
       ]);
   }
   ```

2. **Créer modal création/édition**
   ```javascript
   openCreateModal() {
       const modal = this.createDocumentModal(null); // null = création
       document.body.appendChild(modal);
   }
   
   openEditModal(docId) {
       const doc = this.findDocument(docId);
       const modal = this.createDocumentModal(doc); // doc = édition
       document.body.appendChild(modal);
   }
   
   createDocumentModal(doc = null) {
       const isEdit = doc !== null;
       
       return createElement('div', { className: 'modal' }, [
           createElement('div', { className: 'modal-content' }, [
               createElement('h2', {}, isEdit ? 'Modifier document' : 'Nouveau document'),
               this.createDocumentForm(doc),
               createElement('div', { className: 'modal-actions' }, [
                   createElement('button', {
                       onclick: () => this.closeModal()
                   }, 'Annuler'),
                   createElement('button', {
                       className: 'btn-primary',
                       onclick: () => this.saveDocument(doc?.id)
                   }, isEdit ? 'Enregistrer' : 'Créer')
               ])
           ])
       ]);
   }
   
   createDocumentForm(doc) {
       return createElement('form', { id: 'doc-form' }, [
           // Catégorie
           createElement('label', {}, 'Catégorie'),
           createElement('select', {
               name: 'category',
               value: doc?.category || 'libraries'
           }, [
               createElement('option', { value: 'libraries' }, 'Librairies'),
               createElement('option', { value: 'methodologies' }, 'Méthodologies'),
               createElement('option', { value: 'prompts' }, 'Prompts'),
               createElement('option', { value: 'personal' }, 'Personnel')
           ]),
           
           // Nom
           createElement('label', {}, 'Nom'),
           createElement('input', {
               type: 'text',
               name: 'name',
               value: doc?.name || '',
               required: true
           }),
           
           // Icon
           createElement('label', {}, 'Icône (emoji)'),
           createElement('input', {
               type: 'text',
               name: 'icon',
               value: doc?.icon || '',
               placeholder: '📚'
           }),
           
           // Description
           createElement('label', {}, 'Description'),
           createElement('textarea', {
               name: 'description',
               value: doc?.description || '',
               rows: 3,
               required: true
           }),
           
           // Tags
           createElement('label', {}, 'Tags (séparés par virgules)'),
           createElement('input', {
               type: 'text',
               name: 'tags',
               value: doc?.tags?.join(', ') || '',
               placeholder: 'python, web, api'
           }),
           
           // Agents
           createElement('label', {}, 'Agents (séparés par virgules)'),
           createElement('input', {
               type: 'text',
               name: 'agents',
               value: doc?.agents?.join(', ') || '',
               placeholder: 'CODEUR, BASE'
           }),
           
           // Contenu
           createElement('label', {}, 'Contenu (Markdown)'),
           createElement('textarea', {
               name: 'content',
               value: doc?.content || '',
               rows: 15,
               required: true,
               placeholder: '# Titre\n\nContenu en Markdown...'
           })
       ]);
   }
   ```

3. **Implémenter saveDocument()**
   ```javascript
   async saveDocument(docId = null) {
       const form = document.getElementById('doc-form');
       const formData = new FormData(form);
       
       const data = {
           category: formData.get('category'),
           name: formData.get('name'),
           icon: formData.get('icon') || null,
           description: formData.get('description'),
           content: formData.get('content'),
           tags: formData.get('tags').split(',').map(t => t.trim()).filter(Boolean),
           agents: formData.get('agents').split(',').map(a => a.trim()).filter(Boolean)
       };
       
       try {
           const url = docId 
               ? `${API_BASE}/api/library/${docId}` 
               : `${API_BASE}/api/library`;
           const method = docId ? 'PUT' : 'POST';
           
           const response = await fetch(url, {
               method,
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify(data)
           });
           
           if (!response.ok) throw new Error('Save failed');
           
           this.closeModal();
           await this.fetchLibraryData(); // Recharger
           this.renderLibrary();
           this.showSuccess(docId ? 'Document modifié' : 'Document créé');
       } catch (error) {
           console.error('Error saving document:', error);
           this.showError('Erreur lors de la sauvegarde');
       }
   }
   ```

4. **Implémenter deleteDocument()**
   ```javascript
   async deleteDocument(docId) {
       if (!confirm('Supprimer ce document ?')) return;
       
       try {
           const response = await fetch(`${API_BASE}/api/library/${docId}`, {
               method: 'DELETE'
           });
           
           if (!response.ok) throw new Error('Delete failed');
           
           await this.fetchLibraryData();
           this.renderLibrary();
           this.showSuccess('Document supprimé');
       } catch (error) {
           console.error('Error deleting document:', error);
           this.showError('Erreur lors de la suppression');
       }
   }
   ```

5. **Ajouter boutons édition/suppression dans renderItem()**
   ```javascript
   renderItem(item) {
       return createElement('div', { className: 'library-item' }, [
           // ... contenu existant ...
           createElement('div', { className: 'item-actions' }, [
               createElement('button', {
                   className: 'btn-icon',
                   onclick: (e) => {
                       e.stopPropagation();
                       this.openEditModal(item.id);
                   }
               }, '✏️'),
               createElement('button', {
                   className: 'btn-icon btn-danger',
                   onclick: (e) => {
                       e.stopPropagation();
                       this.deleteDocument(item.id);
                   }
               }, '🗑️')
           ])
       ]);
   }
   ```

6. **Ajouter CSS**
   ```css
   /* frontend/css/library.css */
   .library-header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 2rem;
   }
   
   .modal {
       position: fixed;
       top: 0;
       left: 0;
       width: 100%;
       height: 100%;
       background: rgba(0,0,0,0.5);
       display: flex;
       align-items: center;
       justify-content: center;
       z-index: 1000;
   }
   
   .modal-content {
       background: white;
       padding: 2rem;
       border-radius: 8px;
       max-width: 800px;
       max-height: 90vh;
       overflow-y: auto;
   }
   
   .item-actions {
       display: flex;
       gap: 0.5rem;
       margin-top: 1rem;
   }
   
   .btn-icon {
       background: none;
       border: 1px solid #ddd;
       padding: 0.5rem;
       cursor: pointer;
       border-radius: 4px;
   }
   
   .btn-icon:hover {
       background: #f5f5f5;
   }
   
   .btn-danger:hover {
       background: #fee;
       border-color: #f00;
   }
   ```

**Durée** : 2-3h  
**Validation** : Créer/modifier/supprimer document via UI fonctionne

---

### PHASE 3 : Migration BDD (Versioning/Métriques)

**Objectif** : Ajouter colonnes et tables pour fonctionnalités avancées

**Fichiers impactés** :
- `backend/db/schema.sql` (référence)
- Nouveau : `backend/db/migrations/003_library_enhanced.sql`
- `backend/db/database.py` (méthodes CRUD)

**Actions détaillées** :

1. **Créer script migration**
   ```sql
   -- backend/db/migrations/003_library_enhanced.sql
   
   -- Ajouter colonnes à library_documents
   ALTER TABLE library_documents ADD COLUMN subcategory TEXT;
   ALTER TABLE library_documents ADD COLUMN priority INTEGER DEFAULT 5;
   ALTER TABLE library_documents ADD COLUMN version INTEGER DEFAULT 1;
   ALTER TABLE library_documents ADD COLUMN parent_id TEXT REFERENCES library_documents(id);
   ALTER TABLE library_documents ADD COLUMN last_used_at TEXT;
   ALTER TABLE library_documents ADD COLUMN usage_count INTEGER DEFAULT 0;
   
   -- Supprimer CHECK constraint catégories (pour permettre nouvelles catégories)
   -- Note: SQLite ne supporte pas DROP CONSTRAINT, recréer table
   CREATE TABLE library_documents_new (
       id TEXT PRIMARY KEY,
       category TEXT NOT NULL,
       subcategory TEXT,
       name TEXT NOT NULL,
       icon TEXT,
       description TEXT,
       content TEXT NOT NULL,
       tags TEXT,
       agents TEXT,
       priority INTEGER DEFAULT 5,
       version INTEGER DEFAULT 1,
       parent_id TEXT,
       last_used_at TEXT,
       usage_count INTEGER DEFAULT 0,
       created_at TEXT NOT NULL,
       updated_at TEXT NOT NULL,
       FOREIGN KEY (parent_id) REFERENCES library_documents_new(id)
   );
   
   -- Copier données
   INSERT INTO library_documents_new 
       (id, category, name, icon, description, content, tags, agents, created_at, updated_at)
   SELECT id, category, name, icon, description, content, tags, agents, created_at, updated_at
   FROM library_documents;
   
   -- Remplacer table
   DROP TABLE library_documents;
   ALTER TABLE library_documents_new RENAME TO library_documents;
   
   -- Recréer index
   CREATE INDEX idx_library_category ON library_documents(category);
   CREATE INDEX idx_library_subcategory ON library_documents(subcategory);
   CREATE INDEX idx_library_updated ON library_documents(updated_at DESC);
   CREATE INDEX idx_library_name ON library_documents(name);
   CREATE INDEX idx_library_priority ON library_documents(priority);
   CREATE INDEX idx_library_last_used ON library_documents(last_used_at DESC);
   
   -- Table versions
   CREATE TABLE library_versions (
       id TEXT PRIMARY KEY,
       document_id TEXT NOT NULL,
       version INTEGER NOT NULL,
       content TEXT NOT NULL,
       created_at TEXT NOT NULL,
       created_by TEXT,
       change_summary TEXT,
       FOREIGN KEY (document_id) REFERENCES library_documents(id) ON DELETE CASCADE,
       UNIQUE(document_id, version)
   );
   
   CREATE INDEX idx_versions_doc ON library_versions(document_id);
   CREATE INDEX idx_versions_created ON library_versions(created_at DESC);
   
   -- Table métriques
   CREATE TABLE library_metrics (
       id TEXT PRIMARY KEY,
       document_id TEXT NOT NULL,
       agent_name TEXT NOT NULL,
       used_at TEXT NOT NULL,
       context TEXT,
       helpful BOOLEAN,
       FOREIGN KEY (document_id) REFERENCES library_documents(id) ON DELETE CASCADE
   );
   
   CREATE INDEX idx_metrics_doc ON library_metrics(document_id);
   CREATE INDEX idx_metrics_agent ON library_metrics(agent_name);
   CREATE INDEX idx_metrics_used ON library_metrics(used_at DESC);
   ```

2. **Créer runner migration**
   ```python
   # backend/db/run_migration.py
   import asyncio
   import aiosqlite
   from pathlib import Path
   
   async def run_migration_003():
       db_path = Path(__file__).parent / "jarvis.db"
       migration_path = Path(__file__).parent / "migrations" / "003_library_enhanced.sql"
       
       with open(migration_path, 'r', encoding='utf-8') as f:
           sql = f.read()
       
       async with aiosqlite.connect(db_path) as db:
           await db.executescript(sql)
           await db.commit()
           print("✅ Migration 003 appliquée")
   
   if __name__ == "__main__":
       asyncio.run(run_migration_003())
   ```

3. **Mettre à jour database.py**
   - Ajouter paramètres subcategory, priority dans create/update
   - Ajouter méthodes : create_version(), get_versions(), track_usage()

4. **Tester migration**
   ```bash
   python backend/db/run_migration.py
   ```

**Durée** : 1h  
**Validation** : Migration appliquée, colonnes ajoutées, données préservées

---

### PHASE 4 : Enrichissement Contenu (20+ Documents)

**Objectif** : Créer documents personnalisés Val C.

**Fichiers impactés** :
- `backend/db/library_seed.json` (enrichi)

**Actions détaillées** :

1. **Créer documents CORE (6)**
   - Règles Absolues (Storage JSON, Pydantic v2, Cohérence, Tests)
   - Conventions Code Python
   - Conventions Code JavaScript
   - Structure Projet Standard
   - Stack Technique Val C.
   - Profil Val C.

2. **Créer documents METHODOLOGIES (5 nouveaux)**
   - Workflow Confirmation Actions
   - Gestion Dette Technique
   - Tests Strategy
   - Versioning & Changelog
   - Session Management

3. **Créer documents PATTERNS (4)**
   - Error Handling Python
   - Async/Await Patterns
   - Factory Pattern
   - Dependency Injection

4. **Créer documents TEMPLATES (4)**
   - Template Calculator (code complet)
   - Template TODO App (code complet)
   - Template MiniBlog (code complet)
   - Template FastAPI Service (structure)

5. **Créer documents CONTEXT (2)**
   - Décisions Architecturales JARVIS
   - Historique Problèmes Résolus

6. **Mettre à jour library_seed.json**
   - Ajouter 20+ nouveaux documents
   - Utiliser nouvelles catégories (core, patterns, templates, context)
   - Ajouter subcategory, priority

7. **Reseed database**
   ```bash
   # Supprimer BDD et recréer
   rm backend/db/jarvis.db
   python -m backend.app
   ```

**Durée** : 4-5h  
**Validation** : 30+ documents en BDD, catégories enrichies

---

### PHASE 5 : RAG Intégré Backend (OPTIONNEL)

**Objectif** : Intégrer ChromaDB au backend (pas processus externe)

**Note** : Phase optionnelle, API RAG externe fonctionne actuellement

**Fichiers impactés** :
- Nouveau : `backend/services/rag_manager.py`
- `backend/services/orchestration.py`
- `requirements.txt`

**Actions détaillées** :

1. **Créer IntegratedRAGManager**
   ```python
   # backend/services/rag_manager.py
   import chromadb
   from sentence_transformers import SentenceTransformer
   from backend.db.database import Database
   
   class IntegratedRAGManager:
       def __init__(self, db: Database):
           self.db = db
           self.chroma_client = chromadb.PersistentClient(
               path="./data/chroma_db"
           )
           self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
           self.collection = self.chroma_client.get_or_create_collection(
               name="jarvis_library"
           )
       
       async def index_document(self, doc_id: str):
           """Indexe un document dans ChromaDB."""
           doc = await self.db.get_library_document(doc_id)
           if not doc:
               return
           
           chunks = self._split_text(doc['content'])
           
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
CONTEXTE LIBRARY :

{context}
---

Utilise le contexte ci-dessus pour respecter les standards.
"""
       
       def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200):
           """Découpe texte en chunks."""
           chunks = []
           start = 0
           while start < len(text):
               end = start + chunk_size
               chunks.append(text[start:end])
               start = end - overlap
           return chunks
   ```

2. **Modifier orchestration.py**
   - Remplacer RAGService par IntegratedRAGManager
   - Supprimer check_health (toujours disponible)

3. **Ajouter dépendances**
   ```txt
   chromadb==0.4.22
   sentence-transformers==2.3.1
   ```

4. **Indexation auto lors création/modification**
   ```python
   # backend/api.py
   @router.post("/api/library", response_model=LibraryDocument)
   async def create_library_document(doc: LibraryDocumentCreate):
       document = await db_instance.create_library_document(...)
       
       # Indexer dans RAG
       await rag_manager.index_document(document['id'])
       
       return document
   ```

**Durée** : 3-4h  
**Validation** : RAG intégré, enrichissement CODEUR fonctionne

---

### PHASE 6 : Documentation et Validation

**Objectif** : Mettre à jour documentation, valider cohérence

**Fichiers impactés** :
- `docs/_meta/INDEX.md`
- `docs/_meta/CHANGELOG.md`
- `docs/reference/` (si nécessaire)

**Actions détaillées** :

1. **Mettre à jour INDEX.md**
   - Ajouter section Library
   - Référencer nouveaux documents

2. **Mettre à jour CHANGELOG.md**
   - Entrée datée avec modifications
   - Lister fichiers modifiés
   - Résumer changements

3. **Archiver documents work/**
   - `MISSION_REORGANISATION_LIBRAIRIE_RAG_05MARS2026.md` → history/
   - `PLAN_ACTION_DETAILLE_LIBRARY_05MARS2026.md` → history/

4. **Créer document référence (optionnel)**
   - `docs/reference/LIBRARY_ARCHITECTURE.md`
   - Architecture, schéma BDD, API, utilisation

5. **Tests validation complète**
   - Backend : pytest tests/
   - Frontend : Tests manuels CRUD
   - Agents : Vérifier enrichissement CODEUR

**Durée** : 1h  
**Validation** : Documentation à jour, cohérence complète

---

## 📊 RÉCAPITULATIF

### Durée Totale Estimée
- Phase 0 : 30 min
- Phase 1 : 1h
- Phase 2 : 2-3h
- Phase 3 : 1h
- Phase 4 : 4-5h
- Phase 5 : 3-4h (optionnel)
- Phase 6 : 1h

**Total** : 9-11h (sans Phase 5) ou 12-15h (avec Phase 5)

### Ordre d'Exécution
1. Phase 0 (nettoyage)
2. Phase 1 (frontend API)
3. Phase 2 (CRUD frontend)
4. Phase 4 (contenu) — avant Phase 3 car pas besoin colonnes avancées
5. Phase 3 (migration BDD)
6. Phase 5 (RAG intégré) — optionnel
7. Phase 6 (documentation)

### Validation Continue
- Après chaque phase : commit Git
- Tests manuels après Phase 1, 2, 4
- Tests automatisés après Phase 3, 5

---

**FIN DU PLAN DÉTAILLÉ**
