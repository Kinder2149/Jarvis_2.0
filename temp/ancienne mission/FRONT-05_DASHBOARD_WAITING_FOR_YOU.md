# FRONT-05 — Dashboard : section "En attente de toi"

> Lire PROJET_CONTEXTE.md en entier avant toute action.
> **Prérequis :** FRONT-03 terminé (`session_status` disponible dans `GET /atelier/prospects`).

---

## Problème exact

Dans `frontend/assets/js/dashboard.js`, la fonction `renderActivePipelines()` mélange sessions RUNNING et WAITING_VALIDATION dans la même section "⚡ Module Code actif". L'utilisateur ne peut pas distinguer ce qui tourne tout seul de ce qui attend son intervention.

De plus :
1. Les sessions Atelier en WAITING_VALIDATION ne sont **pas affichées** sur le dashboard (seules les sessions Module Code via `getProjectSessions` sont dans `allSessions`)
2. Il n'y a pas de bannière urgente type "X éléments attendent ton action"

Le dashboard est le premier écran ouvert le matin — c'est précisément là où il faut savoir immédiatement "qu'est-ce qui bloque ?"

---

## Objectif

Restructurer la section active du dashboard en **2 parties distinctes** :

**Partie 1 — "En attente de toi" (WAITING_VALIDATION)** — PRIORITÉ HAUTE, en tête
- Sessions Module Code en WAITING_VALIDATION (déjà dans allSessions)
- Sessions Atelier en WAITING_VALIDATION (nouveau : via `GET /atelier/prospects`)
- Affichage : fond légèrement coloré (orange/warning), bouton "→ Reprendre" direct

**Partie 2 — "En cours" (RUNNING)** — secondaire
- Sessions Module Code en RUNNING
- Ne pas montrer les sessions Atelier RUNNING (pas de page de reprise directe sans prospect_id)

Les sessions bloquées (CREATED>1h) restent dans leur section repliable existante.

---

## Fichiers à modifier

1. `frontend/assets/js/dashboard.js`
2. `frontend/index.html` — ajouter l'ID HTML manquant si besoin

---

## Modifications détaillées

### 1. `dashboard.js` — charger les prospects Atelier

Dans `loadDashboardData()`, ajouter le chargement des prospects Atelier :

```js
async function loadDashboardData() {
  try {
    const [projects, conversations, atelierProspects] = await Promise.all([
      window.API.getProjects(),
      window.API.getConversations(),
      window.API.getProspects().catch(() => [])
    ]);

    allProjects = projects;
    allConversations = conversations;
    allAtelierProspects = atelierProspects; // ← nouveau

    const sessionPromises = projects.map(p =>
      window.API.getProjectSessions(p.id).catch(() => [])
    );
    const sessionsArrays = await Promise.all(sessionPromises);
    allSessions = sessionsArrays.flat();

  } catch (error) {
    console.error('Erreur chargement dashboard:', error);
    window.showToast('Erreur de chargement', 'error');
  }
}
```

Ajouter la déclaration `let allAtelierProspects = [];` en haut du module avec les autres variables d'état.

### 2. `dashboard.js` — restructurer `renderActivePipelines()`

Remplacer la fonction entière par :

