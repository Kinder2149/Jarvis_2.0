# GUIDE TESTS LIVE — JARVIS 2.0

**Date** : 6 mars 2026  
**Statut** : WORK  
**Objectif** : Valider le paramétrage JARVIS 2.0 via tests live

---

## 🎯 OBJECTIF

Valider que le paramétrage JARVIS 2.0 fonctionne correctement :
- ✅ Prompts agents v5.0 (JARVIS_Maître), v3.1 (CODEUR, BASE)
- ✅ Library avec 40 documents (dont 5 CONFIG)
- ✅ Provider Gemini configuré
- ✅ Workflow 6 phases opérationnel

---

## 📋 PRÉREQUIS

### 1. Vérifier Configuration .env

Le fichier `.env` doit contenir :

```env
# Provider Gemini
GEMINI_API_KEY=votre_cle_api_ici

# Modèles par agent
JARVIS_MAITRE_PROVIDER=gemini
JARVIS_MAITRE_MODEL=gemini-2.0-flash

CODEUR_PROVIDER=gemini
CODEUR_MODEL=gemini-2.5-pro

BASE_PROVIDER=gemini
BASE_MODEL=gemini-2.0-flash-lite

VALIDATEUR_PROVIDER=gemini
VALIDATEUR_MODEL=gemini-3.1-pro-preview
```

**Obtenir clé API** : https://aistudio.google.com/app/apikey

### 2. Vérifier Environnement Virtuel

```powershell
# Activer venv
.\venv\Scripts\Activate.ps1

# Vérifier dépendances
pip install -r requirements.txt
```

---

## 🚀 LANCEMENT SERVEUR

### Option 1 : Script de Lancement (Recommandé)

```powershell
python start_server.py
```

**Résultat attendu** :
```
🚀 Démarrage JARVIS 2.0...
📁 Racine projet : D:\Coding\AppWindows\Jarvis 2.0
🌐 Serveur : http://localhost:8000

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Option 2 : Lancement Direct

```powershell
# Depuis la racine du projet
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### Vérification Serveur

Ouvrir navigateur : http://localhost:8000

✅ Interface JARVIS doit s'afficher

---

## 🧪 TESTS LIVE AUTOMATISÉS

### Lancement Tests

**Terminal 1** : Serveur JARVIS
```powershell
python start_server.py
```

**Terminal 2** : Tests live
```powershell
# Attendre 5 secondes que le serveur démarre
Start-Sleep -Seconds 5

# Lancer tests live
python tests/live/test_live_projects.py
```

### Tests Exécutés

**Niveau 1 : Calculatrice CLI**
- Fichiers attendus : 3 (src/calculator.py, src/main.py, tests/test_calculator.py)
- Tests pytest : 5 tests (add, subtract, multiply, divide, division par zéro)
- Durée : ~30-60 secondes

**Niveau 2 : Gestionnaire TODO**
- Fichiers attendus : 4+ (src/storage.py, src/todo.py, src/cli.py, tests/)
- Tests pytest : 10+ tests (CRUD complet)
- Durée : ~60-90 secondes

**Niveau 3 : API REST Mini-Blog**
- Fichiers attendus : 4+ (src/models.py, src/database.py, src/main.py, tests/)
- Tests pytest : 10+ tests (CRUD + pagination + recherche)
- Durée : ~90-120 secondes

### Résultat Attendu

```
============================================================
  RAPPORT FINAL
============================================================

  ✅ SUCCÈS  Calculatrice CLI        3 fichiers (min 3)       tests OK
  ✅ SUCCÈS  Gestionnaire TODO       4 fichiers (min 4)       tests OK
  ✅ SUCCÈS  API REST Mini-Blog      4 fichiers (min 4)       tests OK

============================================================
  ANALYSE DES CORRECTIONS
============================================================

  ✅ Problème 1 (artefacts markdown) : RÉSOLU — aucun artefact trouvé
  ✅ Problème 3 (max_tokens / fichiers incomplets) : RÉSOLU — tous les fichiers produits
  ✅ Qualité du code : BONNE — tous les tests passent
```

