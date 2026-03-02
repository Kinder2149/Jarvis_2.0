# Guide d'Utilisation RAG - JARVIS 2.0

**Date** : 2 mars 2026  
**Version** : 1.0  
**Statut** : REFERENCE

---

## 📋 Vue d'Ensemble

Le système RAG (Retrieval-Augmented Generation) de JARVIS 2.0 enrichit automatiquement les instructions envoyées au CODEUR avec du contexte pertinent depuis la Library.

**Bénéfices** :
- ✅ Recherche sémantique (pas seulement nom exact)
- ✅ Enrichissement automatique contexte CODEUR
- ✅ Code généré respecte les standards de la Library
- ✅ Scalable (peut gérer 1000+ documents)

---

## 🏗️ Architecture

### Composants

```
┌─────────────────────────────────────────────────────────┐
│                    Backend Principal                     │
│                   (FastAPI - Port 8000)                  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Orchestration (orchestration.py)         │  │
│  │                                                   │  │
│  │  Si agent = CODEUR:                              │  │
│  │    instruction = rag_service.enrich_instruction()│  │
│  └──────────────────────────────────────────────────┘  │
│                          │                              │
│                          │ HTTP                         │
│                          ▼                              │
└──────────────────────────┼──────────────────────────────┘
                           │
                           │
┌──────────────────────────┼──────────────────────────────┐
│                          │                              │
│                    API RAG Standalone                   │
│                   (Flask - Port 5001)                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │              RAGManager (rag.py)               │    │
│  │                                                 │    │
│  │  • Sentence Transformers (embeddings)          │    │
│  │  • LangChain (text splitting)                  │    │
│  │  • ChromaDB (vector database)                  │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Données : RAG/data/rag_db/ (persisté sur disque)      │
└─────────────────────────────────────────────────────────┘
```

### Flux d'Enrichissement

1. **Utilisateur** : "Crée une API FastAPI avec tests"
2. **JARVIS_Maître** : Délègue au CODEUR
3. **Orchestration** : Détecte agent = CODEUR
4. **RAG Service** : Appelle API RAG `/rag/context`
5. **API RAG** : Recherche sémantique dans ChromaDB
6. **API RAG** : Retourne top 3 documents pertinents
7. **RAG Service** : Formate contexte + instruction
8. **CODEUR** : Reçoit instruction enrichie (42 → 2045 chars)
9. **CODEUR** : Génère code respectant les standards Library

---

## 🚀 Démarrage

### 1. Lancer l'API RAG

**Terminal 1** (API RAG) :
```bash
cd RAG
python run.py
```

**Vérification** :
```bash
curl http://localhost:5001/rag/health
```

### 2. Lancer le Backend Principal

**Terminal 2** (Backend JARVIS) :
```bash
cd backend
$env:PYTHONPATH = ".."
uvicorn backend.app:app --reload --port 8000
```

### 3. Ouvrir le Frontend

Navigateur : `http://localhost:8000`

---

## 📊 Vérification du Système

### Vérifier l'Indexation

```bash
curl http://localhost:5001/rag/collection/info
```

**Résultat attendu** :
```json
{
  "collection_name": "jarvis_library",
  "document_count": 13,
  "chunk_count": 16,
  "embedding_model": "all-MiniLM-L6-v2"
}
```

### Tester la Recherche Sémantique

```bash
python test_rag_search.py
```

**Résultat attendu** : 3 documents pertinents avec scores de similarité

### Tester l'Enrichissement

```bash
python test_rag_enrichment.py
```

**Résultat attendu** : Instruction enrichie avec contexte Library (ratio ~50x)

---

## 🔧 Configuration

### Variables d'Environnement (`RAG/.env`)

```env
# Collection ChromaDB
RAG_COLLECTION_NAME=jarvis_library

# Répertoire de persistance
RAG_PERSIST_DIR=./data/rag_db

# Modèle d'embedding
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Chunking
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200

# Device (cpu, cuda, ou None pour auto)
RAG_DEVICE=cpu
```

### Paramètres RAG Service (`backend/services/rag_service.py`)

```python
RAG_API_URL = "http://localhost:5001"  # URL API RAG
RAG_TIMEOUT = 10.0                     # Timeout requêtes (secondes)
DEFAULT_N_RESULTS = 3                  # Nombre de documents à récupérer
```

