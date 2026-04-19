# MISSION 11 — Corrections UX : Navigation + Modèle Chat + Nettoyage

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Corrections UX — Navigation, Modèle Chat, Sessions, Projet

OBJECTIF :
Corriger 5 problèmes UX identifiés sur l'interface en production :
1. Clic sur projet dans la sidebar ne navigue pas vers la page projet
2. Pas de bouton retour au tableau de bord
3. Pas de sélecteur de modèle IA dans le chat
4. Les sessions "actives" fantômes polluent le dashboard
5. Pas de moyen de créer un nouveau projet depuis l'interface

CONTEXTE IMPORTANT :
- Le backend supporte déjà `model` optionnel dans POST /chat/conversations/{id}/messages
  (champ `model: str | None = None` dans MessageCreate)
- Aucune modification backend n'est nécessaire pour le sélecteur de modèle

PÉRIMÈTRE :
Fichiers à modifier :
- frontend/assets/js/sidebar.js
- frontend/assets/js/api.js
- frontend/assets/js/dashboard.js
- frontend/assets/js/chat.js
- frontend/chat.html
- frontend/assets/style.css  (ajouts CSS uniquement)

---

## FIX 1 — Clic projet sidebar → navigation vers project.html

Fichier : `frontend/assets/js/sidebar.js`

**Problème :** Cliquer sur le projet dans la sidebar déroule/enroule les conversations
mais ne navigue pas vers la page projet. Il faut séparer les deux actions.

**Solution :** Scinder le `.nav-project-header` en deux zones cliquables :
- Clic sur la flèche `▼/▶` → toggle expand/collapse (comportement actuel)
- Clic sur le NOM du projet → navigate vers `project.html?id=X`

**Modification du HTML généré pour chaque projet dans renderSidebar() :**
```js
// AVANT :
html += `
  <div class="nav-project-header" data-project-id="${project.id}">
    <span class="nav-project-toggle">${isExpanded ? '▼' : '▶'}</span>
    <span class="sidebar-text">${project.name}</span>
    ${hasActivePipeline ? '<span class="active-dot"></span>' : ''}
  </div>
`;

// APRÈS :
html += `
  <div class="nav-project-header" data-project-id="${project.id}">
    <span class="nav-project-toggle nav-project-arrow" 
          data-project-id="${project.id}" 
          title="Déplier/Replier">
      ${isExpanded ? '▼' : '▶'}
    </span>
    <a class="nav-project-name sidebar-text" 
       href="project.html?id=${project.id}" 
       title="Ouvrir le projet">
      ${project.name}
    </a>
    ${hasActivePipeline ? '<span class="active-dot"></span>' : ''}
  </div>
`;
```

**Modification des event listeners :**
Remplacer l'écouteur actuel sur `.nav-project-header` par deux écouteurs distincts :

```js
// Flèche toggle : expand/collapse seulement
document.querySelectorAll('.nav-project-arrow').forEach(arrow => {
  arrow.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const projectId = arrow.dataset.projectId;
    const header = arrow.closest('.nav-project-header');
    const items = header.nextElementSibling;
    const isExpanded = items.style.display !== 'none';
    items.style.display = isExpanded ? 'none' : 'block';
    arrow.textContent = isExpanded ? '▶' : '▼';
    localStorage.setItem(`project_${projectId}_expanded`, !isExpanded);
  });
});

// Le lien .nav-project-name est un <a> standard → pas d'écouteur supplémentaire
// Les <a> dans la sidebar doivent avoir class nav-item--active si l'URL courante 
// contient project.html?id=X pour ce projet.
```

**CSS à ajouter pour .nav-project-name :**
```css
.nav-project-name {
  color: var(--text-primary);
  text-decoration: none;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.nav-project-name:hover {
  color: var(--accent);
}
/* Actif si on est sur project.html avec cet id */
.nav-project-name.nav-item--active {
  color: var(--accent);
}
```

Marquer `.nav-project-name` comme actif si `currentPath.includes('project.html') && currentId == project.id`.

---

## FIX 2 — Logo JARVIS → retour tableau de bord

Fichier : `frontend/assets/js/sidebar.js`

**Problème :** Le logo "⚡ JARVIS" n'est pas cliquable. Impossible de revenir au dashboard.

**Solution :** Remplacer le `div` du logo par un lien :

```js
// AVANT :
<div class="sidebar-logo">⚡ <span class="sidebar-text">JARVIS</span></div>

// APRÈS :
<a href="index.html" class="sidebar-logo" title="Tableau de bord">
  ⚡ <span class="sidebar-text">JARVIS</span>
</a>
```

