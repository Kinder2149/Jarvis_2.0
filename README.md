# JARVIS 2.0 - Chat Simple Multi-Agents

Assistant IA personnel avec chat simple et sélection d'agent. Architecture simplifiée sans base de données, stockage JSON unique.

**Statut** : ✅ OPÉRATIONNEL - Version simplifiée (18/03/2026)

## 🚀 Démarrage Rapide

### Installation

1. **Cloner le projet**
```bash
cd "c:\DEV\PROJETS\intelligence_artificielle\Jarvis-2.0"
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec votre clé Gemini
```

4. **Lancer l'application**
```bash
python start_server.py
# ou
uvicorn backend.app:app --reload --port 8000
```

5. **Ouvrir l'application**
```
http://localhost:8000/
```

## 📋 Prérequis

- Python 3.11+
- Clé API Google Gemini : https://aistudio.google.com/app/apikey

## 🏗️ Architecture

### Backend
- **FastAPI** : API REST minimaliste
- **Stockage JSON** : Fichier unique `backend/data/conversations.json`
- **5 Agents IA** : JARVIS_MAITRE, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR
- **Pas de base de données** : Système déconnecté, BDD archivée

### Frontend
- **Vanilla JavaScript** : SPA avec router
- **3 Pages** : Home, Chat, Agents
- **Chat avec dropdown** : Sélection d'agent avant conversation

### Archivés
- Base de données SQLite → `_archived/`
- Système RAG → `_archived/RAG/`
- Documentation workflow → `docs/history/archived_workflow_2026_03_18/`

## 🤖 Agents Disponibles

| Agent | Rôle | Modèle |
|-------|------|--------|
| **JARVIS_MAITRE** | Assistant personnel, orchestrateur | gemini-2.0-flash |
| **ARCHITECTE** | Conception architecture projets | gemini-2.5-pro |
| **CODEUR** | Génération de code Python | gemini-2.5-pro |
| **TESTEUR** | Génération tests pytest | gemini-2.5-flash |
| **VALIDATEUR** | Contrôle qualité code | gemini-3.1-pro-preview |

## 📡 API

### Endpoints Disponibles

**Conversations**
- `POST /api/conversations` - Créer conversation avec agent
- `GET /api/conversations` - Lister conversations
- `GET /api/conversations/{id}` - Détail conversation
- `DELETE /api/conversations/{id}` - Supprimer conversation

**Messages**
- `GET /api/conversations/{id}/messages` - Historique messages
- `POST /api/conversations/{id}/messages` - Envoyer message

**Agents**
- `GET /agents` - Liste agents disponibles

**Health Check**
- `GET /health` - Vérification serveur

## 💬 Utilisation

1. **Ouvrir l'application** : http://localhost:8000/
2. **Sélectionner un agent** dans le dropdown
3. **Cliquer sur "Activer"** pour créer une conversation
4. **Chatter** avec l'agent sélectionné
5. **Changer d'agent** : bouton "Nouvelle" pour créer une nouvelle conversation

## 📁 Structure Projet

```
Jarvis-2.0/
├── backend/
│   ├── agents/              # 5 agents IA
│   ├── ia/                  # Providers (Gemini)
│   ├── models/              # Models Pydantic simplifiés
│   ├── storage/             # ConversationStore (JSON)
│   ├── api.py               # Routes API (7 endpoints)
│   └── app.py               # Application FastAPI
├── frontend/
│   ├── js/
│   │   ├── views/           # home.js, chat-simple.js, agents.js
│   │   ├── components/      # navbar.js, chat.js, agent-selector.js
│   │   └── core/            # router.js, state.js
│   ├── css/                 # Styles
│   └── index.html
├── _archived/               # BDD, RAG, Workflow (archivés)
├── config_agents/           # Configuration agents (.md)
├── .env                     # Configuration (non versionné)
├── requirements.txt         # Dépendances Python
└── README.md
```

## 🔧 Configuration

### Variables d'Environnement (.env)

```env
# Clé API Gemini
GEMINI_API_KEY=votre_clé_ici

# Configuration agents (optionnel, valeurs par défaut)
JARVIS_MAITRE_MODEL=gemini-2.0-flash
ARCHITECTE_MODEL=gemini-2.5-pro
CODEUR_MODEL=gemini-2.5-pro
TESTEUR_MODEL=gemini-2.5-flash
VALIDATEUR_MODEL=gemini-3.1-pro-preview
```

## ✅ Fonctionnalités

- ✅ Chat simple avec sélection d'agent
- ✅ 5 agents IA spécialisés
- ✅ Stockage conversations en JSON
- ✅ Interface moderne et épurée
- ✅ Navigation simplifiée (3 pages)
- ✅ Pas de base de données
- ✅ Pas de système de workflow complexe

## ❌ Fonctionnalités Supprimées

- ❌ Projets et gestion de fichiers
- ❌ Missions et workflow multi-agents
- ❌ Orchestration automatique
- ❌ Knowledge Base / Library
- ❌ Base de données SQLite
- ❌ Système RAG

## 🔮 Évolution Future

Si besoin de réintégrer les fonctionnalités avancées :
- Tout est archivé dans `_archived/`
- Documentation workflow dans `docs/history/archived_workflow_2026_03_18/`
- Base de données dans `_archived/jarvis_data.db.backup_2026_03_18`
- Système RAG dans `_archived/RAG/`

## 📚 Documentation

- **Architecture simplifiée** : `ARCHITECTURE_SIMPLE.md`
- **Plan de redémarrage** : `.windsurf/plans/jarvis-reset-simple-chat-2c04c6.md`

## 🐛 Dépannage

**Port 8000 déjà utilisé** :
```powershell
# Tuer le processus sur le port 8000
$p = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($p) { Stop-Process -Id $p -Force }
```

**Erreur module backend** :
```bash
# Vérifier que vous êtes à la racine du projet
cd "c:\DEV\PROJETS\intelligence_artificielle\Jarvis-2.0"
python -m uvicorn backend.app:app --reload
```

## 📄 Licence

À définir

## 👤 Auteur

Kinder2149