```js
function renderActivePipelines() {
  const now = new Date();
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

  // WAITING_VALIDATION : Module Code
  const waitingModuleSessions = allSessions.filter(s => s.status === 'WAITING_VALIDATION');

  // WAITING_VALIDATION : Atelier
  const waitingAtelierProspects = allAtelierProspects.filter(p => p.session_status === 'WAITING_VALIDATION');

  // RUNNING : Module Code uniquement
  const runningSessions = allSessions.filter(s => s.status === 'RUNNING');

  // Créées récemment (< 1h) mais pas encore RUNNING (en démarrage)
  const startingSessions = allSessions.filter(s => {
    if (s.status !== 'CREATED') return false;
    return new Date(s.created_at) > oneHourAgo;
  });

  // Bloquées (CREATED > 1h)
  const stuckSessions = allSessions.filter(s => {
    if (['COMPLETED', 'ABORTED', 'ERROR', 'FAILED', 'RUNNING', 'WAITING_VALIDATION'].includes(s.status)) return false;
    return new Date(s.created_at) <= oneHourAgo;
  });

  const hasAnything = waitingModuleSessions.length > 0 || waitingAtelierProspects.length > 0
    || runningSessions.length > 0 || startingSessions.length > 0 || stuckSessions.length > 0;

  const section = document.getElementById('active-pipeline-section');
  const list = document.getElementById('active-pipeline-list');

  if (!hasAnything) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';
  let html = '';

  // ── Partie 1 : En attente de TOI ──────────────────────────────
  const totalWaiting = waitingModuleSessions.length + waitingAtelierProspects.length;
  if (totalWaiting > 0) {
    html += `
      <div class="waiting-banner">
        <span class="waiting-banner-title">⏸️ ${totalWaiting} session${totalWaiting > 1 ? 's' : ''} attendent ta validation</span>
      </div>
    `;

    waitingModuleSessions.forEach(s => {
      const project = allProjects.find(p => p.id === s.project_id);
      const projectName = project ? project.name : 'Sans projet';
      // Trouver le step bloqué
      html += `
        <div class="active-pipeline-card card card--waiting">
          <div class="active-pipeline-info">
            <span style="color:#f59e0b">⏸️</span>
            <strong>${s.workflow_type}</strong>
            <span class="text-muted">· ${projectName} · Step ${s.current_step_index + 1}</span>
          </div>
          <a href="module-code.html?session=${s.id}&project_id=${s.project_id}" class="btn-primary btn-sm">→ Valider</a>
        </div>
      `;
    });

    waitingAtelierProspects.forEach(p => {
      html += `
        <div class="active-pipeline-card card card--waiting">
          <div class="active-pipeline-info">
            <span style="color:#f59e0b">⏸️</span>
            <strong>Atelier</strong>
            <span class="text-muted">· ${p.nom}</span>
          </div>
          <a href="atelier.html?prospect_id=${p.id}" class="btn-primary btn-sm">→ Valider</a>
        </div>
      `;
    });
  }

  // ── Partie 2 : En cours (RUNNING) ─────────────────────────────
  const totalRunning = runningSessions.length + startingSessions.length;
  if (totalRunning > 0) {
    html += `<div class="running-section-title text-muted" style="font-size:0.8rem;padding:0.5rem 0 0.25rem">⚡ En cours</div>`;

    [...runningSessions, ...startingSessions].forEach(s => {
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
            <a href="module-code.html?session=${s.id}&project_id=${s.project_id}" class="btn-secondary btn-sm">→ Voir</a>
            <button class="btn-danger btn-sm" onclick="abandonSession(${s.id})">Abandonner</button>
          </div>
        </div>
      `;
    });
  }

  // ── Sessions bloquées ──────────────────────────────────────────
  if (stuckSessions.length > 0) {
    html += `
      <div class="stuck-sessions">
        <div class="stuck-sessions-header" onclick="toggleStuckSessions()">
          <span class="text-muted" style="font-size:0.85rem">⚠️ ${stuckSessions.length} session(s) bloquée(s)</span>
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

### 3. `index.html` — titre section active

Dans `index.html`, modifier le titre de la section :
```html
<h2 class="section-title">⚡ Module Code actif</h2>
```
→
```html
<h2 class="section-title" id="active-pipeline-title">Sessions actives</h2>
```

### 4. `frontend/assets/style.css` — style banner waiting

Ajouter le style pour la bannière waiting :

```css
.waiting-banner {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  margin-bottom: 0.5rem;
}
.waiting-banner-title {
  color: #f59e0b;
  font-weight: 600;
  font-size: 0.9rem;
}
.card--waiting {
  border-left: 3px solid #f59e0b;
}
```

---

## Tests manuels

1. Dashboard avec aucune session active → section masquée ✓
2. Lancer pipeline Module Code → laisser bloquer en WAITING_VALIDATION → dashboard affiche "⏸️ 1 session attend ta validation" en orange ✓
3. Lancer pipeline Atelier → laisser bloquer au form → dashboard affiche ⏸️ Atelier aussi ✓
4. Valider la session → banner disparaît ✓
5. Session RUNNING → section "⚡ En cours" visible ✓
6. Session CREATED>1h → section "bloquée" en bas ✓
7. Vérifier `abandonSession()` fonctionne toujours ✓

---

## FIN DE MISSION

- [ ] Build OK
- [ ] Banner ⏸️ visible pour WAITING_VALIDATION Module Code ET Atelier
- [ ] Clic "→ Valider" navigue directement vers la bonne page
- [ ] Section "En cours" séparée de "En attente"
- [ ] Aucune régression sur timeline, filtres, stats
- [ ] PROJET_CONTEXTE.md section 8 et CHANGELOG.md mis à jour