**CSS pour .sidebar-logo en tant que lien :**
```css
a.sidebar-logo {
  text-decoration: none;
  color: var(--text-primary);
  font-weight: 700;
  font-size: 1.1rem;
}
a.sidebar-logo:hover {
  color: var(--accent);
}
```

---

## FIX 3 — Sélecteur de modèle dans le chat

**Contexte :** Le backend accepte déjà `model` dans POST /chat/conversations/{id}/messages.
Il faut juste exposer ce choix dans l'UI.

### 3a. Modifier api.js — sendMessage accepte un model optionnel

```js
// AVANT :
sendMessage: (conversationId, content) => _post(`/chat/conversations/${conversationId}/messages`, { content }),

// APRÈS :
sendMessage: (conversationId, content, model = null) => {
  const body = { content };
  if (model) body.model = model;
  return _post(`/chat/conversations/${conversationId}/messages`, body);
},
```

### 3b. Modifier chat.html — Ajouter le sélecteur dans le header

Dans `.chat-header-right`, ajouter AVANT le bouton 🗑️ :
```html
<div class="chat-model-selector">
  <select id="chat-model-select" title="Modèle IA">
    <option value="">Modèle par défaut</option>
    <!-- Options chargées dynamiquement par chat.js -->
  </select>
</div>
```

### 3c. Modifier chat.js — Charger les modèles et passer le modèle choisi

**Dans la fonction d'initialisation (DOMContentLoaded), après loadConversation() :**
```js
await loadAvailableModels();
```

**Ajouter la fonction loadAvailableModels() :**
```js
async function loadAvailableModels() {
  try {
    const models = await window.API.getAvailableModels();
    const select = document.getElementById('chat-model-select');
    if (!select || !models) return;
    
    // models peut être un objet {routing: [...], code: [...], analysis: [...]}
    // ou une liste plate. Gérer les deux cas.
    let modelList = [];
    if (Array.isArray(models)) {
      modelList = models;
    } else {
      // Fusionner toutes les listes en dédupliquant
      const seen = new Set();
      Object.values(models).forEach(list => {
        if (Array.isArray(list)) {
          list.forEach(m => {
            const id = typeof m === 'string' ? m : m.id || m.model_id;
            if (id && !seen.has(id)) { seen.add(id); modelList.push(id); }
          });
        }
      });
    }
    
    // Charger le modèle mémorisé pour cette conversation
    const savedModel = localStorage.getItem(`chat_model_${conversationId}`) || '';
    
    modelList.forEach(model => {
      const id = typeof model === 'string' ? model : model.id || model.model_id;
      const label = id.split('/').pop(); // "claude-haiku-4-5" depuis "anthropic/claude-haiku-4-5"
      const opt = document.createElement('option');
      opt.value = id;
      opt.textContent = label;
      if (id === savedModel) opt.selected = true;
      select.appendChild(opt);
    });
    
    // Mémoriser le choix par conversation
    select.addEventListener('change', () => {
      localStorage.setItem(`chat_model_${conversationId}`, select.value);
    });
    
  } catch (e) {
    console.warn('Modèles non disponibles:', e);
  }
}
```

**Dans handleSendMessage(), récupérer le modèle sélectionné :**
```js
// AVANT :
const response = await window.API.sendMessage(conversationId, content);

// APRÈS :
const modelSelect = document.getElementById('chat-model-select');
const selectedModel = modelSelect ? modelSelect.value : null;
const response = await window.API.sendMessage(conversationId, content, selectedModel || null);
```

**CSS pour le sélecteur de modèle :**
```css
.chat-model-selector {
  display: flex;
  align-items: center;
}
.chat-model-selector select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 0.8rem;
  padding: 4px 8px;
  cursor: pointer;
  max-width: 180px;
}
.chat-model-selector select:focus {
  border-color: var(--accent);
  outline: none;
  color: var(--text-primary);
}
```

---

## FIX 4 — Sessions fantômes dans le dashboard

Fichier : `frontend/assets/js/dashboard.js`

**Problème :** Le dashboard affiche toutes les sessions non-COMPLETED/ABORTED comme "actives",
même celles créées il y a des jours et bloquées à Step 1 (status CREATED mais jamais progressées).

**Solution en 2 parties :**

### 4a. Filtrer les sessions vraiment actives

Dans `renderActivePipelines()`, ne montrer comme "actif" que les sessions :
- Dont le status est `RUNNING` ou `WAITING_VALIDATION` (vraiment en cours)
- OU dont le status est `CREATED` mais créées il y a moins de 1 heure

Les sessions `CREATED` bloquées depuis des heures → les afficher dans une section "Bloquées" séparée.

