# Intégration RAG Complète - JARVIS 2.0

**Date** : 25 février 2026  
**Objectif** : Intégrer le système RAG pour enrichir automatiquement les instructions CODEUR avec contexte Library

---

## 📦 Fichiers Créés

### 1. **RAG/requirements-minimal.txt**
Dépendances minimales pour faire tourner le RAG (sans PyTorch lourd) :
- Flask 3.0.0
- sentence-transformers 2.7.0 (installe torch CPU léger automatiquement)
- chromadb 0.5.0
- langchain 0.3.0
- pypdf, python-docx, markdown (parsing documents)

**Taille estimée** : ~1-2 GB (au lieu de 5-10 GB avec PyTorch ROCm)

---

### 2. **RAG/index_jarvis_library.py**
Script Python pour indexer la Library JARVIS dans ChromaDB.

**Fonctionnalités** :
- Vérifie que l'API RAG est accessible
- Charge `backend/db/library_seed.json`
- Vide la collection existante
- Indexe chaque document avec métadonnées (category, agent, tags)
- Affiche résumé de l'indexation

**Usage** :
```bash
# 1. Lancer l'API RAG
cd RAG
python run.py

# 2. Dans un autre terminal, indexer la Library
python index_jarvis_library.py
```

---

### 3. **backend/services/rag_service.py**
Service Python pour communiquer avec l'API RAG depuis JARVIS backend.

**Classe `RAGService`** :
- `check_health()` : Vérifie si l'API RAG est accessible
- `search_documents(query, n_results)` : Recherche documents pertinents
- `get_context(query, n_results)` : Récupère contexte formaté
- `enrich_instruction(instruction, n_results)` : Enrichit instruction avec contexte Library

**Usage** :
```python
from backend.services.rag_service import get_rag_service

rag_service = get_rag_service()
enriched = await rag_service.enrich_instruction(
    "Crée une API FastAPI pour gérer des todos",
    n_results=3
)
```

---

### 4. **backend/services/orchestration.py** (MODIFIÉ)
Ajout de l'enrichissement RAG automatique pour les instructions CODEUR.

**Modifications** :
1. Import `get_rag_service` (ligne 24)
2. Enrichissement automatique avant appel CODEUR (lignes 445-460)

**Logique** :
```python
if agent_name == "CODEUR":
    # Vérifier disponibilité API RAG
    if rag_service.check_health():
        # Enrichir instruction avec top 3 documents Library
        instruction = await rag_service.enrich_instruction(
            instruction,
            n_results=3,
            filter_metadata={"agent": "CODEUR"}
        )
```

**Garde-fous** :
- Si API RAG non disponible → Continue sans enrichissement
- Si erreur RAG → Continue sans enrichissement
- Logs détaillés pour debugging

---

### 5. **RAG/start_rag_server.ps1**
Script PowerShell pour démarrer le serveur RAG avec vérifications.

**Fonctionnalités** :
- Vérifie que Python est installé
- Vérifie les dépendances (flask, chromadb, sentence_transformers, langchain)
- Propose d'installer les dépendances manquantes
- Vérifie que le port 5001 est libre
- Lance le serveur RAG

**Usage** :
```powershell
cd RAG
.\start_rag_server.ps1
```

---

### 6. **RAG/.env.example**
Fichier de configuration exemple pour le RAG.

**Variables** :
- `RAG_COLLECTION_NAME=jarvis_library`
- `RAG_PERSIST_DIR=./data/rag_db`
- `RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2`
- `RAG_CHUNK_SIZE=1000`
- `RAG_CHUNK_OVERLAP=200`
- `RAG_DEVICE=cpu`

---

## 🚀 Plan d'Installation et Démarrage

### **Étape 1 : Installer Dépendances RAG (15-20 min)**

```bash
cd RAG
pip install -r requirements-minimal.txt
```

**Dépendances installées** :
- Flask + flask-cors (API web)
- sentence-transformers (embeddings)
- chromadb (base vectorielle)
- langchain (text splitting)
- pypdf, python-docx, markdown (parsing)

**Note** : `sentence-transformers` installe automatiquement PyTorch CPU léger (~500 MB), pas besoin de PyTorch ROCm complet.

---

### **Étape 2 : Lancer Serveur RAG (1 min)**

**Option A : Script PowerShell (recommandé)**
```powershell
cd RAG
.\start_rag_server.ps1
```

**Option B : Manuel**
```bash
cd RAG
python run.py
```

**Vérification** :
```bash
curl http://localhost:5001/
# Réponse attendue : {"message": "API Flask active", "status": "ok"}
```

---

### **Étape 3 : Indexer Library JARVIS (2-3 min)**

