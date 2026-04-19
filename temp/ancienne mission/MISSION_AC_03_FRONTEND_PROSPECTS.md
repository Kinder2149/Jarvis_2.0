# MISSION AC_03 — Frontend Vue Prospects (Atelier Connecté)

## Objectif
Créer la page `frontend/atelier.html` avec la vue Kanban des prospects, ajouter les routes API atelier dans `api.js`, ajouter les classes CSS kanban dans `style.css`, et modifier `sidebar.js` pour y afficher un lien fixe "Atelier Connecté".

Cette mission couvre uniquement la **vue Prospects** (kanban + modal création). La vue Pipeline sera ajoutée en AC_04.

---

## 1. Modifications `frontend/assets/js/api.js`

Ajouter les méthodes suivantes à l'objet `window.API` (après la dernière méthode existante, avant la fermeture `}`):

```js
  // Atelier
  getProspects: () => _get('/atelier/prospects'),
  createProspect: (data) => _post('/atelier/prospects', data),
  getProspect: (id) => _get(`/atelier/prospects/${id}`),
  patchProspect: (id, data) => _patch(`/atelier/prospects/${id}`, data),
  deleteProspect: (id) => _del(`/atelier/prospects/${id}`),
  startAtelierPipeline: (prospectId) => _post(`/atelier/prospects/${prospectId}/start`, {}),
  listProspectFiles: (prospectId) => _get(`/atelier/prospects/${prospectId}/files`),
  exportProspectZip: (prospectId) => `${BASE_URL}/api/atelier/prospects/${prospectId}/export`,
```

---

## 2. Nouveau fichier `frontend/atelier.html`

Créer ce fichier (structure identique à `module-code.html`, même layout sidebar + main) :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JARVIS — Atelier Connecté</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <div id="app-layout">
    <aside id="sidebar"></aside>
    <main id="main-content">

      <!-- VUE PROSPECTS : kanban -->
      <div id="view-prospects">
        <div class="atelier-header">
          <div>
            <h1 class="atelier-title">Atelier Connecté</h1>
            <p class="text-muted">Gestion des prospects restauration</p>
          </div>
          <button id="btn-new-prospect" class="btn-primary">+ Nouveau prospect</button>
        </div>

        <!-- Kanban board -->
        <div class="kanban-board" id="kanban-board">
          <!-- colonnes rendues par JS -->
        </div>
      </div>

      <!-- VUE PIPELINE : rendu par AC_04 -->
      <div id="view-pipeline" style="display:none">
        <div class="atelier-header">
          <div>
            <h2 id="pipeline-prospect-name" class="atelier-title">...</h2>
            <p class="text-muted" id="pipeline-prospect-meta"></p>
          </div>
          <div style="display:flex;gap:0.5rem;align-items:center">
            <button id="btn-back-kanban" class="btn-secondary">← Kanban</button>
            <button id="btn-pipeline-abort" class="btn-danger" style="display:none">⛔ Abandonner</button>
          </div>
        </div>

        <!-- Steps list -->
        <div class="mc-steps" id="pipeline-steps-list"></div>

        <!-- Zone action courante -->
        <div id="pipeline-action-zone" style="display:none" class="mc-action-zone card"></div>
      </div>

    </main>
  </div>

  <div id="modal-overlay" class="modal-overlay" style="display:none">
    <div class="modal-container" id="modal-container"></div>
  </div>
  <div id="toast-container"></div>

  <script src="assets/js/api.js"></script>
  <script src="assets/js/shared.js"></script>
  <script src="assets/js/sidebar.js"></script>
  <script src="assets/js/ui.js"></script>
  <script src="assets/js/atelier.js"></script>
