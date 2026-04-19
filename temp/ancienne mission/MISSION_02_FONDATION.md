# MISSION 02 — Fondation : CSS + Modules JS Partagés + Shells HTML

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2 — lire entièrement)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Fondation Frontend V2 — Layout + CSS + Modules partagés

OBJECTIF :
Poser les bases complètes du frontend V2 :
- Le CSS global avec le layout 3 panneaux
- Les 4 modules JS partagés (api.js, shared.js, sidebar.js, ui.js)
- Le shell HTML (structure de base) des 5 pages

À la fin de cette mission, naviguer entre les pages doit fonctionner,
la sidebar doit s'afficher et se replier, le layout doit être correct.
Le contenu des pages (dashboard, chat, etc.) sera ajouté dans les missions suivantes.

PÉRIMÈTRE :
Fichiers à réécrire entièrement :
- frontend/assets/style.css
- frontend/index.html
- frontend/project.html
- frontend/chat.html
- frontend/settings.html

Fichiers à créer :
- frontend/module-code.html
- frontend/assets/js/api.js
- frontend/assets/js/shared.js
- frontend/assets/js/sidebar.js
- frontend/assets/js/ui.js

Fichier à supprimer (remplacé par les nouveaux modules) :
- frontend/assets/app.js   ← NE PAS supprimer encore, sera supprimé en Mission 08

---

INSTRUCTIONS DÉTAILLÉES :

### 1. frontend/assets/style.css — CSS Global

Réécrire entièrement. Conserver les variables existantes et ajouter les nouvelles.

**Variables CSS (section :root) :**
```css
:root {
  /* Existantes */
  --bg-primary: #0f1117;
  --bg-card: #1a1d2e;
  --bg-input: #252840;
  --accent: #6366f1;
  --accent-hover: #4f46e5;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --text-primary: #e2e8f0;
  --text-muted: #64748b;
  --border: #2d3148;
  --diff-add-bg: #0d2818;
  --diff-add-text: #22c55e;
  --diff-remove-bg: #2d1010;
  --diff-remove-text: #ef4444;
  /* Nouvelles */
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 52px;
  --explorer-width: 280px;
}
```

**Layout 3 panneaux :**
```
#app-layout : display flex, height 100vh, overflow hidden
#sidebar : width var(--sidebar-width), flex-shrink 0, transition width 0.2s
#main-content : flex 1, overflow-y auto, padding 1.5rem
#explorer : width var(--explorer-width), flex-shrink 0, border-left 1px solid var(--border)
```

État collapsed sidebar :
```
#sidebar.sidebar--collapsed : width var(--sidebar-collapsed-width)
#sidebar.sidebar--collapsed .sidebar-text : display none
```

État explorer caché :
```
#explorer.explorer--hidden : display none
```

**Sidebar gauche — structure interne :**
```
.sidebar-header : logo JARVIS + bouton collapse
.sidebar-actions : boutons "Nouveau Chat" et "Nouveau Module Code"
.sidebar-search : input recherche
.sidebar-nav : liste navigation (scroll)
.sidebar-footer : coût du jour + lien paramètres
```

**Items navigation :**
```
.nav-section : groupe (PROJETS, LIBRES)
.nav-section-title : label section (majuscules, text-muted, font-size 0.7rem)
.nav-project : conteneur projet repliable
.nav-project-header : en-tête projet (nom + badge actif)
.nav-project-items : liste conversations du projet
.nav-item : item cliquable (chat ou module code)
.nav-item--active : item de la page courante (accent color, bg légèrement éclairci)
.nav-item--chat : préfixe 💬
.nav-item--module : préfixe ⚙️
```

**Badges et états :**
```
.badge : display inline-flex, align-items center, border-radius 9999px, font-size 0.7rem, padding 2px 8px
.badge--success : background rgba(34,197,94,0.15), color var(--success)
.badge--error : background rgba(239,68,68,0.15), color var(--danger)
.badge--running : background rgba(99,102,241,0.15), color var(--accent), animation pulse 1.5s infinite
.badge--pending : background rgba(100,116,139,0.15), color var(--text-muted)
.badge--waiting : background rgba(245,158,11,0.15), color var(--warning)
.badge--cost : background var(--bg-input), color var(--text-muted)
.active-dot : petit cercle animé (pulse) indiquant pipeline actif
```

**Boutons :**
```
.btn-primary : background var(--accent), color white, border-radius 6px, padding 8px 16px
.btn-secondary : background var(--bg-input), color var(--text-primary), border 1px solid var(--border)
.btn-danger : background var(--danger), color white
.btn-icon : background transparent, border none, color var(--text-muted), cursor pointer, hover color var(--text-primary)
.btn-sidebar-action : width 100%, text-align left, background var(--bg-input), border 1px solid var(--border), border-radius 6px, padding 8px 12px, color var(--text-primary), hover background var(--border)
```