```bash
# Dans un nouveau terminal (serveur RAG doit tourner)
cd RAG
python index_jarvis_library.py
```

**Résultat attendu** :
```
========================================
INDEXATION LIBRARY JARVIS DANS RAG
========================================

1. Vérification de l'API RAG...
✅ API RAG accessible

2. Chargement de backend/db/library_seed.json...
✅ 13 documents trouvés

3. Vidage de la collection existante...
✅ Collection RAG vidée avec succès

4. Indexation des 13 documents...
  ✅ FastAPI: 5 chunks indexés
  ✅ Pydantic: 4 chunks indexés
  ✅ Tests: 3 chunks indexés
  ...

========================================
RÉSUMÉ DE L'INDEXATION
========================================
✅ Succès : 13/13
❌ Échecs : 0/13

🎉 Indexation terminée avec succès !
```

---

### **Étape 4 : Tester Recherche RAG (1 min)**

```bash
curl -X POST http://localhost:5001/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "API FastAPI", "n_results": 3}'
```

**Résultat attendu** : JSON avec 3 documents pertinents

---

### **Étape 5 : Lancer JARVIS Backend (1 min)**

```bash
# Dans un nouveau terminal
cd backend
uvicorn api:app --reload --port 8000
```

**Note** : Le serveur RAG doit rester actif en parallèle (port 5001)

---

### **Étape 6 : Tester avec Projet Simple (5 min)**

1. Ouvrir frontend JARVIS : `http://localhost:8000`
2. Créer nouveau projet : "Test RAG"
3. Demander : "Crée une API FastAPI pour gérer des todos"
4. Observer les logs backend :
   ```
   Orchestration: enrichissement RAG activé pour CODEUR
   RAG context 'Crée une API FastAPI...': 1847 caractères
   Orchestration: instruction CODEUR enrichie avec RAG
   ```

**Résultat attendu** : Code généré respecte les patterns Library (Pydantic v2, structure routers/, etc.)

---