</body>
</html>
```

---

## 3. Nouveau fichier `frontend/assets/js/atelier.js`

Créer ce fichier avec la logique Vue Prospects complète :

```js
(function () {
  // ── État ──────────────────────────────────────────────────────
  let currentProspectId = null;
  let currentSessionId = null;
  let pollInterval = null;

  // Colonnes kanban (ordre affiché)
  const KANBAN_COLS = [
    { key: 'identifie',   label: 'Identifié',   color: '#64748b' },
    { key: 'en_analyse',  label: 'En analyse',  color: '#6366f1' },
    { key: 'demo_ok',     label: 'Démo OK',     color: '#f59e0b' },
    { key: 'contacte',    label: 'Contacté',    color: '#3b82f6' },
    { key: 'relance',     label: 'Relancé',     color: '#f97316' },
    { key: 'conclu',      label: 'Conclu',      color: '#22c55e' },
  ];

  // ── Init ─────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', async () => {
    const prospectId = window.getURLParam('prospect_id');
    if (prospectId) {
      currentProspectId = parseInt(prospectId);
      await showPipelineView(currentProspectId);
    } else {
      await showProspectsView();
    }

    document.getElementById('btn-new-prospect')?.addEventListener('click', handleNewProspect);
    document.getElementById('btn-back-kanban')?.addEventListener('click', () => {
      stopPolling();
      window.location.href = 'atelier.html';
    });
  });

  // ── Vue Prospects ─────────────────────────────────────────────
  async function showProspectsView() {
    document.getElementById('view-prospects').style.display = '';
    document.getElementById('view-pipeline').style.display = 'none';
    await loadKanban();
  }

  async function loadKanban() {
    try {
      const prospects = await window.API.getProspects();
      renderKanban(prospects);
    } catch (e) {
      document.getElementById('kanban-board').innerHTML =
        '<p style="color:var(--danger);padding:2rem">Erreur chargement prospects</p>';
    }
  }

  function renderKanban(prospects) {
    const board = document.getElementById('kanban-board');

    // Regrouper par statut
    const byStatus = {};
    KANBAN_COLS.forEach(col => { byStatus[col.key] = []; });
    prospects.forEach(p => {
      const key = p.statut || 'identifie';
      if (!byStatus[key]) byStatus[key] = [];
      byStatus[key].push(p);
    });

    board.innerHTML = KANBAN_COLS.map(col => `
      <div class="kanban-col">
        <div class="kanban-col-header" style="border-top:3px solid ${col.color}">
          <span class="kanban-col-title">${col.label}</span>
          <span class="kanban-col-count">${byStatus[col.key].length}</span>
        </div>
        <div class="kanban-col-body" data-status="${col.key}">
          ${byStatus[col.key].map(p => renderProspectCard(p)).join('')}
          ${byStatus[col.key].length === 0 ? '<div class="kanban-empty">—</div>' : ''}
        </div>
      </div>
    `).join('');

    // Attacher les clics sur les cartes
    board.querySelectorAll('.prospect-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = parseInt(card.dataset.id);
        window.location.href = `atelier.html?prospect_id=${id}`;
      });
    });

    // Boutons suppression
    board.querySelectorAll('.btn-prospect-delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = parseInt(btn.dataset.id);
        if (!confirm('Supprimer ce prospect ?')) return;
        try {
          await window.API.deleteProspect(id);
          await loadKanban();
        } catch (err) {
          window.showToast && window.showToast(err.message, 'error');
        }
      });
    });
  }

  function renderProspectCard(prospect) {
    const scoreBadge = prospect.score
      ? `<span class="score-badge">${prospect.score}</span>`
      : '';
    const url = prospect.url
      ? `<span class="prospect-url text-muted">${prospect.url}</span>`
      : '';
    const hasPipeline = prospect.session_id ? '⚙️ ' : '';
    return `
      <div class="prospect-card" data-id="${prospect.id}">
        <div class="prospect-card-header">
          <span class="prospect-name">${hasPipeline}${prospect.nom}</span>
          ${scoreBadge}
        </div>
        ${url}
        <div class="prospect-card-footer">
          <span class="text-muted prospect-date">${window.formatDate ? window.formatDate(prospect.updated_at) : ''}</span>
          <button class="btn-icon btn-prospect-delete" data-id="${prospect.id}" title="Supprimer">🗑</button>
        </div>
      </div>
    `;
  }

  // ── Modal Nouveau Prospect ────────────────────────────────────
  function handleNewProspect() {
    const bodyHTML = `
      <div style="margin-bottom:1rem">
        <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Nom du restaurant *</label>
        <input type="text" id="modal-prospect-nom" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="Le Bistrot du Coin">
      </div>
      <div style="margin-bottom:1rem">
        <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Site web (optionnel)</label>
        <input type="url" id="modal-prospect-url" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="https://...">
      </div>
    `;

    window.showModal('Nouveau prospect', bodyHTML, [
      { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
      { label: 'Créer', type: 'primary', onClick: async () => {
        const nom = document.getElementById('modal-prospect-nom').value.trim();
        const url = document.getElementById('modal-prospect-url').value.trim() || null;
        if (!nom) { window.showToast && window.showToast('Le nom est requis', 'error'); return; }
        try {
          await window.API.createProspect({ nom, url, categorie: 'restauration' });
          window.closeModal();
          window.showToast && window.showToast(`Prospect "${nom}" créé`);
          await loadKanban();
        } catch (err) {
          window.showToast && window.showToast(err.message, 'error');
        }
      }}
    ]);
  }

  // ── Vue Pipeline ─────────────────────────────────────────────
  async function showPipelineView(prospectId) {
    document.getElementById('view-prospects').style.display = 'none';
    document.getElementById('view-pipeline').style.display = '';

    try {
      const { prospect, session } = await window.API.getProspect(prospectId);
      document.getElementById('pipeline-prospect-name').textContent = prospect.nom;
      document.getElementById('pipeline-prospect-meta').textContent =
        prospect.url || prospect.categorie || '';

      if (!session) {
        renderNoSession(prospectId);
        return;
      }

      currentSessionId = session.id;
      renderPipeline(session);

      const ACTIVE = ['CREATED', 'RUNNING', 'WAITING', 'PENDING', 'WAITING_VALIDATION'];
      if (ACTIVE.includes(session.status)) startPolling();

    } catch (e) {
      document.getElementById('pipeline-steps-list').innerHTML =
        `<p style="color:var(--danger);padding:2rem">Erreur: ${e.message}</p>`;
    }
  }

  function renderNoSession(prospectId) {
    document.getElementById('pipeline-steps-list').innerHTML = `
      <div style="text-align:center;padding:3rem;color:var(--text-muted)">
        <p style="margin-bottom:1.5rem">Aucun pipeline lancé pour ce prospect.</p>
        <button id="btn-start-pipeline" class="btn-primary">Lancer l'analyse</button>
      </div>
    `;
    document.getElementById('btn-start-pipeline')?.addEventListener('click', async () => {
      try {
        const result = await window.API.startAtelierPipeline(prospectId);
        currentSessionId = result.session_id;
        await showPipelineView(prospectId);
      } catch (err) {
        window.showToast && window.showToast(err.message, 'error');
      }
    });
  }

  function renderPipeline(session) {
    renderPipelineSteps(session);
    renderPipelineActionZone(session);

    const btnAbort = document.getElementById('btn-pipeline-abort');
    const TERMINAL = ['COMPLETED', 'ABORTED', 'FAILED'];
    if (btnAbort) {
      btnAbort.style.display = TERMINAL.includes(session.status) ? 'none' : 'block';
      btnAbort.onclick = handlePipelineAbort;
    }
  }

  function renderPipelineSteps(session) {
    const container = document.getElementById('pipeline-steps-list');
    if (!session.steps?.length) {
      container.innerHTML = '<p style="color:var(--text-muted);padding:2rem">Aucun step</p>';
      return;
    }
    const sorted = [...session.steps].sort((a, b) => a.step_index - b.step_index);
    container.innerHTML = sorted.map(step => renderAtlierStepCard(step)).join('');
  }

  function renderAtlierStepCard(step) {
    const statusClass = getStepStatusClass(step.status);
    const indicator = getStepIndicator(step.status);
    let outputPreview = '';
    if (step.status === 'COMPLETED' && step.output_data) {
      const preview = step.output_data.substring(0, 100);
      outputPreview = `<div class="step-output">${preview}${step.output_data.length > 100 ? '...' : ''}</div>`;
    }
    return `
      <div class="step-card ${statusClass}" data-step-id="${step.id}">
        <div class="step-card-left">
          <div class="step-indicator">${indicator}</div>
          <div class="step-index">${step.step_index + 1}</div>
        </div>
        <div class="step-card-body">
          <div class="step-name">${step.step_display_name || step.step_name}</div>
          <div class="step-meta"><span class="text-muted">${step.model_type || ''}</span></div>
          ${outputPreview}
        </div>
      </div>
    `;
  }

  function getStepStatusClass(status) {
    return { PENDING: 'step-card--pending', RUNNING: 'step-card--running', COMPLETED: 'step-card--completed', FAILED: 'step-card--error', WAITING_VALIDATION: 'step-card--waiting' }[status] || '';
  }

  function getStepIndicator(status) {
    return { PENDING: '<span style="color:var(--text-muted)">○</span>', RUNNING: '<div class="spinner"></div>', COMPLETED: '✅', FAILED: '❌', WAITING_VALIDATION: '⏸️' }[status] || '○';
  }

  function renderPipelineActionZone(session) {
    const zone = document.getElementById('pipeline-action-zone');
    const waiting = session.steps?.find(s => s.status === 'WAITING_VALIDATION');
    if (!waiting) { zone.style.display = 'none'; return; }
    zone.style.display = 'block';

    // Dispatcher selon output_type
    switch (waiting.output_type) {
      case 'form':       zone.innerHTML = renderSaisieForm(waiting); attachSaisieHandlers(waiting); break;
      case 'checkpoint': zone.innerHTML = renderCheckpointZone(waiting); attachCheckpointHandlers(waiting); break;
      default:           zone.innerHTML = renderGenericWaiting(waiting); attachGenericHandlers(waiting);
    }
  }

  // ── Renderers de zones d'action (détail en AC_04) ─────────────
  // Placeholder minimal pour cette mission — AC_04 remplace ces fonctions

  function renderSaisieForm(step) {
    return `<div class="mc-action-header"><h3>⏸️ Saisie prospect</h3><p class="text-muted">Complétez les informations avant de lancer l'analyse.</p></div>
    <div id="saisie-form-body"><p style="color:var(--text-muted)">Formulaire en cours de chargement...</p></div>`;
  }

  function attachSaisieHandlers(step) { /* AC_04 */ }

  function renderCheckpointZone(step) {
    const md = window.renderMarkdown || ((t) => `<pre>${t}</pre>`);
    return `<div class="mc-action-header"><h3>⏸️ Validation proposition</h3></div>
    <div class="mc-output-preview">${md(step.output_data || '')}</div>
    <div class="mc-validation-actions" style="margin-top:1rem">
      <button id="btn-checkpoint-approve" class="btn-primary">✅ Valider — Lancer la génération</button>
      <button id="btn-checkpoint-reject" class="btn-danger">❌ Abandonner</button>
    </div>`;
  }

  function attachCheckpointHandlers(step) { /* AC_04 */ }

  function renderGenericWaiting(step) {
    return `<div class="mc-action-header"><h3>⏸️ ${step.step_display_name} — En attente</h3></div>`;
  }

  function attachGenericHandlers(step) { /* AC_04 */ }

  // ── Polling ──────────────────────────────────────────────────
  function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(async () => {
      try {
        const { session } = await window.API.getProspect(currentProspectId);
        if (!session) { stopPolling(); return; }
        renderPipeline(session);
        if (['COMPLETED', 'ABORTED', 'FAILED'].includes(session.status)) stopPolling();
      } catch (e) { console.error('Polling error:', e); }
    }, 2500);
  }

  function stopPolling() {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
  }

  // ── Abandon pipeline ─────────────────────────────────────────
  async function handlePipelineAbort() {
    if (!confirm('Abandonner ce pipeline ?')) return;
    try {
      await window.API.abortPipeline(currentSessionId);
      window.showToast && window.showToast('Pipeline abandonné');
      await showPipelineView(currentProspectId);
    } catch (err) {
      window.showToast && window.showToast(err.message, 'error');
    }
  }

  window.addEventListener('beforeunload', stopPolling);
})();
```

---

## 4. Modifications `frontend/assets/style.css`

Ajouter à la **fin du fichier** les classes CSS suivantes :

```css
/* ── Atelier Connecté ────────────────────────────────────── */

