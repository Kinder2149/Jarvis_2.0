# FRONT-01 — CTA post-session Module Code

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Dans `frontend/assets/js/module-code.js`, la fonction `renderActionZone(session)` masque complètement la zone d'action quand il n'y a pas de step en WAITING_VALIDATION :

```js
if (!waitingStep || waitingStep.requires_validation !== 1) {
  actionZone.style.display = 'none';
  return;
}
```

Résultat : quand une session est COMPLETED, ABORTED ou ERROR → page morte. Aucun bouton, aucune navigation, l'utilisateur ne sait pas quoi faire.

---

## Objectif

Ajouter une zone d'action contextuelle quand la session est terminée :
- **COMPLETED** → message succès + bouton retour projet + bouton nouvelle session
- **ABORTED / ERROR / FAILED** → message d'état + bouton retour projet + bouton relancer même workflow

Ajouter dans `sidebar.js` une fonction `handleNewModulePreset(projectId, workflowType)` pour lancer une session avec projet et workflow pré-remplis.

---

## Fichiers à modifier

1. `frontend/assets/js/module-code.js`
2. `frontend/assets/js/sidebar.js`

---

## Modifications détaillées

### 1. `module-code.js` — fonction `renderActionZone`

Remplacer le début de la fonction par :

```js
function renderActionZone(session) {
  const actionZone = document.getElementById('mc-action-zone');

  // Cas terminal : session terminée, abandonnée ou en erreur
  const TERMINAL = ['COMPLETED', 'ABORTED', 'ERROR', 'FAILED'];
  if (TERMINAL.includes(session.status)) {
    actionZone.style.display = 'block';
    const isSuccess = session.status === 'COMPLETED';
    const emoji = isSuccess ? '✅' : '❌';
    const label = {
      COMPLETED: 'Session terminée avec succès',
      ABORTED: 'Session abandonnée',
      ERROR: 'Session en erreur',
      FAILED: 'Session échouée'
    }[session.status] || session.status;

    const backBtn = projectId
      ? `<a href="project.html?id=${projectId}" class="btn-secondary">📁 Retour au projet</a>`
      : `<a href="index.html" class="btn-secondary">🏠 Tableau de bord</a>`;

    const relanceBtn = !isSuccess && projectId && currentSession
      ? `<button class="btn-secondary" onclick="window._relancerSession()">🔄 Relancer ce workflow</button>`
      : '';

    const nouvelleBtn = projectId
      ? `<button class="btn-primary" onclick="window._nouvelleSession()">⚡ Nouvelle session</button>`
      : '';

    actionZone.innerHTML = `
      <div class="mc-action-header">
        <h3>${emoji} ${label}</h3>
      </div>
      <div class="mc-validation-actions">
        ${backBtn}
        ${relanceBtn}
        ${nouvelleBtn}
      </div>
    `;
    return;
  }

  // Suite du code existant inchangée :
  const waitingStep = session.steps?.find(s => s.status === 'WAITING_VALIDATION');
  if (!waitingStep || waitingStep.requires_validation !== 1) {
    actionZone.style.display = 'none';
    return;
  }
  // ... rest of existing code unchanged
```

Ajouter à la fin du module (avant le `window.addEventListener('beforeunload', ...)`) :

```js
  window._relancerSession = function() {
    if (currentSession && projectId) {
      if (window.handleNewModulePreset) {
        window.handleNewModulePreset(projectId, currentSession.workflow_type);
      } else if (window.handleNewModule) {
        window.handleNewModule();
      }
    }
  };

  window._nouvelleSession = function() {
    if (window.handleNewModulePreset && projectId) {
      window.handleNewModulePreset(projectId, null);
    } else if (window.handleNewModule) {
      window.handleNewModule();
    }
  };
```

### 2. `sidebar.js` — ajouter `handleNewModulePreset`

Ajouter cette fonction après la fonction `handleNewModule` existante :

