# SPEC FRONTEND V2 — JARVIS
> Document de référence pour toutes les missions Cascade V2.
> Cascade doit lire ce fichier en entier avant chaque mission.

---

## 1. CONTEXTE

JARVIS est une interface locale d'orchestration IA multi-modèles.
- Backend FastAPI Python 3.11, port 8000, stable (162 tests passants)
- 1 seul utilisateur, Windows 10, Chrome/Edge
- Le launcher (`launcher/JARVIS.exe`) démarre le serveur et ouvre `http://localhost:8000`
- FastAPI sert les fichiers HTML depuis `/frontend` à l'URL `/app/`
- `GET /` redirige vers `/app/index.html`

**Stack frontend — IMMUABLE :**
HTML5 + CSS3 + JavaScript Vanilla. Zéro framework JS (pas de React, Vue, Angular, jQuery).

---

## 2. PRINCIPE DIRECTEUR

UI inspirée de Claude.ai/ChatGPT : sidebar de navigation + zone principale + explorateur droit.

Deux types de sessions dans JARVIS :
- 💬 **Chat** : conversation texte avec l'IA
- ⚙️ **Module Code** : workflow IA multi-steps (ex "pipeline")

Les deux apparaissent dans la sidebar comme des entrées d'historique, groupées par projet.

---

## 3. LAYOUT GLOBAL — 3 PANNEAUX

```
┌─────────────────┬──────────────────────────┬───────────────┐
│  SIDEBAR GAUCHE │     ZONE PRINCIPALE      │ EXPLORATEUR   │
│  id="sidebar"   │     id="main-content"    │ id="explorer" │
│  ~260px         │     flex: 1              │  ~280px       │
│  collapsible    │                          │  collapsible  │
└─────────────────┴──────────────────────────┴───────────────┘
```

- Sidebar gauche : toujours présente sur toutes les pages
- Explorateur droit : visible uniquement si le projet actif a un `local_path` défini
- Les deux panneaux ont un bouton collapse indépendant
- Sur mobile (< 768px) : sidebar et explorateur cachés par défaut

### HTML Shell (identique sur toutes les pages)
```html
<body>
  <div id="app-layout">
    <aside id="sidebar"><!-- sidebar.js injecte ici --></aside>
    <main id="main-content"><!-- contenu de la page --></main>
    <aside id="explorer"><!-- explorer.js injecte ici --></aside>
  </div>
  <div id="toast-container"></div>
</body>
```

---

## 4. STRUCTURE FICHIERS COMPLÈTE

```
frontend/
  index.html              ← Dashboard (page par défaut, vue bilan)
  project.html            ← Vue projet (hub)
  chat.html               ← Conversation chat
  module-code.html        ← Module Code (workflows IA)
  settings.html           ← Paramètres (rarement utilisé)

  assets/
    style.css             ← CSS global (variables + layout + tous composants)
    js/
      api.js              ← COUCHE DONNÉES : tous les appels HTTP, rien d'autre
      shared.js           ← COUCHE PARTAGÉE : init layout, event bus, URL utils, formatage
      sidebar.js          ← Sidebar gauche : rendu, navigation, groupement projets
      explorer.js         ← Panneau droit : arborescence fichiers, preview
      ui.js               ← Widgets réutilisables : Toast, Modal, StatusBadge, CostBadge
      dashboard.js        ← Page dashboard
      project.js          ← Page vue projet
      chat.js             ← Page chat
      module-code.js      ← Page module code (polling toutes les 2s, steps, validation)
      settings.js         ← Page paramètres
```

### Chargement JS par page
```html
<!-- index.html -->
<script src="assets/js/api.js"></script>
<script src="assets/js/shared.js"></script>
<script src="assets/js/sidebar.js"></script>
<script src="assets/js/ui.js"></script>
<script src="assets/js/dashboard.js"></script>

<!-- chat.html -->
<script src="assets/js/api.js"></script>
<script src="assets/js/shared.js"></script>
<script src="assets/js/sidebar.js"></script>
<script src="assets/js/explorer.js"></script>
<script src="assets/js/ui.js"></script>
<script src="assets/js/chat.js"></script>

<!-- module-code.html -->
<script src="assets/js/api.js"></script>
<script src="assets/js/shared.js"></script>
<script src="assets/js/sidebar.js"></script>
<script src="assets/js/ui.js"></script>
<script src="assets/js/module-code.js"></script>

<!-- project.html -->
<script src="assets/js/api.js"></script>
<script src="assets/js/shared.js"></script>
<script src="assets/js/sidebar.js"></script>
<script src="assets/js/explorer.js"></script>
<script src="assets/js/ui.js"></script>
<script src="assets/js/project.js"></script>

<!-- settings.html -->
<script src="assets/js/api.js"></script>
<script src="assets/js/shared.js"></script>
<script src="assets/js/sidebar.js"></script>
<script src="assets/js/ui.js"></script>
<script src="assets/js/settings.js"></script>
```

