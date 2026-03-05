# Analyse du Système RAG Fourni

**Date** : 25 février 2026  
**Objectif** : Évaluer le code RAG fourni et proposer un plan d'intégration dans JARVIS 2.0

---

## 📦 Contenu du Dossier RAG

### Structure
```
RAG/
├── .gitignore
├── README.md (erreur lecture - null bytes)
├── requirements.txt (47 dépendances)
├── run.py (script lancement Flask)
├── doc/
│   ├── API_DOCUMENTATION.md (740 lignes)
│   ├── RAG_ROUTES.md (712 lignes)
│   └── setup.md (65 lignes)
├── src/
│   ├── __init__.py
│   ├── main.py (API Flask principale)
│   ├── rag.py (580 lignes - cœur du système)
│   └── routes/
│       └── rag/
│           ├── __init__.py
│           ├── collection.py
│           ├── config.py
│           ├── documents.py
│           ├── health.py
│           └── search.py
└── tests/ (3 items)
```

---

## ✅ Analyse Technique

### 1. **Architecture : API Flask Standalone**

**Type** : Application Flask indépendante (port 5001)

**Composants** :
- **Flask** : Framework web pour exposer l'API
- **ChromaDB** : Base de données vectorielle pour stocker les embeddings
- **Sentence Transformers** : Génération d'embeddings (modèle `all-MiniLM-L6-v2`)
- **LangChain** : Découpage de texte en chunks

**Verdict** : ✅ **Architecture propre et modulaire**

---

### 2. **Fonctionnalités Disponibles**

#### **Classe `RAGManager` (rag.py)**

**Méthodes principales** :

1. **`add_document(file_path, metadata)`** :
   - Charge un fichier (.txt, .md, .pdf, .docx)
   - Découpe en chunks (1000 chars, overlap 200)
   - Génère embeddings
   - Stocke dans ChromaDB

2. **`add_text(text, source, metadata)`** :
   - Ajoute du texte brut (sans fichier)
   - Même processus de chunking/embedding

3. **`search(query, n_results, filter_metadata)`** :
   - Recherche par similarité sémantique
   - Retourne top N documents pertinents
   - Support filtres métadonnées

4. **`get_context_for_query(query, n_results, filter_metadata)`** :
   - Recherche + formatage pour injection dans prompt LLM
   - Retourne contexte formaté prêt à l'emploi

**Verdict** : ✅ **API complète et bien conçue**

---

### 3. **Routes API Disponibles**

**Base URL** : `http://localhost:5001/rag`

| Route | Méthode | Description |
|-------|---------|-------------|
| `/rag/health` | GET | État du système RAG |
| `/rag/documents` | POST | Ajouter un document |
| `/rag/text` | POST | Ajouter du texte brut |
| `/rag/search` | POST | Rechercher documents |
| `/rag/context` | POST | Récupérer contexte formaté |
| `/rag/collection/info` | GET | Info collection |
| `/rag/collection/clear` | DELETE | Vider collection |

**Verdict** : ✅ **API REST complète**

---

### 4. **Configuration**

**Variables d'environnement** :
```env
RAG_COLLECTION_NAME=rag_collection
RAG_PERSIST_DIR=./data/rag_db
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_DEVICE=None  # auto-detect (cuda/cpu)
```

**Verdict** : ✅ **Configuration flexible**

---

### 5. **Dépendances (requirements.txt)**

**Catégories** :

1. **Framework Web** :
   - Flask 3.0.0
   - flask-cors 6.0.1

2. **PyTorch** (⚠️ ATTENTION) :
   - torch 2.2.0 (ROCm 5.7 - GPU AMD)
   - torchvision 0.17.0
   - torchaudio 2.2.0

3. **Transformers & Embeddings** :
   - transformers 4.40.0
   - sentence-transformers 2.7.0
   - accelerate 0.30.0

4. **Base de Données Vectorielle** :
   - chromadb 0.5.0
   - faiss-cpu 1.8.0

5. **Parsing Documents** :
   - pypdf 4.3.1
   - python-docx 1.1.2
   - markdown 3.6
   - beautifulsoup4 4.12.3

6. **RAG Utilities** :
   - langchain 0.3.0
   - langchain-community 0.3.0
   - tiktoken 0.8.0

**Taille totale estimée** : ~5-10 GB (avec PyTorch)

**Verdict** : ⚠️ **Dépendances lourdes (PyTorch ROCm pour GPU AMD)**

---

## 🔍 Compatibilité avec JARVIS 2.0

### ✅ **Points Positifs**

1. **API REST** : Facile à intégrer (appels HTTP depuis JARVIS backend)
2. **Standalone** : Pas de conflit avec JARVIS (port différent)
3. **Fonctionnalités complètes** : Tout ce dont on a besoin (search, context)
4. **Persistance** : ChromaDB sauvegarde les données (pas besoin de ré-indexer)
5. **Métadonnées** : Support filtres (ex: category, agent)

### ⚠️ **Points d'Attention**

1. **PyTorch ROCm** : Conçu pour GPU AMD (pas nécessaire pour CPU)
   - Solution : Utiliser `sentence-transformers` seul (pas besoin de PyTorch complet)
   - Alternative : Modèle d'embedding plus léger

