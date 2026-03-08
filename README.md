# JARVIS 2.0

Assistant IA personnel multi-agent pour la génération de code. Architecture 100% Gemini (Google AI) - Configuration Tier 1 validée le 22 février 2026.

**Statut** : ✅ OPÉRATIONNEL (08/03/2026) - Tests live validés (85.7% succès)

## 🚀 Démarrage Rapide

### ⚡ LANCEMENT EN 1 COMMANDE (RECOMMANDÉ)

**Windows (PowerShell)** :
```powershell
cd "d:\Coding\AppWindows\Jarvis 2.0"
.\start_jarvis_complete.ps1
```

**Alternative (Python multi-plateforme)** :
```bash
python start_jarvis_complete.py
```

**Le script lance automatiquement** :
- ✅ Serveur JARVIS (backend + frontend) sur http://localhost:8000
- ✅ Serveur RAG (enrichissement contexte) sur http://localhost:5001
- ✅ Vérification et installation des dépendances
- ✅ Configuration .env (créé depuis .env.example si absent)

**Options** :
- `--SkipRAG` / `--skip-rag` : Lancer sans serveur RAG
- `--Force` / `--force` : Forcer le lancement même si ports occupés

**Guide complet** : Voir [`DEMARRAGE_RAPIDE.md`](DEMARRAGE_RAPIDE.md)

### Prérequis
- Python 3.11+
- Clé API Google Gemini (Tier 1) : https://aistudio.google.com/app/apikey
- Compte Google Cloud avec facturation activée (pour Tier 1)

### URLs Importantes
- **Application** : `http://localhost:8000/`
- **API Docs** : `http://localhost:8000/docs`
- **Health Check** : `http://localhost:8000/health`
- **RAG API** : `http://localhost:5001/`

### Installation

1. Cloner le projet
```bash
cd "d:\Coding\AppWindows\Jarvis 2.0"
```

2. Installer les dépendances
```bash
pip install -r requirements.txt
```

3. Configurer l'environnement
```bash
cp .env.example .env
# Éditer .env avec votre clé Gemini :
# - GEMINI_API_KEY (Google AI Studio)
# - Configuration agents → modèles Gemini (voir .env.example)
```

4. Lancer le backend
```bash
uvicorn backend.app:app --reload --port 8000
```

Important : exécuter cette commande depuis la racine du projet (sinon erreur `ModuleNotFoundError: No module named 'backend'`).

5. Ouvrir l'application
```text
http://localhost:8000/
```

## 📚 Documentation

**Point d'entrée** : [`docs/_meta/INDEX.md`](docs/_meta/INDEX.md)

### Documents de Référence
- **Architecture** : [`docs/reference/ARCHITECTURE.md`](docs/reference/ARCHITECTURE.md)
- **API** : [`docs/reference/API_SPECIFICATION.md`](docs/reference/API_SPECIFICATION.md)
- **Agents** : [`docs/reference/AGENT_SYSTEM.md`](docs/reference/AGENT_SYSTEM.md)
- **Optimisation Quotas API** : [`docs/reference/OPTIMISATION_QUOTAS_API.md`](docs/reference/OPTIMISATION_QUOTAS_API.md)

## 🏗️ Structure

```
Jarvis 2.0/
├── backend/          # API FastAPI
│   ├── agents/       # Système d'agents
│   ├── ia/           # Providers IA (Gemini)
│   ├── api.py        # Routes
│   └── app.py        # Point d'entrée
├── frontend/         # Interface utilisateur
├── docs/             # Documentation structurée
│   ├── reference/    # Docs contractuels
│   ├── work/         # Docs en cours
│   ├── history/      # Archives
│   └── _meta/        # Index et règles
└── .env              # Configuration (non versionné)
```

## 🔧 Configuration

### Configuration Tier 1 Gemini (Validée)

Variables requises dans `.env` :
```env
# Provider Gemini unique
GEMINI_API_KEY=<votre_clé_google>
GEMINI_MODEL=gemini-2.5-pro

# Configuration agents → modèles Gemini
JARVIS_MAITRE_PROVIDER=gemini
JARVIS_MAITRE_MODEL=gemini-2.5-pro

BASE_PROVIDER=gemini
BASE_MODEL=gemini-2.5-pro

CODEUR_PROVIDER=gemini
CODEUR_MODEL=gemini-2.5-pro

VALIDATEUR_PROVIDER=gemini
VALIDATEUR_MODEL=gemini-3.1-pro-preview
```

**Avantages** :
- ✅ Configuration 100% Gemini (Tier 1)
- ✅ Qualité code excellente (gemini-2.5-pro)
- ✅ Quotas Tier 1 : 150 RPM, 2M TPM, 1K RPD
- ✅ Coût quasi-nul (<$0.05 pour 3 projets complets)
- ✅ Tests live validés : 3/3 réussis (Calculatrice, TODO, MiniBlog)