---

## 5. MODULES JS — RESPONSABILITÉS

### api.js — Couche données
- Constante `BASE_URL = window.location.origin`
- Helpers HTTP privés : `_get(path)`, `_post(path, body)`, `_patch(path, body)`, `_del(path)`
- Objet exporté global `API` avec une fonction nommée par endpoint (voir section 7)
- Gestion erreurs centralisée : si réponse non-ok, throw Error avec le message `detail` du JSON

### shared.js — Couche partagée
- `initLayout()` : appelé au DOMContentLoaded sur chaque page, initialise sidebar et explorateur
- `getURLParam(name)` : lit les paramètres URL (`?id=3&project_id=2`)
- `EventBus` : objet avec `emit(event, data)` et `on(event, callback)` via CustomEvent
- `formatDate(isoString)` : retourne "Aujourd'hui 14h32" / "Hier" / "12 janv."
- `formatCost(usd)` : retourne "$0.024" avec 3 décimales
- Récupère et stocke le projet actif en `window.currentProjectId`

### sidebar.js — Navigation gauche
- `renderSidebar(projects, conversations, sessions)` : génère et injecte le HTML de la sidebar
- Regroupe les conversations et sessions par `project_id`
- Marque l'item actif selon l'URL courante
- Gère le bouton collapse (toggle class `sidebar--collapsed` sur `#sidebar`)
- Bouton "Nouveau Chat" → `POST /chat/conversations` puis redirect vers `chat.html?id=X`
- Bouton "Nouveau Module Code" → modal de sélection workflow → `POST /pipelines/start` puis redirect

### explorer.js — Panneau droit fichiers
- `initExplorer(projectId)` : appelle `API.listLocalFiles(projectId)`, rend l'arborescence
- Arborescence cliquable : dossiers repliables, fichiers ouvrants
- Clic fichier → appelle `API.readFile(projectId, filepath)`, affiche contenu dans panneau preview en bas
- Bouton `[🗺️ Graphify]` : déclenche l'analyse graphify du dossier (placeholder pour l'instant)
- Si `local_path` null → afficher message "Aucun dossier lié — éditer le projet pour en ajouter un"
- Collapse toggle indépendant de la sidebar

### ui.js — Widgets réutilisables
- `showToast(message, type)` : type = 'success' | 'error' | 'warning'. Auto-disparaît après 4s
- `showModal(title, content, actions)` : modal générique avec overlay
- `closeModal()` : ferme le modal actif
- `statusBadge(status)` : retourne un `<span class="badge badge--{status}">` (pending/running/completed/error/waiting)
- `costBadge(usdAmount)` : retourne `<span class="badge badge--cost">$0.024</span>`

### dashboard.js
- Charge : tous les projets, toutes les conversations, les logs récents
- Affiche timeline chronologique mixant chats et modules code (triés par date desc)
- Section "Pipelines actifs" si des sessions non-terminées existent
- Filtres date : Aujourd'hui / Hier / Cette semaine

### project.js
- Charge le projet via `API.getProject(id)`, ses sessions via `API.getProjectSessions(id)`, ses conversations via `API.getConversations(id)`
- Affiche : nom, path, local_path, instructions (éditables inline), liste conversations mixte triée par date
- Bouton "Nouveau Chat" → crée et redirige
- Bouton "Nouveau Module Code" → modal workflow → lance et redirige
- Bouton "Modifier dossier local" → champ input + sauvegarde via `API.updateProject`

### chat.js
- Charge la conversation via `API.getConversation(id)`
- Rendu des messages avec markdown minimal (gras, code inline, blocs code)
- Envoi message → `API.sendMessage(id, content)` → affiche réponse IA au retour
- Titre de conversation éditable (double-clic)
- Auto-scroll vers le bas après chaque message
- État loading pendant la réponse IA (bouton désactivé + spinner)

### module-code.js
- Charge la session via `API.getPipeline(sessionId)`
- **Polling actif toutes les 2 secondes** quand `session.status` est 'CREATED' ou 'RUNNING'
- Arrêt polling si status = 'COMPLETED' | 'ABORTED' | 'ERROR'
- Rendu dynamique des steps selon leur status :
  - `PENDING` → cercle vide
  - `RUNNING` → spinner animé
  - `COMPLETED` → ✅ + résumé output (100 premiers chars)
  - `ERROR` → ❌ + message erreur + bouton [Relancer]
  - `WAITING_VALIDATION` → zone validation s'ouvre (approve/reject + feedback)
- Si step a `output_type === 'diff'` → afficher diff viewer avant validation
- Bouton [Abandonner] → `API.abortPipeline(sessionId)` + confirmation modal
- Coût total en temps réel depuis `API.getPipelineCosts(sessionId)`
- Mode historique si session COMPLETED : tout en lecture seule