**Cards :**
```
.card : background var(--bg-card), border 1px solid var(--border), border-radius 8px, padding 1rem
.card--interactive : hover border-color var(--accent), cursor pointer, transition 0.15s
```

**Toast (notifications) :**
```
#toast-container : position fixed, bottom 1.5rem, right 1.5rem, z-index 1000, display flex, flex-direction column, gap 8px
.toast : background var(--bg-card), border 1px solid var(--border), border-radius 8px, padding 12px 16px, max-width 360px, animation slideIn 0.2s ease
.toast--success : border-left 3px solid var(--success)
.toast--error : border-left 3px solid var(--danger)
.toast--warning : border-left 3px solid var(--warning)
```

**Modal :**
```
.modal-overlay : position fixed, inset 0, background rgba(0,0,0,0.7), z-index 500, display flex, align-items center, justify-content center
.modal : background var(--bg-card), border 1px solid var(--border), border-radius 12px, padding 1.5rem, min-width 400px, max-width 600px
.modal-header : flex, justify-content space-between, margin-bottom 1rem
.modal-actions : flex, gap 8px, justify-content flex-end, margin-top 1.5rem
```

**Spinner :**
```
.spinner : width 16px, height 16px, border 2px solid var(--border), border-top-color var(--accent), border-radius 50%, animation spin 0.8s linear infinite
@keyframes spin { to { transform: rotate(360deg) } }
@keyframes pulse { 0%,100% { opacity 1 } 50% { opacity 0.5 } }
```

**Diff viewer :**
```
.diff-viewer : background var(--bg-input), border-radius 6px, overflow-x auto, font-family monospace, font-size 0.85rem
.diff-line-add : background var(--diff-add-bg), color var(--diff-add-text)
.diff-line-remove : background var(--diff-remove-bg), color var(--diff-remove-text)
.diff-line-header : color var(--text-muted)
```

**Explorateur droit :**
```
.explorer-header : padding 12px, border-bottom 1px solid var(--border), flex justify-between
.explorer-tree : overflow-y auto, flex 1
.tree-folder : cursor pointer, user-select none
.tree-folder-name : flex, align-items center, gap 6px, padding 3px 8px, hover background var(--bg-input), border-radius 4px
.tree-file : padding 3px 8px 3px 24px, cursor pointer, hover background var(--bg-input), border-radius 4px, font-size 0.85rem
.tree-file--active : background var(--bg-input), color var(--accent)
.explorer-preview : border-top 1px solid var(--border), max-height 40%, overflow-y auto, padding 12px, font-family monospace, font-size 0.8rem, color var(--text-muted)
```

---

### 2. frontend/assets/js/api.js

Créer ce fichier. Il expose un objet global `window.API`.

**Structure :**
```js
const BASE_URL = window.location.origin;

async function _request(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE_URL}/api${path}`, opts);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const d = await res.json(); if (d.detail) msg = d.detail; } catch(e) {}
    throw new Error(msg);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

const _get = (path) => _request('GET', path);
const _post = (path, body) => _request('POST', path, body);
const _patch = (path, body) => _request('PATCH', path, body);
const _del = (path) => _request('DELETE', path);

