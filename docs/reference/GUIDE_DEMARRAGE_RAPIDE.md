# GUIDE DÉMARRAGE RAPIDE — JARVIS 2.0

**Version** : 1.0  
**Date** : 6 mars 2026  
**Statut** : REFERENCE

---

## 🎯 OBJECTIF

Ce guide vous permet de démarrer avec JARVIS 2.0 en 10 minutes.

JARVIS est votre assistant IA personnel pour créer des projets logiciels sans coder.

---

## 📋 PRÉREQUIS

- **Python 3.11+** installé
- **Git** installé
- **Éditeur de texte** (VS Code, Notepad++, etc.)
- **Navigateur web** (Chrome, Firefox, Edge)

---

## 🚀 INSTALLATION

### 1. Cloner le Projet

```bash
git clone https://github.com/Kinder2149/Jarvis-2.0.git
cd Jarvis-2.0
```

### 2. Créer Environnement Virtuel

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 3. Installer Dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer .env

Créer fichier `.env` à la racine :

```env
# Provider par défaut
DEFAULT_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash

# Clé API Gemini (gratuit Tier 1)
GEMINI_API_KEY=votre_cle_api_ici

# Providers par agent
JARVIS_MAITRE_PROVIDER=gemini
CODEUR_PROVIDER=gemini
BASE_PROVIDER=gemini
VALIDATEUR_PROVIDER=gemini

# Modèles par agent
JARVIS_MAITRE_MODEL=gemini-2.0-flash
CODEUR_MODEL=gemini-2.5-pro
BASE_MODEL=gemini-2.0-flash-lite
VALIDATEUR_MODEL=gemini-3.1-pro-preview
```

**Obtenir clé API Gemini** :
1. Aller sur https://aistudio.google.com/app/apikey
2. Cliquer "Create API key"
3. Copier la clé et la coller dans `.env`

### 5. Lancer JARVIS

```bash
python backend/app.py
```

**Résultat attendu** :
```
INFO:     Started server process
INFO:     Uvicorn running on http://localhost:8000
```

### 6. Ouvrir Interface Web

Ouvrir navigateur : http://localhost:8000

✅ **JARVIS est prêt !**

---

## 💬 PREMIER PROJET (TODO LIST)

### Étape 1 : Créer Nouveau Projet

1. Cliquer sur **"Nouveau Projet"**
2. Nom : `TODO List`
3. Cliquer **"Créer"**

### Étape 2 : Exprimer Besoin

Dans le chat, écrire :

```
Je veux une TODO list simple avec Python FastAPI.

Fonctionnalités :
- Ajouter une tâche
- Marquer comme terminée
- Supprimer une tâche
- Lister toutes les tâches

Stockage : fichier JSON
```

### Étape 3 : Validation Architecture

JARVIS propose une architecture :

```
OK, je comprends ton besoin. Voici ce que je propose :

ARCHITECTURE :
- Backend : Python + FastAPI (ta stack préférée)
- BDD : SQLite (dev local)
- Frontend : HTML/CSS/JS vanilla (simple)

FICHIERS À CRÉER :
- backend/main.py : API FastAPI
- backend/models.py : Modèle Task (Pydantic)
- backend/storage.py : Stockage JSON
- frontend/index.html : Interface utilisateur
- frontend/app.js : Logique frontend
- tests/test_tasks.py : Tests unitaires

Tu valides cette architecture ?
```

**Répondre** : `OK génère`

### Étape 4 : Génération Code

JARVIS génère le code :

```
✅ CODE GÉNÉRÉ !

FICHIERS CRÉÉS :
- backend/main.py (120 lignes) : API FastAPI avec routes CRUD
- backend/models.py (30 lignes) : Modèle Task avec Pydantic v2
- backend/storage.py (40 lignes) : Stockage JSON avec __init__, save, load
- frontend/index.html (80 lignes) : Interface TODO list
- frontend/app.js (100 lignes) : Logique CRUD frontend
- tests/test_tasks.py (60 lignes) : Tests pytest

DOCUMENTATION CRÉÉE :
- README.md : Instructions lancement
- .env.example : Variables nécessaires

PROCHAINE ÉTAPE : Tests
```

### Étape 5 : Tests Guidés

JARVIS guide les tests :