```js
async function handleNewModulePreset(presetProjectId, presetWorkflow) {
  const projects = await window.API.getProjects();

  const workflowOptions = [
    { value: 'session_start',    label: 'Session Start — démarrer une session de dev' },
    { value: 'session_end',      label: 'Session End — clôturer, commit, docs' },
    { value: 'bug_simple',       label: 'Bug Simple — analyser et corriger un bug' },
    { value: 'mission_complexe', label: 'Mission Complexe — feature multi-fichiers' },
    { value: 'nouveau_projet',   label: 'Nouveau Projet — initialiser un projet' },
    { value: 'projet_existant',  label: 'Projet Existant — reprendre un projet' },
  ];

  let projectOptionsHTML = '';
  projects.forEach(p => {
    const selected = String(p.id) === String(presetProjectId) ? 'selected' : '';
    projectOptionsHTML += `<option value="${p.id}" ${selected}>${p.name}</option>`;
  });

  let workflowOptionsHTML = '';
  workflowOptions.forEach(w => {
    const selected = w.value === presetWorkflow ? 'selected' : '';
    workflowOptionsHTML += `<option value="${w.value}" ${selected}>${w.label}</option>`;
  });

  const bodyHTML = `
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Projet *</label>
      <select id="modal-module-project" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)"
              ${presetProjectId ? 'disabled' : ''}>
        ${projectOptionsHTML}
      </select>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Workflow *</label>
      <select id="modal-module-workflow" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
        ${workflowOptionsHTML}
      </select>
    </div>
    <div style="margin-bottom:1rem">
      <label style="display:block;margin-bottom:0.5rem;color:var(--text-primary)">Demande initiale *</label>
      <textarea id="modal-module-input" rows="4" style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);resize:vertical" placeholder="Décrivez votre demande..."></textarea>
    </div>
  `;

  window.showModal('Nouvelle session', bodyHTML, [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: 'Lancer', type: 'primary', onClick: async () => {
      const projId = presetProjectId || document.getElementById('modal-module-project').value;
      const workflow = document.getElementById('modal-module-workflow').value;
      const input = document.getElementById('modal-module-input').value.trim();
      if (!projId || !workflow || !input) {
        window.showToast('Tous les champs sont requis', 'error');
        return;
      }
      try {
        const result = await window.API.startPipeline({
          project_id: parseInt(projId),
          workflow_type: workflow,
          initial_input: input
        });
        const sessionId = result.session?.id || result.id;
        if (!sessionId) throw new Error('Session ID non trouvé');
        window.closeModal();
        window.location.href = `module-code.html?session=${sessionId}&project_id=${projId}`;
      } catch (error) {
        window.showToast(error.message, 'error');
      }
    }}
  ]);
}

window.handleNewModulePreset = handleNewModulePreset;
```

**Note importante :** Dans la fonction `handleNewModule` existante, remplacer aussi les options du workflow dropdown pour qu'elles utilisent le même format avec description (pas juste la valeur brute) — utiliser le même tableau `workflowOptions` défini dans `handleNewModulePreset`.

---

## Tests manuels

1. Lancer une session Module Code → attendre qu'elle se termine (ou l'abandonner)
2. **Page COMPLETED** : la zone d'action doit afficher "✅ Session terminée avec succès" + bouton "📁 Retour au projet" + bouton "⚡ Nouvelle session"
3. Cliquer "📁 Retour au projet" → naviguer vers project.html?id=X ✓
4. Cliquer "⚡ Nouvelle session" → modal s'ouvre avec projet pré-sélectionné + workflow dropdown avec descriptions
5. **Page ABORTED** : zone affiche "❌ Session abandonnée" + boutons retour + "🔄 Relancer ce workflow"
6. Cliquer "🔄 Relancer ce workflow" → modal avec même workflow pré-sélectionné
7. Vérifier que la validation WAITING_VALIDATION fonctionne toujours normalement (pas de régression)

---

## FIN DE MISSION

- [ ] Build OK (serveur démarre sans erreur)
- [ ] Test manuel 3 cas : COMPLETED, ABORTED, WAITING_VALIDATION (toujours fonctionnel)
- [ ] PROJET_CONTEXTE.md section 8 et CHANGELOG.md mis à jour
