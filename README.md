# JARVIS 2.0

Assistant IA personnel multi-agent pour la génération de code. Architecture 100% Gemini (Google AI) - Configuration Tier 1 validée le 22 février 2026.

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.11+
- Clé API Google Gemini (Tier 1) : https://aistudio.google.com/app/apikey
- Compte Google Cloud avec facturation activée (pour Tier 1)

### Lancer le projet (backend + frontend)

Le frontend est servi par le backend FastAPI (fichiers statiques montés sur `/frontend` et page principale sur `/`). Il n'y a donc pas de serveur frontend séparé à démarrer.

1. Installer les dépendances
```bash
pip install -r requirements.txt
```

2. Configurer l'environnement
```bash
cp .env.example .env
# Éditer .env avec votre clé Gemini :
# - GEMINI_API_KEY (Google AI Studio)
# - Configuration agents → modèles Gemini (voir .env.example)
```

3. Lancer le backend (qui sert aussi le frontend)
```bash
uvicorn backend.app:app --reload --port 8000
```

Important : cette commande doit être exécutée depuis la racine du projet (sinon erreur `ModuleNotFoundError: No module named 'backend'`).

Si tu es déjà dans `backend/` (PowerShell) :
```powershell
$env:PYTHONPATH = ".."
uvicorn backend.app:app --reload --port 8000
```

4. Ouvrir l'application : `http://localhost:8000/`

URLs utiles :
- Frontend (app) : `http://localhost:8000/`
- Health : `http://localhost:8000/health`
- API (OpenAPI) : `http://localhost:8000/docs`

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

**Version** : 2.1 (Configuration Tier 1 Gemini Validée - 22 Février 2026)  
**Statut** : ✅ Système opérationnel - Configuration Gemini unique validée  
**Tests** : 238/241 tests unitaires (99%), 3/3 tests live réussis

### Agents Disponibles
- **JARVIS_Maître** : Orchestrateur principal (délégation, coordination) — `gemini-2.5-pro`
- **CODEUR** : Génération de code (Python, tests, documentation) — `gemini-2.5-pro`
- **BASE** : Worker générique (rapports, vérification) — `gemini-2.5-pro`
- **VALIDATEUR** : Contrôle qualité automatique — `gemini-3.1-pro-preview`

### Fonctionnalités Implémentées
- ✅ Système multi-agent avec orchestration réelle
- ✅ Délégation JARVIS_Maître → CODEUR opérationnelle
- ✅ **Génération automatique de code sur le disque**
- ✅ Boucle de vérification CODEUR/BASE adaptative
- ✅ Protections anti-boucle (max 3 iterations, timeout 30s)
- ✅ Gestion de projets avec contexte
- ✅ Conversations persistées en base de données
- ✅ Logging structuré avec traçabilité complète
- ✅ Frontend moderne (gestion projets, conversations, chat)
- ✅ Configuration Tier 1 Gemini validée (22/02/2026)

### Résultats Tests Live Validés
- ✅ **Calculatrice CLI** : 4 fichiers, 9/9 tests passants
- ✅ **Gestionnaire TODO** : 7 fichiers, tests passants
- ✅ **API REST Mini-Blog** : 5 fichiers, tests passants
- ✅ **Qualité code** : Excellente (docstrings, gestion erreurs, tests complets)

### Limitations Actuelles
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