```
MAINTENANT ON TESTE :

1. LANCE LE BACKEND :
   cd TODO_List
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

### Étape 6 : Validation

Si tout fonctionne : **Projet terminé !**

Si erreur : Copier message d'erreur et l'envoyer à JARVIS qui expliquera et corrigera.

---

## 🔧 WORKFLOW COMPLET

### Mode Chat Simple

Pour questions rapides, conseils, explications.

**Exemple** :
```
Utilisateur : C'est quoi Pydantic v2 ?

JARVIS : Pydantic v2 est une bibliothèque Python pour validation de données.
Principales méthodes :
- .model_dump() : Convertir en dict
- .model_validate() : Créer depuis dict
- .model_copy() : Copier avec modifications

Exemple :
[code example]
```

### Mode Projet

Pour créer des projets logiciels complets.

**6 Phases** :

1. **Analyse Besoin** : JARVIS traduit besoin français → architecture technique
2. **Validation Explicite** : Tu valides l'architecture proposée
3. **Génération + Documentation** : JARVIS génère code + README + .env.example
4. **Configuration Services** : JARVIS guide configuration Supabase, Firebase, etc.
5. **Tests Guidés** : JARVIS donne instructions précises pour tester
6. **Debugging** : Si erreur, JARVIS explique et corrige

---

## 🛠️ STACK PAR DÉFAUT

JARVIS utilise cette stack sauf si tu demandes autre chose :

**Backend** : Python + FastAPI  
**Frontend** : HTML/CSS/JS vanilla (simple) ou Angular (complexe)  
**BDD** : SQLite (dev) ou PostgreSQL/Supabase (production)  
**Auth** : Supabase Auth (JWT RS256)  
**Mobile** : Flutter/Dart  
**Déploiement** : Vercel (web), GitHub Pages (statique)

**Alerte déviation** : Si JARVIS propose autre stack, il expliquera pourquoi.

---

## 📚 GESTION MÉMOIRE

JARVIS rappelle automatiquement le contexte à chaque session :

```
📋 CONTEXTE PROJET :

NOM : TODO List
STACK : Python/FastAPI + HTML/CSS/JS vanilla
DERNIÈRE ACTION : Génération code terminée
FICHIERS CRÉÉS : 6 fichiers (backend, frontend, tests)
STATUT : Prêt pour tests

PROCHAINES ÉTAPES :
- Tester fonctionnalités CRUD
- Vérifier logs backend

Que veux-tu faire maintenant ?
```

---

## ❓ TROUBLESHOOTING

### Erreur : "Module not found"

**Cause** : Dépendances non installées

**Solution** :
```bash
pip install -r requirements.txt
```

### Erreur : "Port 8000 already in use"

**Cause** : JARVIS déjà lancé ou autre application sur port 8000

**Solution** :
```bash
# Arrêter JARVIS (Ctrl+C)
# Ou changer port dans backend/app.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Erreur : "API key not found"

**Cause** : Fichier .env manquant ou clé API incorrecte

**Solution** :
1. Vérifier fichier `.env` existe à la racine
2. Vérifier `GEMINI_API_KEY=...` présent
3. Vérifier clé API valide sur https://aistudio.google.com/app/apikey

### Erreur : "CORS policy"

**Cause** : Frontend et backend sur ports différents

**Solution** : JARVIS configure CORS automatiquement. Vérifier backend lancé sur http://localhost:8000

### JARVIS ne répond pas

**Cause** : Quota API Gemini épuisé (Free Tier)

**Solution** :
1. Vérifier quotas : https://aistudio.google.com/app/apikey
2. Attendre reset quotas (minuit Pacific Time)
3. Ou upgrader Tier 1 (gratuit avec compte Google Cloud)

---

## 🎓 PROCHAINES ÉTAPES

1. **Créer premier projet** : TODO list (voir ci-dessus)
2. **Lire exemples** : `docs/reference/EXEMPLES_PROJETS.md`
3. **Tester workflow complet** : Créer projet avec auth (Supabase)
4. **Explorer Library** : 40 documents disponibles (patterns, méthodologies, outils)

---

## 📞 AIDE

**Documentation complète** :
- `docs/reference/EXEMPLES_PROJETS.md` : Exemples concrets
- `docs/reference/ARCHITECTURE.md` : Architecture JARVIS
- `docs/JARVIS CONFIG/` : Configuration agents

**Support** :
- GitHub Issues : https://github.com/Kinder2149/Jarvis-2.0/issues
- Email : valentin.coutry@gmail.com

---

**Bon développement avec JARVIS ! 🚀**
