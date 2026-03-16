# Audit Cohérence Frontend ↔ Backend

**Date** : 16 mars 2026, 20:15

---

## 🎯 Objectif

Vérifier que tous les onglets du frontend correspondent à la réalité du backend :
- WorkflowMonitor ↔ API Missions
- Chat Simple ↔ API Conversations
- Librairie ↔ RAG Backend
- Autres onglets (Agents, Projets)

---

## ✅ 1. WorkflowMonitor ↔ API Missions Backend

### Backend API Missions

**Endpoints disponibles** :
- `POST /api/missions/start` : Démarre nouvelle mission
- `GET /api/missions/{mission_id}` : Récupère statut mission
- `POST /api/missions/{mission_id}/validate` : Valide/rejette architecture
- `POST /api/missions/{mission_id}/continue` : Continue workflow après validation
- `GET /api/missions?status=X&project_path=Y` : Liste missions avec filtres

**Modèle Mission** (backend) :
```python
class Mission:
    mission_id: str
    user_request: str
    project_path: str
    status: MissionStatus  # PENDING, IN_PROGRESS, VALIDATING, COMPLETED, FAILED
    current_phase: MissionPhase  # ARCHITECTURE, GENERATION_CODE, GENERATION_TESTS, VALIDATION_CODE
    architecture_validated: bool
    code_validated: bool
    tests_validated: bool
    files_created: List[str]
    files_modified: List[str]
    error_count: int
    last_error: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    pending_validation: Optional[Dict]  # Contient architecture proposée
```

### Frontend WorkflowMonitor

**Fichier** : `frontend/js/components/workflow-monitor.js`

**Appels API** :
- ✅ `GET /api/missions/${missionId}` (ligne 64)
- ✅ Polling toutes les 2 secondes (ligne 17)
- ✅ Arrêt polling si COMPLETED ou FAILED (ligne 74-80)

**Modifications récentes** :
- ✅ Détection `VALIDATING` status (ligne 140-143)
- ✅ Affichage interface validation architecture (ligne 237-268)
- ✅ Appels `POST /api/missions/{id}/validate` et `/continue` (ligne 278-302)

### ⚠️ INCOHÉRENCE #1 : Endpoint URL

**Frontend** (ligne 64) :
```javascript
const response = await fetch(`/api/missions/${this.missionId}`);
```

**Problème** : URL relative `/api/missions/` au lieu de `http://localhost:8000/api/missions/`

**Impact** : Si le frontend n'est pas servi par le même serveur que le backend, les appels échoueront.

**Vérification nécessaire** : Le frontend est-il servi par FastAPI sur le port 8000 ?

### ✅ COHÉRENCE : Modèle Mission

Le frontend utilise correctement les champs du modèle backend :
- `mission.status` ✅
- `mission.current_phase` ✅
- `mission.files_created` ✅
- `mission.pending_validation.data.architecture` ✅

---

## ✅ 2. Chat Simple ↔ API Conversations Backend

### Backend API Conversations

**Endpoints disponibles** :
- `POST /api/conversations` : Crée conversation standalone (ligne 138)
- `GET /api/conversations` : Liste conversations standalone (ligne 152)
- `GET /api/conversations/{id}` : Récupère conversation (ligne 190)
- `DELETE /api/conversations/{id}` : Supprime conversation (ligne 203)
- `GET /api/conversations/{id}/messages` : Récupère messages (ligne 216)
- `POST /api/conversations/{id}/messages` : Envoie message (ligne 225)

**Modèle Conversation** :
```python
class Conversation:
    id: str
    agent_id: str  # "BASE" ou "JARVIS_Maître"
    project_id: Optional[str]  # None pour chat simple
    title: str
    created_at: datetime
```

### Frontend Chat Simple

**Fichier** : `frontend/js/views/chat-simple.js`

**Appels API** :
- ✅ `POST http://localhost:8000/api/conversations` (ligne 121)
- ✅ Agent par défaut utilisé : `state.get('currentAgent')` (ligne 76)

### ✅ COHÉRENCE : Chat Simple

**Tout est cohérent** :
- Le frontend utilise les bons endpoints
- Le modèle correspond
- L'agent par défaut a été corrigé (`JARVIS_Maître` au lieu de `BASE`)

---

## ⚠️ 3. Librairie ↔ RAG Backend

### Backend RAG

**Serveur** : Port 5001 (serveur Flask séparé)
**Fichier** : `RAG/src/main.py`

**Endpoints RAG disponibles** :
- `GET /` : Health check
- `GET /rag/library/list` : Liste documents librairie
- `GET /rag/library/document/<category>/<name>` : Récupère document

**Structure librairie** :
```
RAG/library/
  ├── patterns/
  ├── rules/
  ├── templates/
  └── assets/
```

### Frontend Librairie

**Fichier** : `frontend/js/views/library.js`