.atelier-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.atelier-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* Kanban board */
.kanban-board {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 1rem;
  align-items: flex-start;
}

.kanban-col {
  min-width: 220px;
  max-width: 240px;
  flex-shrink: 0;
  background: var(--bg-card);
  border-radius: 10px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.kanban-col-header {
  padding: 0.75rem 1rem 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 10px 10px 0 0;
}

.kanban-col-title {
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-primary);
}

.kanban-col-count {
  background: var(--bg-input);
  color: var(--text-muted);
  border-radius: 999px;
  padding: 1px 8px;
  font-size: 0.75rem;
}

.kanban-col-body {
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 80px;
}

.kanban-empty {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.85rem;
  padding: 1rem 0;
}

/* Prospect card */
.prospect-card {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.1s;
}

.prospect-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.prospect-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.prospect-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.prospect-url {
  font-size: 0.75rem;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
  margin-bottom: 0.4rem;
}

.prospect-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
}

.prospect-date {
  font-size: 0.7rem;
}

.btn-prospect-delete {
  opacity: 0;
  transition: opacity 0.15s;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
}

.prospect-card:hover .btn-prospect-delete {
  opacity: 1;
}

/* Score badge */
.score-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
}

/* Sidebar Atelier section */
.nav-section--atelier {
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5rem;
  margin-bottom: 0.5rem;
}