window.API = {
  // Projects
  getProjects: () => _get('/projects/'),
  getProject: (id) => _get(`/projects/${id}`),
  createProject: (data) => _post('/projects/', data),
  updateProject: (id, data) => _patch(`/projects/${id}`, data),
  deleteProject: (id) => _del(`/projects/${id}`),
  getProjectSessions: (id) => _get(`/projects/${id}/sessions`),
  getActiveSession: (id) => _get(`/projects/${id}/active-session`),

  // Pipelines / Module Code
  startPipeline: (data) => _post('/pipelines/start', data),
  getPipeline: (sessionId) => _get(`/pipelines/${sessionId}`),
  nextStep: (sessionId) => _post(`/pipelines/${sessionId}/next`),
  validateStep: (sessionId, stepId, data) => _post(`/pipelines/${sessionId}/validate/${stepId}`, data),
  retryStep: (sessionId, stepId) => _post(`/pipelines/${sessionId}/retry/${stepId}`),
  abortPipeline: (sessionId) => _post(`/pipelines/${sessionId}/abort`),
  getPipelineCosts: (sessionId) => _get(`/pipelines/${sessionId}/costs`),
  getLogs: (params = {}) => _get(`/pipelines/logs?${new URLSearchParams(params)}`),

  // Config
  getConfig: () => _get('/config/'),
  saveConfig: (data) => _post('/config/', data),
  testConnection: (data) => _post('/config/test', data),
  getAvailableModels: () => _get('/config/models/available'),

  // Files
  listProjectFiles: (projectId) => _get(`/files/${projectId}/list`),
  readFile: (projectId, filepath) => _post(`/files/${projectId}/read`, { filepath }),
  diffFile: (projectId, filepath, new_content) => _post(`/files/${projectId}/diff`, { filepath, new_content }),
  applyFiles: (projectId, changes) => _post(`/files/${projectId}/apply`, { changes }),
  listLocalFiles: (projectId) => _get(`/files/${projectId}/local-list`),

  // Chat
  createConversation: (data) => _post('/chat/conversations', data),
  getConversations: (projectId = null) => _get(`/chat/conversations${projectId ? `?project_id=${projectId}` : ''}`),
  getConversation: (id) => _get(`/chat/conversations/${id}`),
  sendMessage: (conversationId, content) => _post(`/chat/conversations/${conversationId}/messages`, { content }),
  updateConversationFolder: (id, folder_path) => _patch(`/chat/conversations/${id}/folder`, { folder_path }),
  deleteConversation: (id) => _del(`/chat/conversations/${id}`),
};
```

---

### 3. frontend/assets/js/shared.js

```js
// Event bus pour communication inter-modules
window.EventBus = {
  emit(name, data) { document.dispatchEvent(new CustomEvent(`jarvis:${name}`, { detail: data })); },
  on(name, cb) { document.addEventListener(`jarvis:${name}`, e => cb(e.detail)); }
};

// Lecture paramètres URL
window.getURLParam = (name) => new URLSearchParams(window.location.search).get(name);

// Formatage date : "Aujourd'hui 14h32" / "Hier" / "12 janv."
window.formatDate = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  const itemDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const hhmm = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  if (itemDay.getTime() === today.getTime()) return `Aujourd'hui ${hhmm}`;
  if (itemDay.getTime() === yesterday.getTime()) return 'Hier';
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
};

// Formatage coût
window.formatCost = (usd) => usd != null ? `$${Number(usd).toFixed(3)}` : '';

// Markdown minimal (gras, code inline, blocs code)
window.renderMarkdown = (text) => {
  if (!text) return '';
  return text
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>');
};

// Diff renderer (migré depuis app.js)
window.renderDiff = (diffText) => {
  if (!diffText) return '';
  const lines = diffText.split('\n');
  let html = '<div class="diff-viewer">';
  lines.forEach(line => {
    const escaped = line.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
      html += `<div class="diff-line-header">${escaped}</div>`;
    } else if (line.startsWith('+')) {
      html += `<div class="diff-line-add">${escaped}</div>`;
    } else if (line.startsWith('-')) {
      html += `<div class="diff-line-remove">${escaped}</div>`;
    } else {
      html += `<div style="color:var(--text-muted)">${escaped}</div>`;
    }
  });
  html += '</div>';
  return html;
};

// Init layout — appelé au DOMContentLoaded
window.initLayout = async () => {
  // Sidebar
  if (typeof window.initSidebar === 'function') await window.initSidebar();
  // Explorer — initialisé par chaque page si nécessaire
  // Stocker project_id courant
  const pid = window.getURLParam('project_id') || window.getURLParam('id');
  if (pid) window.currentProjectId = parseInt(pid);
};

document.addEventListener('DOMContentLoaded', () => window.initLayout());
```

---

### 4. frontend/assets/js/sidebar.js

Ce fichier expose `window.initSidebar()` qui charge les données et rend la sidebar.

**Structure de la sidebar rendue (HTML injecté dans #sidebar) :**
```
.sidebar-header
  .sidebar-logo : "⚡ JARVIS"
  button#btn-sidebar-collapse : "←" (collapsed: "→")
.sidebar-actions
  button#btn-new-chat : "+ Chat"
  button#btn-new-module : "⚡ Module"
.sidebar-search
  input#sidebar-search-input placeholder="Rechercher..."
.sidebar-nav (scrollable)
  [sections générées dynamiquement]
.sidebar-footer
  .sidebar-cost : "💰 $0.000 aujourd'hui"
  a href="settings.html" : "⚙️ Paramètres"