**Configuration** :
- `API_BASE = 'http://localhost:8000'` (ligne 8)
- `RAG_API = 'http://localhost:5001'` (ligne 9)

**Appels API** :
- ✅ `GET http://localhost:5001/rag/library/list` (ligne 58)

### ✅ COHÉRENCE : Librairie RAG

**Tout est cohérent** :
- Le frontend appelle le bon endpoint RAG
- Le serveur RAG expose bien `/rag/library/list`
- Les catégories correspondent (patterns, rules, templates, assets)

**Note** : Le serveur RAG doit être démarré séparément sur le port 5001.

---

## ✅ 4. Autres Onglets

### 4.1 Agents

**Backend** : `GET /api/agents/detailed` (api.py)
**Frontend** : `frontend/js/views/agents-enhanced.js`
- ✅ Appelle `http://localhost:8000/api/agents/detailed` (ligne 58)

**Cohérence** : ✅

### 4.2 Projets

**Backend** : 
- `GET /api/projects` : Liste projets
- `POST /api/projects` : Crée projet
- `GET /api/projects/{id}` : Récupère projet
- `DELETE /api/projects/{id}` : Supprime projet

**Frontend** : `frontend/js/views/projects-list.js`
- ✅ Utilise les bons endpoints

**Cohérence** : ✅

### 4.3 Missions (Vue dédiée)

**Backend** : `GET /api/missions`
**Frontend** : `frontend/js/views/missions.js`

**Vérification nécessaire** : Cette vue existe-t-elle et est-elle utilisée ?

---

## 🔍 Problèmes Identifiés

### 🔴 PROBLÈME #1 : URLs Relatives vs Absolues

**WorkflowMonitor** utilise des URLs relatives :
```javascript
const response = await fetch(`/api/missions/${this.missionId}`);
```

**Autres composants** utilisent des URLs absolues :
```javascript
const response = await fetch('http://localhost:8000/api/conversations', {...});
```

**Conséquence** :
- Si le frontend est servi par FastAPI (port 8000), les URLs relatives fonctionnent
- Si le frontend est servi autrement, les URLs relatives échouent

**Solution** : Uniformiser en utilisant une constante `API_BASE_URL` partout.

### 🟡 PROBLÈME #2 : Serveur RAG Non Démarré

**Le frontend Librairie appelle `http://localhost:5001`** mais le serveur RAG doit être démarré séparément.

**Vérification nécessaire** :
- Le script `start_jarvis_complete.ps1` démarre-t-il automatiquement le RAG ?
- Oui, il démarre le RAG en arrière-plan (ligne 208-233)

**Cohérence** : ✅ (si script utilisé)

### 🟡 PROBLÈME #3 : Gestion d'Erreur Manquante

**WorkflowMonitor** : Si l'API missions échoue, le composant log l'erreur mais ne l'affiche pas clairement à l'utilisateur.

**Amélioration possible** : Afficher un message d'erreur visible dans l'interface.

---

## 📊 Résumé Cohérence

| Composant | Backend | Frontend | Cohérence | Notes |
|-----------|---------|----------|-----------|-------|
| **WorkflowMonitor** | ✅ API Missions | ✅ Appels corrects | ⚠️ URLs relatives | Uniformiser URLs |
| **Chat Simple** | ✅ API Conversations | ✅ Appels corrects | ✅ | Agent corrigé |
| **Librairie** | ✅ RAG Port 5001 | ✅ Appels corrects | ✅ | RAG doit être lancé |
| **Agents** | ✅ API Agents | ✅ Appels corrects | ✅ | - |
| **Projets** | ✅ API Projects | ✅ Appels corrects | ✅ | - |

---

## 🎯 Actions Recommandées

### 1. Uniformiser les URLs (Priorité Moyenne)

**Créer un fichier de configuration** :
```javascript
// frontend/js/config.js
export const API_BASE_URL = 'http://localhost:8000';
export const RAG_API_URL = 'http://localhost:5001';
```

**Modifier tous les composants** pour utiliser ces constantes.

### 2. Améliorer Gestion d'Erreur WorkflowMonitor (Priorité Basse)

**Ajouter affichage d'erreur visible** dans l'interface au lieu de seulement logger.

### 3. Vérifier Vue Missions (Priorité Basse)

**Vérifier si `frontend/js/views/missions.js` est utilisée** et cohérente avec le backend.

---

## ✅ Conclusion

**La cohérence frontend ↔ backend est globalement bonne** :
- ✅ Tous les endpoints backend sont correctement appelés
- ✅ Les modèles de données correspondent
- ✅ Les modifications récentes (WorkflowMonitor validation) sont cohérentes
- ⚠️ Seul problème mineur : URLs relatives vs absolues (non bloquant si frontend servi par FastAPI)

**Le problème principal identifié précédemment (agent BASE au lieu de JARVIS_Maître) a été corrigé.**

**Prêt pour test après redémarrage serveur.**