---

## 📚 Utilisation

### Ajouter des Documents à la Library

**Via API Backend** :
```bash
curl -X POST http://localhost:8000/api/library \
  -H "Content-Type: application/json" \
  -d '{
    "category": "libraries",
    "name": "React",
    "description": "Framework JavaScript",
    "content": "# React\n\n## Installation\nnpm install react",
    "tags": ["javascript", "frontend"],
    "agents": ["CODEUR"]
  }'
```

**Réindexer dans RAG** :
```bash
cd RAG
python index_jarvis_library.py
```

### Rechercher dans la Library

**Recherche exacte (Library API)** :
```bash
curl "http://localhost:8000/api/library?category=libraries"
```

**Recherche sémantique (RAG API)** :
```bash
curl -X POST http://localhost:5001/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "comment tester une API", "n_results": 3}'
```

### Enrichissement Automatique

L'enrichissement est **automatique** pour le CODEUR. Aucune action requise.

**Logs à surveiller** (backend) :
```
Orchestration: enrichissement RAG activé pour CODEUR
Orchestration: instruction CODEUR enrichie avec RAG
```

---

## 🛠️ Maintenance

### Réindexer la Library

**Quand** : Après ajout/modification de documents dans la Library

**Comment** :
```bash
cd RAG
python index_jarvis_library.py
```

**Durée** : ~10 secondes pour 13 documents

### Vider la Collection

```bash
curl -X DELETE http://localhost:5001/rag/collection/delete
```

**⚠️ Attention** : Supprime tous les documents indexés. Réindexer après.

### Changer le Modèle d'Embedding

1. Modifier `RAG/.env` : `RAG_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2`
2. Redémarrer API RAG : `cd RAG && python run.py`
3. Réindexer : `python index_jarvis_library.py`

**Modèles recommandés** :
- `all-MiniLM-L6-v2` : Anglais, léger, rapide (par défaut)
- `paraphrase-multilingual-MiniLM-L12-v2` : Multilingue (français)
- `all-mpnet-base-v2` : Anglais, plus précis, plus lent

---

## 🐛 Dépannage

### API RAG Non Accessible

**Symptôme** : `API RAG non disponible` dans les logs

**Solutions** :
1. Vérifier que l'API RAG est lancée : `curl http://localhost:5001/rag/health`
2. Vérifier le port dans `rag_service.py` (doit être 5001)
3. Vérifier les dépendances : `pip list | grep -E "chromadb|sentence-transformers"`

### Aucun Contexte Ajouté

**Symptôme** : `Aucun contexte RAG trouvé` dans les logs

**Solutions** :
1. Vérifier que la collection est indexée : `curl http://localhost:5001/rag/collection/info`
2. Réindexer si vide : `cd RAG && python index_jarvis_library.py`
3. Tester la recherche : `python test_rag_search.py`

### Erreur ChromaDB

**Symptôme** : `chromadb.errors.InvalidCollectionException`

**Solutions** :
1. Supprimer la base : `rm -rf RAG/data/rag_db/`
2. Relancer API RAG : `cd RAG && python run.py`
3. Réindexer : `python index_jarvis_library.py`

### Performance Lente

**Symptôme** : Enrichissement prend > 5 secondes

**Solutions** :
1. Réduire `n_results` dans `rag_service.py` (3 → 2)
2. Utiliser un modèle plus léger : `all-MiniLM-L6-v2`
3. Activer GPU si disponible : `RAG_DEVICE=cuda` dans `.env`

---

## 📈 Métriques

### Statistiques Actuelles

| Métrique | Valeur |
|----------|--------|
| Documents Library | 13 |
| Chunks indexés | 16 |
| Modèle embedding | all-MiniLM-L6-v2 |
| Taille moyenne chunk | ~600 caractères |
| Ratio enrichissement | ~50x |
| Temps recherche | < 1 seconde |

### Limites

- **Scalabilité** : Testé jusqu'à 100 documents (peut gérer 1000+)
- **Latence** : +1-2 secondes par requête CODEUR
- **Mémoire** : ~500 MB (modèle embedding + ChromaDB)
- **Disque** : ~50 MB pour 100 documents