## 📡 API

### Health Check
```bash
GET http://localhost:8000/
```

### Chat
```bash
POST http://localhost:8000/chat
Content-Type: application/json

{
  "message": "Bonjour",
  "session_id": "optional-uuid"
}
```

## ✅ État Actuel

**Version** : 2.3 (Tests Live Validés - 8 Mars 2026)  
**Statut** : ✅ Système opérationnel - JARVIS + RAG + Tests validés  
**Tests** : 238/241 tests unitaires (99%), **6/7 tests live individuels (85.7%)**

### Agents Disponibles
- **JARVIS_Maître** : Orchestrateur principal (délégation, coordination) — `gemini-2.0-flash`
- **ARCHITECTE** : Conception architecture projets complexes — `gemini-2.5-pro`
- **CODEUR** : Génération de code (Python, tests, documentation) — `gemini-2.5-pro`
- **TESTEUR** : Génération tests pytest exhaustifs — `gemini-2.5-flash`
- **VALIDATEUR** : Contrôle qualité automatique — `gemini-3.1-pro-preview`
- **BASE** : Worker générique (rapports, vérification) — `gemini-2.0-flash-lite`

### Fonctionnalités Implémentées
- ✅ Système multi-agent avec orchestration réelle
- ✅ **Workflow RAPIDE** : CODEUR → TESTEUR → VALIDATEUR (validé)
- ✅ **Workflow COMPLET** : ARCHITECTE → CODEUR → TESTEUR → VALIDATEUR (validé)
- ✅ **Boucle de correction** : Max 6 tentatives, feedbacks précis (validée)
- ✅ **Génération automatique de code sur le disque**
- ✅ Détection automatique de complexité (SIMPLE/COMPLEX)
- ✅ Gestion de projets avec contexte
- ✅ Conversations persistées en base de données
- ✅ Logging structuré avec traçabilité complète
- ✅ Frontend moderne (gestion projets, conversations, chat)
- ✅ Configuration Tier 1 Gemini validée (22/02/2026)
- ✅ **Serveur RAG pour enrichissement contexte (7/03/2026)**
- ✅ **Library locale 40 documents (CONFIG, Python, JS, Architecture)**
- ✅ **Script de lancement automatique (JARVIS + RAG)**
- ✅ **Suite de tests live complète** : 40 tests (unit, intégration, E2E)

### Résultats Tests Live (8 Mars 2026)
- ✅ **Workflow RAPIDE - Calculatrice** : 3 fichiers, validation OK (49.81s)
- ✅ **Workflow RAPIDE - TODO** : 3 fichiers, validation OK (75.58s)
- ✅ **Workflow RAPIDE - Multifichiers** : 4 fichiers, validation OK (66.28s)
- ✅ **Boucle Correction** : 2 fichiers, 0 corrections nécessaires (71.04s)
- ✅ **E2E Calculatrice** : 2 fichiers, 35 tests collectés (72.83s)
- ✅ **E2E API REST** : ARCHITECTE validé, architecture complète (36.95s)
- ❌ **E2E TODO Complet** : 6 corrections, code invalide (381.42s) - **Amélioration nécessaire**

### Projets Validés (100% succès)
- ✅ Calculatrices, utilitaires mathématiques
- ✅ APIs REST simples
- ✅ Projets multi-fichiers structurés

### Limitations Actuelles
- ⚠️ Projets TODO/CRUD complexes (échec validation)
- ⚠️ Tests batch pytest-asyncio (event loop issue)
- ⚠️ Pas d'authentification (usage local uniquement)
- ⚠️ CORS permissif (localhost uniquement)
- ⚠️ Quotas Tier 1 Gemini : 150 RPM, 1K RPD (suffisant pour usage normal)

## 🔮 Prochaines Étapes

Voir [`docs/work/TACHES_RESTANTES.md`](docs/work/TACHES_RESTANTES.md) pour le suivi détaillé.

### Vision Long Terme (Non Implémentée)
Voir [`JARVIS_Base_Document_Complet.md`](JARVIS_Base_Document_Complet.md) pour la vision complète :
- Orchestration réelle (routage intelligent, délégation)
- 9 agents spécialisés (ARCHITECTE, AUDITEUR, PLANIFICATEUR, EXÉCUTANT, etc.)
- Persistance SQLite (sessions, historique, traçabilité)
- Sécurité production (auth JWT, rate limiting, CORS strict)
- Streaming (SSE/WebSocket)

## 📄 Licence

À définir

## 👤 Auteur

Kinder2149