2. **Port séparé** : API sur port 5001, JARVIS sur port 8000
   - Solution : Lancer les 2 serveurs en parallèle
   - Alternative : Intégrer directement `RAGManager` dans JARVIS (pas d'API Flask)

3. **Dépendances lourdes** : ~5-10 GB avec PyTorch
   - Solution : Installer seulement ce qui est nécessaire
   - Alternative : Utiliser un modèle d'embedding plus léger

---

## 🎯 Deux Options d'Intégration

### **Option A : API Standalone (Recommandée pour Démarrage Rapide)**

**Principe** :
- Lancer l'API RAG sur port 5001
- JARVIS appelle l'API via HTTP

**Avantages** :
- ✅ Pas de modification du code RAG
- ✅ Séparation des responsabilités
- ✅ Facile à tester indépendamment

**Inconvénients** :
- ⚠️ 2 serveurs à lancer
- ⚠️ Latence réseau (minime en local)

**Implémentation** :
```python
# backend/services/rag_service.py
import httpx

async def search_library(query: str, n_results: int = 3):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5001/rag/context",
            json={"query": query, "n_results": n_results}
        )
        return response.json()["context"]
```

---

### **Option B : Intégration Directe (Recommandée pour Production)**

**Principe** :
- Copier `RAGManager` dans `backend/services/rag_manager.py`
- Utiliser directement sans API Flask

**Avantages** :
- ✅ 1 seul serveur (JARVIS)
- ✅ Pas de latence réseau
- ✅ Moins de dépendances (pas de Flask pour RAG)

**Inconvénients** :
- ⚠️ Modification du code RAG
- ⚠️ Dépendances ajoutées à JARVIS

**Implémentation** :
```python
# backend/services/rag_manager.py
from RAG.src.rag import RAGManager

# Initialiser au démarrage de JARVIS
rag_manager = RAGManager(
    collection_name="jarvis_library",
    persist_directory="backend/data/rag_db",
    embedding_model="all-MiniLM-L6-v2",
    chunk_size=1000,
    chunk_overlap=200
)

# Utiliser dans orchestration
async def enrich_instruction_with_library(instruction: str):
    context = rag_manager.get_context_for_query(instruction, n_results=3)
    return f"{instruction}\n\nCONTEXTE LIBRARY:\n{context}"
```

---

## 📋 Plan d'Intégration Recommandé

### **Phase 1 : Test Standalone (1-2h)**

1. **Installer dépendances RAG** :
   ```bash
   cd RAG
   pip install sentence-transformers chromadb langchain
   # Pas besoin de PyTorch complet pour CPU
   ```

2. **Indexer la Library JARVIS** :
   ```bash
   python run.py  # Lancer API RAG
   # Puis via API : POST /rag/documents pour chaque fichier Library
   ```

3. **Tester recherche** :
   ```bash
   curl -X POST http://localhost:5001/rag/context \
     -H "Content-Type: application/json" \
     -d '{"query": "API FastAPI", "n_results": 3}'
   ```

**Résultat attendu** : Contexte Library pertinent retourné

---

### **Phase 2 : Intégration JARVIS (2-3h)**

1. **Créer service RAG** :
   - `backend/services/rag_service.py`
   - Appels HTTP vers API RAG

2. **Modifier orchestration** :
   - `backend/services/orchestration.py`
   - Enrichir instruction CODEUR avec contexte RAG

3. **Tester avec projet simple** :
   - "Crée une API FastAPI pour gérer des todos"
   - Vérifier que le code respecte les patterns Library

**Résultat attendu** : Code généré avec patterns Library

---

### **Phase 3 : Optimisation (optionnel)**

1. **Intégration directe** (Option B)
2. **Modèle d'embedding français** (si besoin)
3. **Cache contexte** (réutiliser pour plusieurs fichiers)

---

## 🚀 Recommandation Finale

### **Utiliser Option A (API Standalone) pour commencer**

**Raisons** :
1. ✅ **Rapide** : Pas de modification du code RAG
2. ✅ **Testable** : API indépendante facile à tester
3. ✅ **Réversible** : Pas d'impact sur JARVIS si problème
4. ✅ **Évolutif** : Migration vers Option B facile plus tard

**Prochaines Actions** :
1. Installer dépendances RAG légères (sans PyTorch complet)
2. Lancer API RAG et indexer Library
3. Créer `rag_service.py` dans JARVIS
4. Tester avec 1 projet simple

---

## ❓ Questions à Résoudre

1. **PyTorch ROCm** : Nécessaire uniquement pour GPU AMD. Sur CPU, `sentence-transformers` suffit.
2. **Modèle d'embedding** : `all-MiniLM-L6-v2` est anglais. Pour français : `paraphrase-multilingual-MiniLM-L12-v2`
3. **Persistance** : ChromaDB sauvegarde automatiquement dans `./data/rag_db`

---

## 📊 Verdict Final

**Le système RAG fourni est :**
- ✅ **Complet** : Toutes les fonctionnalités nécessaires
- ✅ **Bien conçu** : Architecture propre et modulaire
- ✅ **Utilisable** : Prêt à l'emploi avec quelques ajustements
- ⚠️ **Dépendances lourdes** : PyTorch ROCm pas nécessaire pour CPU

**Recommandation** : **UTILISER ce système RAG avec Option A (API Standalone)**