```

**Logique de rendu de la nav :**
1. Charger `API.getProjects()` et `API.getConversations()` en parallèle
2. Pour chaque projet : afficher son nom en header de section avec un `>` repliable
3. Sous chaque projet : ses conversations chat + sessions récentes (les 5 plus récentes)
4. Section "LIBRES" : conversations sans `project_id`
5. Item actif : comparer l'URL courante avec les hrefs des items

**Format items :**
- Chat : `<a class="nav-item nav-item--chat" href="/app/chat.html?id=42&project_id=3">💬 Titre conv</a>`
- Module Code actif (session non terminée) : afficher un `.active-dot` pulse à côté du projet
- Module Code : `<a class="nav-item nav-item--module" href="/app/module-code.html?session=17&project_id=3">⚙️ session_start <span class="badge badge--success">✅</span></a>`

**Bouton Nouveau Chat :**
Ouvrir un mini-modal inline : "Dans quel projet ?" (dropdown projets + option "Sans projet")
→ `API.createConversation({project_id, title: "Nouvelle conversation"})`
→ redirect vers `chat.html?id=X&project_id=Y`

**Bouton Nouveau Module Code :**
Ouvrir un modal : sélection projet + sélection workflow_type (dropdown) + champ initial_input
→ `API.startPipeline({project_id, workflow_type, initial_input})`
→ redirect vers `module-code.html?session=X&project_id=Y`

**Collapse :**
Toggle class `sidebar--collapsed` sur `#sidebar`.
Persister l'état dans `localStorage.setItem('sidebar_collapsed', 'true/false')`.

**Recherche :**
Filtrage en temps réel des items nav par texte saisi dans l'input.

---

### 5. frontend/assets/js/ui.js

**showToast(message, type = 'success') :**
- `type` : 'success' | 'error' | 'warning'
- Crée un `.toast .toast--{type}` dans `#toast-container`
- Auto-remove après 4000ms avec animation fadeOut
- Max 3 toasts simultanés (supprimer le plus ancien si dépassé)

**showModal(title, bodyHTML, actions) :**
- `actions` : array de `{label, type, onClick}` où type = 'primary'|'secondary'|'danger'
- Crée `.modal-overlay > .modal`
- Click sur overlay → ferme
- Retourne une Promise résolue quand une action est cliquée

**closeModal() :**
- Supprime `.modal-overlay` du DOM

**statusBadge(status) :**
Map status → badge HTML :
- 'PENDING' → `.badge--pending` "En attente"
- 'RUNNING' → `.badge--running` "⏳ En cours"
- 'COMPLETED' → `.badge--success` "✅ Terminé"
- 'ERROR' → `.badge--error` "❌ Erreur"
- 'ABORTED' → `.badge--pending` "Abandonné"
- 'WAITING_VALIDATION' → `.badge--waiting` "⏸️ Validation"

**costBadge(usd) :**
`<span class="badge badge--cost">${formatCost(usd)}</span>`

---

### 6. HTML Shell — Les 5 pages

Chaque page doit avoir exactement cette structure (adapter le `<title>` et les scripts) :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JARVIS — [Nom Page]</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <div id="app-layout">
    <aside id="sidebar"></aside>
    <main id="main-content">
      <div id="page-[nom]">
        <!-- Placeholder : "Chargement..." -->
        <p style="color:var(--text-muted);padding:2rem">Chargement...</p>
      </div>
    </main>
    <aside id="explorer" class="explorer--hidden"></aside>
  </div>
  <div id="toast-container"></div>

  <script src="assets/js/api.js"></script>
  <script src="assets/js/shared.js"></script>
  <script src="assets/js/sidebar.js"></script>
  <script src="assets/js/ui.js"></script>
  <!-- scripts spécifiques à la page -->
</body>
</html>
```

Pages à créer/mettre à jour avec ce shell :
- `index.html` (id="page-dashboard", + script dashboard.js)
- `project.html` (id="page-project", + scripts explorer.js, project.js)
- `chat.html` (id="page-chat", + scripts explorer.js, chat.js)
- `module-code.html` (NOUVEAU fichier, id="page-module-code", + script module-code.js)
- `settings.html` (id="page-settings", + script settings.js)

---

TESTS MANUELS (3 étapes) :

1. Ouvrir http://localhost:8000 → vérifier que la page charge sans erreur JS (console F12),
   que la sidebar s'affiche avec les projets existants, les conversations et sections.

2. Cliquer sur "← collapse" sidebar → la sidebar se réduit à des icônes.
   Cliquer à nouveau → elle se réétend. Recharger la page → l'état est mémorisé.

3. Cliquer sur "+ Chat" dans la sidebar → modal de sélection projet s'ouvre.
   Sélectionner un projet → une nouvelle conversation est créée → redirection vers chat.html.
   La sidebar marque bien cet item comme actif.

FIN DE MISSION :
- Serveur démarre sans erreur
- Tests manuels validés
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