```js
function renderActivePipelines() {
  const now = new Date();
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  
  // Vraiment actives : RUNNING ou WAITING_VALIDATION, OU CREATED récent
  const trultyActiveSessions = allSessions.filter(s => {
    if (['RUNNING', 'WAITING_VALIDATION'].includes(s.status)) return true;
    if (s.status === 'CREATED') {
      const created = new Date(s.created_at);
      return created > oneHourAgo;
    }
    return false;
  });
  
  // Bloquées : CREATED depuis plus de 1h ou PENDING depuis longtemps
  const stuckSessions = allSessions.filter(s => {
    if (['COMPLETED', 'ABORTED', 'ERROR'].includes(s.status)) return false;
    if (['RUNNING', 'WAITING_VALIDATION'].includes(s.status)) return false;
    const created = new Date(s.created_at);
    return created <= oneHourAgo;
  });
  
  const section = document.getElementById('active-pipeline-section');
  const list = document.getElementById('active-pipeline-list');
  
  if (trultyActiveSessions.length === 0 && stuckSessions.length === 0) {
    section.style.display = 'none';
    return;
  }
  
  section.style.display = 'block';
  let html = '';
  
  // Sessions vraiment actives
  trultyActiveSessions.forEach(s => {
    const project = allProjects.find(p => p.id === s.project_id);
    const projectName = project ? project.name : 'Sans projet';
    html += `
      <div class="active-pipeline-card card card--interactive">
        <div class="active-pipeline-info">
          <span class="active-dot"></span>
          <strong>${s.workflow_type}</strong>
          <span class="text-muted">· ${projectName} · Step ${s.current_step_index + 1}</span>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <a href="module-code.html?session=${s.id}&project_id=${s.project_id}" class="btn-primary btn-sm">→ Reprendre</a>
          <button class="btn-secondary btn-sm" onclick="abandonSession(${s.id})">Abandonner</button>
        </div>
      </div>
    `;
  });
  
  // Sessions bloquées (en collapse, pas trop visibles)
  if (stuckSessions.length > 0) {
    html += `
      <div class="stuck-sessions">
        <div class="stuck-sessions-header" onclick="toggleStuckSessions()">
          <span class="text-muted" style="font-size:0.85rem">
            ⚠️ ${stuckSessions.length} session(s) bloquée(s)
          </span>
          <span id="stuck-sessions-toggle" style="color:var(--text-muted)">▼</span>
        </div>
        <div id="stuck-sessions-list" style="display:none">
    `;
    stuckSessions.forEach(s => {
      const project = allProjects.find(p => p.id === s.project_id);
      const projectName = project ? project.name : 'Sans projet';
      const daysAgo = Math.floor((now - new Date(s.created_at)) / (1000 * 60 * 60 * 24));
      html += `
        <div class="active-pipeline-card card" style="opacity:0.7">
          <div class="active-pipeline-info">
            <span style="color:var(--warning)">⚠️</span>
            <span class="text-muted">${s.workflow_type} · ${projectName} · il y a ${daysAgo}j</span>
          </div>
          <button class="btn-danger btn-sm" onclick="abandonSession(${s.id})">Abandonner</button>
        </div>
      `;
    });
    html += '</div></div>';
  }
  
  list.innerHTML = html;
}
```

### 4b. Fonctions globales pour le dashboard

Ajouter dans `dashboard.js` :
```js
window.abandonSession = async function(sessionId) {
  if (!confirm('Abandonner cette session ?')) return;
  try {
    await window.API.abortPipeline(sessionId);
    window.showToast('Session abandonnée');
    // Recharger les données
    await loadDashboardData();
    renderDashboard();
  } catch(e) {
    window.showToast('Erreur: ' + e.message, 'error');
  }
};

window.toggleStuckSessions = function() {
  const list = document.getElementById('stuck-sessions-list');
  const toggle = document.getElementById('stuck-sessions-toggle');
  if (list.style.display === 'none') {
    list.style.display = 'block';
    toggle.textContent = '▲';
  } else {
    list.style.display = 'none';
    toggle.textContent = '▼';
  }
};
```

**CSS à ajouter :**
```css
.stuck-sessions {
  margin-top: 8px;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}
.stuck-sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
}
.stuck-sessions-header:hover .text-muted {
  color: var(--text-primary);
}
```

---

## FIX 5 — Créer un nouveau projet

Fichier : `frontend/assets/js/sidebar.js`

**Problème :** Pas de bouton pour créer un projet depuis l'interface.

**Solution :** Ajouter un bouton [+ Projet] dans `.sidebar-actions`, à côté des boutons existants.

### 5a. Ajouter le bouton dans le HTML généré