---

## 🔍 VÉRIFICATIONS MANUELLES

### 1. Test Workflow 6 Phases (Interface Web)

**Étape 1 : Créer Projet**
1. Ouvrir http://localhost:8000
2. Cliquer "Nouveau Projet"
3. Nom : `Test TODO Manual`
4. Cliquer "Créer"

**Étape 2 : Envoyer Demande**

Message :
```
Je veux une TODO list simple avec Python FastAPI.

Fonctionnalités :
- Ajouter une tâche
- Marquer comme terminée
- Supprimer une tâche
- Lister toutes les tâches

Stockage : fichier JSON
```

**Étape 3 : Vérifier Phase 1 (Analyse Besoin)**

JARVIS doit répondre :
```
OK, je comprends ton besoin. Voici ce que je propose :

ARCHITECTURE :
- Backend : Python + FastAPI (ta stack préférée)
- BDD : Fichier JSON (simple, pas de serveur BDD)
- Frontend : HTML/CSS/JS vanilla (interface simple)

FICHIERS À CRÉER :
- backend/main.py : API FastAPI avec routes CRUD
- backend/models.py : Modèle Task (Pydantic v2)
- backend/storage.py : Stockage JSON (save/load)
- ...

Tu valides cette architecture ?
```

✅ **Vérifier** :
- Communication en français clair
- Stack par défaut proposée (Python/FastAPI)
- Liste fichiers complète
- Demande validation explicite

**Étape 4 : Valider Architecture**

Message : `OK génère`

**Étape 5 : Vérifier Phase 3 (Génération + Documentation)**

JARVIS doit répondre :
```
✅ CODE GÉNÉRÉ !

FICHIERS CRÉÉS :
- backend/main.py (120 lignes) : API FastAPI avec routes CRUD
- backend/models.py (30 lignes) : Modèle Task avec Pydantic v2
- backend/storage.py (40 lignes) : Stockage JSON avec __init__, save, load
- ...

DOCUMENTATION CRÉÉE :
- README.md : Instructions lancement
- .env.example : Variables nécessaires

PROCHAINE ÉTAPE : Tests
```

✅ **Vérifier** :
- Fichiers créés sur disque (vérifier dossier projet)
- Documentation auto (README.md, .env.example)
- Marqueur délégation `[DEMANDE_CODE_CODEUR:]` présent dans logs

**Étape 6 : Vérifier Phase 5 (Tests Guidés)**

JARVIS doit donner instructions précises :
```
MAINTENANT ON TESTE :

1. LANCE LE BACKEND :
   cd Test_TODO_Manual
   python backend/main.py

2. OUVRE LE FRONTEND :
   Ouvre frontend/index.html dans ton navigateur

3. TESTE LES FONCTIONNALITÉS :
   - Ajoute une tâche "Faire les courses"
   - Marque-la comme terminée
   - Supprime-la

4. RÉSULTAT ATTENDU :
   - Interface : Tâche apparaît, se coche, disparaît
   - Logs backend : POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}
   - Fichier tasks.json : Créé avec les données

Ça marche ou tu as une erreur ?
```

✅ **Vérifier** :
- Instructions claires et précises
- Commandes exactes
- Résultat attendu détaillé

---

### 2. Test Gestion Mémoire

**Étape 1 : Créer Projet Session 1**
1. Créer projet "Test Mémoire"
2. Envoyer demande simple
3. Fermer navigateur

**Étape 2 : Rouvrir Session 2**
1. Rouvrir http://localhost:8000
2. Ouvrir projet "Test Mémoire"
3. Envoyer nouveau message

**Résultat attendu** :

JARVIS doit rappeler contexte :
```
📋 CONTEXTE PROJET :

NOM : Test Mémoire
STACK : Python/FastAPI
DERNIÈRE ACTION : Génération code terminée
FICHIERS CRÉÉS : [liste fichiers]
STATUT : [statut actuel]

PROCHAINES ÉTAPES :
- [Étape 1]
- [Étape 2]

Que veux-tu faire maintenant ?
```