.nav-atelier-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 500;
  border-radius: 6px;
  transition: background 0.15s;
}

.nav-atelier-link:hover,
.nav-atelier-link.nav-item--active {
  background: var(--bg-input);
  color: var(--accent);
}

.atelier-active-badge {
  margin-left: auto;
  background: var(--accent);
  color: #fff;
  border-radius: 999px;
  padding: 1px 7px;
  font-size: 0.7rem;
  font-weight: 700;
}
```

---

## 5. Modifications `frontend/assets/js/sidebar.js`

### 5a. Ajouter `getAtelierActiveCount()` à la fin du fichier (avant la dernière accolade du fichier) :

Ajouter à la toute fin du fichier (après la fonction `getStatusBadge`) :

```js
async function getAtelierActiveCount() {
  try {
    const prospects = await window.API.getProspects();
    return prospects.filter(p => p.statut === 'en_analyse').length;
  } catch (e) {
    return 0;
  }
}
```

### 5b. Dans `window.initSidebar`, modifier le chargement initial pour fetch les prospects aussi :

Remplacer :
```js
    const [projects, conversations] = await Promise.all([
      window.API.getProjects(),
      window.API.getConversations()
    ]);
```

Par :
```js
    const [projects, conversations, atelierCount] = await Promise.all([
      window.API.getProjects(),
      window.API.getConversations(),
      getAtelierActiveCount()
    ]);