Dans la section `.sidebar-actions` du HTML généré :
```js
html += `
  <div class="sidebar-actions">
    <button id="btn-new-chat" class="btn-sidebar-action">
      <span class="sidebar-text">💬 Nouveau Chat</span>
      <span class="sidebar-collapsed-text" style="display:none">💬</span>
    </button>
    <button id="btn-new-module" class="btn-sidebar-action">
      <span class="sidebar-text">⚙️ Module Code</span>
      <span class="sidebar-collapsed-text" style="display:none">⚙️</span>
    </button>
    <button id="btn-new-project" class="btn-sidebar-action btn-sidebar-action--secondary" title="Nouveau projet">
      <span class="sidebar-text">📁 Nouveau Projet</span>
      <span class="sidebar-collapsed-text" style="display:none">📁</span>
    </button>
  </div>
`;
```

Ajouter l'event listener dans renderSidebar() après les autres :
```js
document.getElementById('btn-new-project').addEventListener('click', handleNewProject);
```

### 5b. Ajouter handleNewProject() dans sidebar.js

```js
async function handleNewProject() {
  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Nom du projet *</label>
      <input type="text" id="modal-project-name" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="Mon Projet">
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Chemin du dossier *</label>
      <input type="text" id="modal-project-path" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)" placeholder="C:\\DEV\\MON_PROJET">
      <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">Le dossier doit exister sur le disque</div>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Type</label>
      <select id="modal-project-type" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        <option value="dev">Développement</option>
        <option value="research">Recherche</option>
        <option value="business">Business</option>
        <option value="other">Autre</option>
      </select>
    </div>
  `;

  window.showModal('Nouveau Projet', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: '📁 Créer', type: 'primary', onClick: async () => {
      const name = document.getElementById('modal-project-name').value.trim();
      const path = document.getElementById('modal-project-path').value.trim();
      const type = document.getElementById('modal-project-type').value;
      
      if (!name || !path) {
        window.showToast('Nom et chemin sont requis', 'error');
        return;
      }
      
      try {
        const project = await window.API.createProject({ name, path, type, instructions: '' });
        window.closeModal();
        window.showToast(`Projet "${name}" créé`);
        // Naviguer vers la page projet
        window.location.href = `project.html?id=${project.id}`;
      } catch(error) {
        window.showToast(error.message, 'error');
      }
    }}
  ]);
}
```

**CSS pour le bouton projet :**
```css
.btn-sidebar-action--secondary {
  background: transparent;
  border-color: transparent;
  color: var(--text-muted);
  font-size: 0.85rem;
}
.btn-sidebar-action--secondary:hover {
  background: var(--bg-input);
  color: var(--text-primary);
  border-color: var(--border);
}
```

---

## VÉRIFICATIONS FINALES

Après toutes les modifications, vérifier :

1. **Clic projet sidebar** → naviguer vers `project.html?id=X` (pas juste déplier)
2. **Logo JARVIS** → clic → retour `index.html`
3. **Chat header** → dropdown modèle s'affiche avec les modèles disponibles
4. **Chat envoi** → le modèle sélectionné est passé dans la requête (vérifier dans DevTools Network)
5. **Dashboard** → sessions CREATED bloquées → dans section "Bloquées" (pas dans "Actif")
6. **Dashboard** → bouton "Abandonner" sur sessions actives → modal confirmation → session ABORTED
7. **Sidebar** → bouton "📁 Nouveau Projet" → modal → création → redirect vers page projet

---

TESTS MANUELS (5 étapes) :

1. Ouvrir le dashboard → cliquer sur le logo ⚡ JARVIS → retour au dashboard ✓
   Cliquer sur le projet "JARVIS" (le nom, pas la flèche) → page projet s'ouvre ✓
   Cliquer sur la flèche ▼ → toggle expand/collapse sans naviguer ✓

2. Ouvrir un chat → le dropdown modèle apparaît dans le header à droite du titre ✓
   Sélectionner un modèle → envoyer un message → dans DevTools > Network > voir la requête POST → body contient `"model": "..."` ✓

3. Dashboard → "MODULE CODE ACTIF" ne montre plus les sessions bloquées depuis des jours dans la section principale ✓
   Les sessions bloquées apparaissent dans "⚠️ X session(s) bloquée(s)" (repliées) ✓
   Clic "Abandonner" sur une session → confirmation → session disparaît de la liste ✓

4. Cliquer "📁 Nouveau Projet" dans la sidebar → modal s'ouvre avec les 3 champs ✓
   Remplir un chemin valide (ex: `C:\DEV\PROJETS`) → créer → redirect vers page projet ✓
   Remplir un chemin invalide → message d'erreur du backend s'affiche dans un toast ✓

5. Relancer les tests E2E `python -m pytest tests/test_frontend_e2e.py -v --tb=short` → toujours 41+ tests passés ✓

FIN DE MISSION :
- Serveur redémarre sans erreur
- 5 tests manuels validés
- Tests E2E toujours verts
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