### settings.js
- Charge config via `API.getConfig()` qui retourne clés masquées "...xxxx"
- Pour chaque clé : affiche état (définie / non définie), toggle œil pour révéler la valeur masquée
- Mode édition par clé : clic [Modifier] → input text vide → [Sauvegarder] ou [Annuler]
- Test connexion par provider → badge vert ✅ ou rouge ❌ en temps réel
- Sélection modèles par type (routing/code/analysis) via dropdowns alimentés par `API.getAvailableModels()`

---

## 6. CSS — CONVENTIONS

### Variables existantes (conserver)
```css
--bg-primary: #0f1117
--bg-card: #1a1d2e
--bg-input: #252840
--accent: #6366f1
--accent-hover: #4f46e5
--success: #22c55e
--warning: #f59e0b
--danger: #ef4444
--text-primary: #e2e8f0
--text-muted: #64748b
--border: #2d3148
```

### Nouvelles variables à ajouter
```css
--sidebar-width: 260px
--sidebar-collapsed-width: 52px
--explorer-width: 280px
--header-height: 52px
```

### Conventions classes CSS
- Layout : `.app-layout`, `.sidebar`, `.main-content`, `.explorer`
- États sidebar : `.sidebar--collapsed`
- Items nav : `.nav-item`, `.nav-item--active`, `.nav-item--chat`, `.nav-item--module`
- Badges : `.badge`, `.badge--success`, `.badge--error`, `.badge--running`, `.badge--pending`, `.badge--cost`
- Steps module code : `.step-card`, `.step-card--running`, `.step-card--completed`, `.step-card--error`, `.step-card--waiting`
- Diff viewer : `.diff-viewer`, `.diff-line-add`, `.diff-line-remove`, `.diff-line-header`

---

## 7. API REFERENCE COMPLÈTE

### Objet API (dans api.js)
```js
API.getProjects()
API.getProject(id)
API.createProject(data)           // {name, path, type, local_path?, instructions?}
API.updateProject(id, data)       // {local_path?, instructions?} — body JSON
API.deleteProject(id)
API.getProjectSessions(id)        // retourne sessions avec total_cost_usd
API.getActiveSession(id)

API.startPipeline(data)           // {project_id, workflow_type, initial_input}
API.getPipeline(sessionId)        // état complet + steps
API.nextStep(sessionId)
API.validateStep(sessionId, stepId, data)  // {approved: bool, feedback: str}
API.retryStep(sessionId, stepId)
API.abortPipeline(sessionId)
API.getPipelineCosts(sessionId)
API.getLogs(params)               // {lines?, project_id?}

API.getConfig()
API.saveConfig(data)
API.testConnection(data)          // {provider: "openrouter"|"anthropic"|"google"}
API.getAvailableModels()

API.listProjectFiles(projectId)
API.readFile(projectId, filepath)
API.diffFile(projectId, filepath, new_content)
API.applyFiles(projectId, changes)
API.listLocalFiles(projectId)

API.createConversation(data)      // {project_id?, title?, folder_path?}
API.getConversations(projectId?)
API.getConversation(id)
API.sendMessage(conversationId, content)
API.updateConversationFolder(id, folder_path)
API.deleteConversation(id)
```

### Workflow types disponibles pour startPipeline
`session_start` | `session_end` | `bug_simple` | `mission_complexe` | `nouveau_projet` | `projet_existant`

---

## 8. MODÈLE DE DONNÉES PROJET (après Mission 01)

```json
{
  "id": 3,
  "name": "Jarvis-2.0",
  "path": "C:\\DEV\\PROJETS\\intelligence_artificielle\\Jarvis-2.0",
  "type": "dev",
  "local_path": "C:\\DEV\\PROJETS\\intelligence_artificielle\\Jarvis-2.0",
  "instructions": "Interface d'orchestration IA locale. Backend FastAPI stable...",
  "has_projet_contexte": true,
  "created_at": "2026-04-10 09:00:00",
  "active_session": {
    "id": 17,
    "workflow_type": "session_start",
    "status": "RUNNING",
    "current_step_index": 2
  }
}
```

---

## 9. NAVIGATION URL

```
http://localhost:8000/app/index.html
http://localhost:8000/app/project.html?id=3
http://localhost:8000/app/chat.html?id=42
http://localhost:8000/app/chat.html?id=42&project_id=3
http://localhost:8000/app/module-code.html?session=17
http://localhost:8000/app/module-code.html?session=17&project_id=3
http://localhost:8000/app/settings.html
```

---

## 10. ORDRE DES MISSIONS

| # | Mission | Dépend de |
|---|---|---|
| 01 | Backend : champ instructions projet | — |
| 02 | Fondation : CSS + api.js + shared.js + sidebar.js + ui.js + shells HTML | — |
| 03 | Dashboard (index.html) | 02 |
| 04 | Chat (chat.html) | 02 |
| 05 | Vue Projet (project.html) | 01 + 02 |
| 06 | Module Code (module-code.html) | 02 |
| 07 | Explorateur droit (explorer.js) | 02 |
| 08 | Paramètres (settings.html) | 02 |