## 📊 Architecture Finale

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend JARVIS (http://localhost:8000)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Backend JARVIS (FastAPI - port 8000)                        │
│  ├─ api.py                                                  │
│  ├─ services/orchestration.py ← ENRICHISSEMENT RAG ICI     │
│  └─ services/rag_service.py (appels HTTP vers API RAG)     │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP POST /rag/context
┌─────────────────────────────────────────────────────────────┐
│ API RAG (Flask - port 5001)                                 │
│  ├─ src/main.py                                             │
│  ├─ src/rag.py (RAGManager)                                 │
│  └─ src/routes/rag/search.py                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ ChromaDB (./data/rag_db)                                    │
│  └─ Collection: jarvis_library (13 docs × N chunks)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Flux d'Enrichissement RAG

```
1. Utilisateur : "Crée une API FastAPI pour gérer des todos"
                              ↓
2. JARVIS_Maître : Détecte demande de code
   → Délègue : [DEMANDE_CODE_CODEUR: API FastAPI todos]
                              ↓
3. Orchestration : Détecte agent_name == "CODEUR"
   → Appelle rag_service.enrich_instruction()
                              ↓
4. RAGService : POST http://localhost:5001/rag/context
   Body: {"query": "API FastAPI todos", "n_results": 3}
                              ↓
5. API RAG : Recherche similarité sémantique dans ChromaDB
   → Retourne top 3 documents pertinents formatés
                              ↓
6. RAGService : Reçoit contexte (1847 chars)
   → Enrichit instruction :
   
   "Crée une API FastAPI pour gérer des todos
   
   ---
   CONTEXTE LIBRARY (pertinent pour cette tâche) :
   
   [Document 1 - Source: FastAPI, Chunk 0]
   Structure recommandée :
   - routers/ : Routes API
   - models/ : Modèles Pydantic v2
   - services/ : Logique métier
   ...
   
   [Document 2 - Source: Pydantic, Chunk 1]
   Utiliser BaseModel avec Field() pour validation
   ...
   
   [Document 3 - Source: Tests, Chunk 0]
   Tests avec pytest, fixtures, 80%+ coverage
   ...
   ---
   
   Utilise le contexte Library ci-dessus pour respecter
   les standards et patterns recommandés."
                              ↓
7. CODEUR : Reçoit instruction enrichie
   → Génère code respectant patterns Library
                              ↓
8. Orchestration : Parse code, écrit fichiers
   → Retourne résultat à JARVIS_Maître
```

---

## 📈 Impact sur Consommation Tokens

### **Avant RAG**
```
Prompt CODEUR : ~550 tokens
Output : ~1500 tokens
Total : ~2050 tokens/fichier
```

### **Après RAG (3 documents)**
```
Prompt CODEUR : ~550 tokens
Contexte RAG : ~1200 tokens (3 docs × 400 tokens)
Output : ~1500 tokens
Total : ~3250 tokens/fichier
```

**Augmentation** : +1200 tokens/fichier (+218%)

### **Optimisations Possibles**

1. **Réduire à 2 documents** : ~2850 tokens (+164%)
2. **Extraire sections pertinentes** : ~2350 tokens (+115%)
3. **Cache contexte** : Réutiliser pour plusieurs fichiers du même projet

---

## ⚙️ Configuration Avancée

### **Changer Modèle d'Embedding**

Pour un modèle français :
```env
# RAG/.env
RAG_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

**Note** : Nécessite ré-indexation de la Library

### **Ajuster Taille Chunks**

Pour chunks plus petits (moins de tokens) :
```env
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=100
```

### **Filtrer par Agent**

Dans `orchestration.py`, filtrer documents par agent :
```python
instruction = await rag_service.enrich_instruction(
    instruction,
    n_results=3,
    filter_metadata={"agent": "CODEUR"}  # Seulement docs pour CODEUR
)
```

---

## 🐛 Troubleshooting

### **Problème : API RAG non accessible**

**Symptôme** : Logs `API RAG non disponible, instruction non enrichie`

**Solutions** :
1. Vérifier que serveur RAG tourne : `curl http://localhost:5001/`
2. Vérifier port 5001 libre : `netstat -ano | findstr :5001`
3. Relancer serveur RAG : `cd RAG && python run.py`

---

### **Problème : Dépendances manquantes**

**Symptôme** : `ModuleNotFoundError: No module named 'chromadb'`

**Solution** :
```bash
cd RAG
pip install -r requirements-minimal.txt
```

---

### **Problème : Indexation échoue**

**Symptôme** : `❌ FastAPI: Erreur 500`

**Solutions** :
1. Vérifier `backend/db/library_seed.json` existe
2. Vérifier format JSON valide
3. Vérifier logs serveur RAG pour erreur détaillée

---

### **Problème : Contexte RAG vide**

**Symptôme** : Logs `Aucun contexte RAG trouvé, instruction non enrichie`

**Solutions** :
1. Vérifier que Library est indexée : `curl http://localhost:5001/rag/health`
2. Tester recherche manuellement :
   ```bash
   curl -X POST http://localhost:5001/rag/search \
     -H "Content-Type: application/json" \
     -d '{"query": "FastAPI", "n_results": 3}'
   ```
3. Ré-indexer Library : `python RAG/index_jarvis_library.py`

---

## 📝 Maintenance

### **Ajouter Nouveau Document Library**

1. Ajouter document dans `backend/db/library_seed.json`
2. Ré-indexer : `python RAG/index_jarvis_library.py`

### **Vider Collection RAG**

```bash
curl -X DELETE http://localhost:5001/rag/collection/clear
```

### **Vérifier Statut RAG**

```bash
curl http://localhost:5001/rag/health
```

**Réponse** :
```json
{
  "status": "ok",
  "rag_system": "active",
  "collection_info": {
    "collection_name": "jarvis_library",
    "total_chunks": 42,
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "persist_directory": "./data/rag_db"
  }
}
```

---

## ✅ Checklist Déploiement

- [ ] Dépendances RAG installées (`pip install -r requirements-minimal.txt`)
- [ ] Serveur RAG lancé (port 5001)
- [ ] Library indexée (13/13 documents)
- [ ] Recherche RAG testée (retourne résultats pertinents)
- [ ] Backend JARVIS lancé (port 8000)
- [ ] Test projet simple (code respecte patterns Library)
- [ ] Logs vérifiés (enrichissement RAG activé)

---

## 🎯 Prochaines Étapes (Optionnel)

1. **Optimiser tokens** : Réduire à 2 documents, extraire sections pertinentes
2. **Cache contexte** : Réutiliser pour plusieurs fichiers du même projet
3. **Modèle français** : Tester `paraphrase-multilingual-MiniLM-L12-v2`
4. **Intégration directe** : Migrer vers Option B (RAGManager dans backend, sans API Flask)
5. **Métriques** : Mesurer impact RAG sur qualité code (tests, respect patterns)

---

## 📚 Références

- **ChromaDB** : https://docs.trychroma.com/
- **Sentence Transformers** : https://www.sbert.net/
- **LangChain** : https://python.langchain.com/docs/modules/data_connection/document_transformers/text_splitters/recursive_text_splitter
- **Flask** : https://flask.palletsprojects.com/

---

**Auteur** : Cascade AI  
**Date** : 25 février 2026  
**Version** : 1.0