```

### 5c. Dans `renderSidebar`, ajouter le paramètre `atelierCount` et injecter la section Atelier :

Remplacer la signature :
```js
function renderSidebar(projects, conversations, sessionsMap) {
```

Par :
```js
function renderSidebar(projects, conversations, sessionsMap, atelierCount = 0) {
```

Et après `renderSidebar(projects, conversations, sessionsMap);` dans `initSidebar` :
```js
    renderSidebar(projects, conversations, sessionsMap, atelierCount);
```

### 5d. Dans `renderSidebar`, ajouter la section Atelier **avant** la section PROJETS :

Localiser dans `renderSidebar` la ligne :
```js
  if (projects.length > 0) {
    html += '<div class="nav-section"><div class="nav-section-title">PROJETS</div>';
```

Juste **avant** cette ligne, insérer :

```js
  const isAtelierActive = currentPath.includes('atelier.html');
  const atelierBadge = atelierCount > 0
    ? `<span class="atelier-active-badge sidebar-text">${atelierCount}</span>`
    : '';
  html += `
    <div class="nav-section nav-section--atelier">
      <a href="atelier.html" class="nav-atelier-link ${isAtelierActive ? 'nav-item--active' : ''}">
        <span class="sidebar-text">🏭 Atelier Connecté</span>
        <span class="sidebar-collapsed-text" style="display:none">🏭</span>
        ${atelierBadge}
      </a>
    </div>
  `;
```

---

## 6. Ajout du bouton Atelier dans `sidebar.js`

Dans la section `sidebar-actions` HTML générée par `renderSidebar`, après le bouton `btn-new-module`, ajouter un bouton "Atelier" :

Localiser :
```js
      <button id="btn-new-module" class="btn-sidebar-action">
        <span class="sidebar-text">⚙️ Module Code</span>
        <span class="sidebar-collapsed-text" style="display:none">⚙️</span>
      </button>
```

Ajouter après :
```js
      <a href="atelier.html" id="btn-atelier" class="btn-sidebar-action" style="text-decoration:none;display:flex;align-items:center;gap:0.5rem">
        <span class="sidebar-text">🏭 Atelier</span>
        <span class="sidebar-collapsed-text" style="display:none">🏭</span>
      </a>
```

---

## Vérification finale

Après implémentation, s'assurer que :
1. `GET http://localhost:8000/api/atelier/prospects` répond 200 (serveur déjà lancé)
2. `atelier.html` s'ouvre sans erreur console
3. Le kanban s'affiche avec les colonnes même si vide
4. Le bouton "Atelier Connecté" est visible dans la sidebar sur toutes les pages
5. Créer un prospect via le modal → la carte apparaît dans la colonne "Identifié"
6. Cliquer sur une carte → redirige vers `atelier.html?prospect_id=X`

---

## Ne pas faire dans cette mission
- Ne pas implémenter les renderers de formulaire SAISIE (AC_04)
- Ne pas implémenter le renderer checkpoint complet (AC_04)
- Ne pas implémenter l'affichage des fichiers démo / ZIP export (AC_04)