---

## 🔐 Sécurité

### Accès API RAG

**Actuel** : Aucune authentification (localhost uniquement)

**Recommandations** :
- Ne PAS exposer l'API RAG sur internet
- Utiliser un reverse proxy avec auth si nécessaire
- Limiter CORS à `localhost:8000`

### Données Sensibles

**⚠️ Attention** : Les documents Library sont indexés en clair dans ChromaDB.

**Recommandations** :
- Ne PAS indexer de secrets (API keys, passwords)
- Ne PAS indexer de données personnelles sensibles
- Sauvegarder `RAG/data/rag_db/` régulièrement

---

## 📝 Logs

### Backend Principal

**Fichier** : `backend/logs/jarvis_audit.log`

**Logs RAG** :
```
Orchestration: enrichissement RAG activé pour CODEUR
Orchestration: instruction CODEUR enrichie avec RAG
API RAG non disponible, instruction non enrichie
```

### API RAG

**Sortie console** :
```
RAGManager initialisé avec collection 'jarvis_library'
127.0.0.1 - - [02/Mar/2026 22:22:52] "POST /rag/search HTTP/1.1" 200 -
```

---

## 🎯 Bonnes Pratiques

### 1. Structurer les Documents Library

**Bon** :
```markdown
# FastAPI — Référence rapide

## Installation
pip install fastapi uvicorn

## App de base
from fastapi import FastAPI
...
```

**Mauvais** :
```
FastAPI c'est bien. Voici du code : [code mal formaté]
```

### 2. Utiliser des Tags Pertinents

**Bon** : `["python", "web", "api"]`  
**Mauvais** : `["truc", "machin"]`

### 3. Catégoriser Correctement

- `libraries` : Frameworks, bibliothèques
- `methodologies` : Processus, workflows
- `prompts` : Templates de prompts
- `personal` : Conventions personnelles

### 4. Maintenir la Library à Jour

- Réindexer après chaque modification
- Supprimer les documents obsolètes
- Versionner les documents importants

---

## 🚀 Prochaines Étapes

### Améliorations Possibles

1. **Filtrage par agent** : Corriger indexation pour utiliser `agents` (liste)
2. **Recherche hybride** : Combiner recherche exacte + sémantique
3. **Cache** : Mettre en cache les résultats fréquents
4. **Métriques** : Dashboard de monitoring RAG
5. **Feedback** : Permettre à l'utilisateur de noter la pertinence

### Évolutions Futures

1. **Multi-collection** : Séparer Library / Projets / Documentation
2. **Reranking** : Améliorer le scoring des résultats
3. **Extraction d'entités** : Détecter automatiquement les concepts clés
4. **Génération de résumés** : Résumer les documents longs

---

## 📚 Références

### Documentation Technique

- `RAG/doc/RAG_ROUTES.md` : API complète
- `RAG/src/rag.py` : Code RAGManager
- `backend/services/rag_service.py` : Intégration backend

### Fichiers Clés

- `RAG/.env` : Configuration
- `RAG/run.py` : Lancement API
- `RAG/index_jarvis_library.py` : Script indexation
- `backend/db/library_seed.json` : Seed data

### Tests

- `test_rag_search.py` : Test recherche sémantique
- `test_rag_enrichment.py` : Test enrichissement

---

## ✅ Checklist de Validation

### Installation
- [ ] Dépendances RAG installées
- [ ] Fichier `.env` créé dans `RAG/`
- [ ] API RAG démarre sans erreur

### Indexation
- [ ] Script `index_jarvis_library.py` exécuté
- [ ] 13 documents indexés
- [ ] `/rag/collection/info` retourne 16 chunks

### Tests
- [ ] `test_rag_search.py` : 3 résultats pertinents
- [ ] `test_rag_enrichment.py` : Ratio ~50x
- [ ] Logs backend : "enrichissement RAG activé"

### Production
- [ ] API RAG lancée au démarrage
- [ ] Backend principal lancé
- [ ] Frontend accessible
- [ ] Création projet teste enrichissement

---

**Dernière mise à jour** : 2 mars 2026  
**Auteur** : Cascade AI  
**Version** : 1.0