✅ **Vérifier** :
- Rappel contexte automatique
- Informations exactes
- Continuité conversation

---

### 3. Test Accès Documents CONFIG

**Étape 1 : Vérifier Library**

Ouvrir console Python :
```python
import json
from pathlib import Path

library = json.loads(Path("backend/db/library_seed.json").read_text())
config_docs = [d for d in library if d["category"] == "personal"]

print(f"Documents CONFIG : {len(config_docs)}")
for doc in config_docs:
    print(f"  - {doc['name']}")
```

**Résultat attendu** :
```
Documents CONFIG : 5
  - KEAMDER_PROFILE
  - KEAMDER_WORKFLOW
  - JARVIS_ARCHITECTURE
  - KEAMDER_DEV_RULES
  - JARVIS_COMPORTEMENT_GENERIQUE
```

✅ **Vérifier** :
- 5 documents CONFIG présents
- Catégorie "personal"
- Noms corrects

---

## 📊 CRITÈRES DE SUCCÈS

### Tests Automatisés

| Test | Critère | Statut |
|------|---------|--------|
| Calculatrice | 3 fichiers + tests passent | 🔄 |
| TODO | 4+ fichiers + tests passent | 🔄 |
| MiniBlog | 4+ fichiers + tests passent | 🔄 |

### Tests Manuels

| Test | Critère | Statut |
|------|---------|--------|
| Workflow 6 phases | Toutes phases présentes | 🔄 |
| Communication | Français clair, pas jargon | 🔄 |
| Stack par défaut | Python/FastAPI proposé | 🔄 |
| Gestion mémoire | Rappel contexte fonctionne | 🔄 |
| Documents CONFIG | 5 docs accessibles | 🔄 |

---

## ❌ PROBLÈMES CONNUS

### Problème 1 : Serveur ne démarre pas

**Symptôme** : `ModuleNotFoundError: No module named 'backend.api'`

**Solution** :
```powershell
# Utiliser script de lancement
python start_server.py

# OU définir PYTHONPATH
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### Problème 2 : Clé API Gemini manquante

**Symptôme** : Erreur 401 ou "API key not found"

**Solution** :
1. Vérifier `.env` contient `GEMINI_API_KEY=...`
2. Obtenir clé : https://aistudio.google.com/app/apikey
3. Redémarrer serveur

### Problème 3 : Tests timeout

**Symptôme** : Tests échouent avec timeout

**Solution** :
- Vérifier quotas Gemini : https://aistudio.google.com/app/apikey
- Attendre reset quotas (minuit Pacific Time)
- Augmenter timeout dans tests (ligne 91-99)

---

## 📝 RAPPORT TESTS

Après exécution des tests, compléter ce tableau :

### Tests Automatisés

| Test | Fichiers | Tests | Durée | Statut |
|------|----------|-------|-------|--------|
| Calculatrice | _/3 | _/5 | _s | ⬜ |
| TODO | _/4 | _/10 | _s | ⬜ |
| MiniBlog | _/4 | _/10 | _s | ⬜ |

### Tests Manuels

| Test | Résultat | Notes |
|------|----------|-------|
| Workflow 6 phases | ⬜ | |
| Communication FR | ⬜ | |
| Stack par défaut | ⬜ | |
| Gestion mémoire | ⬜ | |
| Documents CONFIG | ⬜ | |

### Problèmes Rencontrés

_[Noter ici les problèmes rencontrés et solutions appliquées]_

---

## 🚀 PROCHAINES ÉTAPES

Si tous les tests passent :
1. ✅ Paramétrage validé
2. ✅ JARVIS 2.0 prêt pour utilisation quotidienne
3. ✅ Peut remplacer Windsurf

Si certains tests échouent :
1. Noter problèmes dans rapport
2. Ajuster prompts si nécessaire
3. Relancer tests

---

**Bon courage pour les tests ! 🧪**
