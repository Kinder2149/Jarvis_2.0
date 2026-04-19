# MISSION AC_04 — Frontend Vue Pipeline (Atelier Connecté)

## Prérequis
**AC_03 doit être complété** : `atelier.html`, `atelier.js` (Vue Prospects), modifications `api.js`, `style.css`, `sidebar.js`.

## Objectif
Compléter la **Vue Pipeline** dans `atelier.js` et `atelier.html` :
- Renderer formulaire **SAISIE** (step 0, output_type="form")
- Renderer **CHECKPOINT** avec boutons Valider/Abandonner (step 4, output_type="checkpoint")
- Renderer **EXPORT** avec liste de fichiers + bouton ZIP (step 8, output_type="export")
- Ajouter le bouton **"Lancer le step suivant"** (pour les steps auto qui restent PENDING)
- Améliorer la carte step pour afficher l'output complet au clic (expand)

---

## Architecture des 9 steps du pipeline `atelier_restauration`

| Index | Nom           | model_type | output_type  | requires_validation |
|-------|---------------|------------|--------------|---------------------|
| 0     | saisie        | none       | form         | true                |
| 1     | qualification | routing    | qualification| false               |
| 2     | analyse_site  | analysis   | extraction   | false               |
| 3     | proposition   | analysis   | proposition  | false               |
| 4     | checkpoint    | none       | checkpoint   | true                |
| 5     | generation_css| code       | file         | false               |
| 6     | generation_index| code     | file         | false               |
| 7     | generation_admin| code     | file         | false               |
| 8     | export        | none       | export       | false               |

**Logique des actions :**
- Steps 0 et 4 : `status === 'WAITING_VALIDATION'` → afficher la zone d'action
- Steps 1-3, 5-7 : auto-complétés par le backend, aucune action utilisateur
- Step 8 (export) : `status === 'COMPLETED'` → afficher liste fichiers + bouton ZIP

**Important : étape de progression manuelle**
Le polling détecte quand une session est en `WAITING_VALIDATION`. Après validation, le backend passe la session en `RUNNING` puis auto-complète les steps suivants. Le frontend n'a pas besoin d'appeler `nextStep` — le backend avance tout seul jusqu'au prochain `WAITING_VALIDATION` ou `COMPLETED`.

Seule exception : la route `POST /pipelines/{sessionId}/next` est utilisée si un step reste bloqué en PENDING après une longue attente.

---

## 1. Formulaire SAISIE (step 0, output_type="form")

### Structure du JSON `form_data` attendu par le backend :
```json
{
  "nom": "Le Bistrot du Coin",
  "url": "https://bistrot.fr",
  "categorie": "restauration",
  "observations": "Restaurant de quartier, 30 couverts, pas de resa en ligne, beaucoup de clients fidèles",
  "outils": {
    "evenements": false,
    "avis": false,
    "emporter": false
  }
}
```

`get_activated_tools()` lit `saisie_data["outils"]` et active automatiquement `reservations` + `menu_ardoise` (toujours), plus les 3 optionnels si cochés.

### Remplacer dans `atelier.js` la fonction `renderSaisieForm(step)` par :

```js
function renderSaisieForm(step) {
  return `
    <div class="mc-action-header">
      <h3>📋 Saisie prospect</h3>
      <p class="text-muted">Complétez les informations pour lancer l'analyse IA.</p>
    </div>
    <div id="saisie-form-body" style="display:flex;flex-direction:column;gap:1rem;margin-top:1rem">
      <div>
        <label class="form-label">Observations terrain *</label>
        <textarea id="saisie-observations" rows="4" class="form-input"
          placeholder="Ex: Restaurant de 30 couverts, clientèle fidèle, pas de système de réservation en ligne, menu ardoise au tableau..."
          style="width:100%;resize:vertical"></textarea>
        <div class="form-hint">Ce que vous avez observé lors de votre prospection physique</div>
      </div>
      <div>
        <label class="form-label">Outils supplémentaires à proposer</label>
        <div class="saisie-tools-grid">
          <label class="saisie-tool-toggle">
            <input type="checkbox" disabled checked> Réservations <span class="text-muted">(inclus)</span>
          </label>
          <label class="saisie-tool-toggle">
            <input type="checkbox" disabled checked> Menu ardoise <span class="text-muted">(inclus)</span>
          </label>
          <label class="saisie-tool-toggle">
            <input type="checkbox" id="tool-evenements"> Événements
          </label>
          <label class="saisie-tool-toggle">
            <input type="checkbox" id="tool-avis"> Avis clients
          </label>
          <label class="saisie-tool-toggle">
            <input type="checkbox" id="tool-emporter"> Commande emporter
          </label>
        </div>
      </div>
      <div class="mc-validation-actions">
        <button id="btn-saisie-submit" class="btn-primary">Lancer l'analyse ➜</button>
      </div>
    </div>
  `;
}
```

### Remplacer `attachSaisieHandlers(step)` par :

```js
async function attachSaisieHandlers(step) {
  // Pré-remplir avec les données du prospect
  try {
    const { prospect } = await window.API.getProspect(currentProspectId);
    if (prospect.form_data) {
      try {
        const saved = JSON.parse(prospect.form_data);
        if (saved.observations) {
          document.getElementById('saisie-observations').value = saved.observations;
        }
        if (saved.outils) {
          if (saved.outils.evenements) document.getElementById('tool-evenements').checked = true;
          if (saved.outils.avis) document.getElementById('tool-avis').checked = true;
          if (saved.outils.emporter) document.getElementById('tool-emporter').checked = true;
        }
      } catch (e) { /* form_data pas encore JSON */ }
    }
  } catch (e) { /* pas bloquant */ }

  document.getElementById('btn-saisie-submit')?.addEventListener('click', async () => {
    const observations = document.getElementById('saisie-observations')?.value.trim();
    if (!observations) {
      window.showToast && window.showToast('Les observations terrain sont requises', 'error');
      return;
    }

    const btn = document.getElementById('btn-saisie-submit');
    btn.disabled = true;
    btn.textContent = 'Envoi...';

    const { prospect } = await window.API.getProspect(currentProspectId).catch(() => ({ prospect: {} }));

    const formData = {
      nom: prospect.nom || '',
      url: prospect.url || '',
      categorie: 'restauration',
      observations,
      outils: {
        evenements: document.getElementById('tool-evenements')?.checked || false,
        avis: document.getElementById('tool-avis')?.checked || false,
        emporter: document.getElementById('tool-emporter')?.checked || false,
      }
    };

    try {
      // Sauvegarder form_data sur le prospect
      await window.API.patchProspect(currentProspectId, { form_data: JSON.stringify(formData) });

      // Valider le step 0 avec le JSON comme edited_output
      await window.API.validateStep(currentSessionId, step.id, {
        approved: true,
        edited_output: JSON.stringify(formData)
      });

      window.showToast && window.showToast('Analyse lancée !');
      await showPipelineView(currentProspectId);
      startPolling();
    } catch (err) {
      window.showToast && window.showToast(err.message || 'Erreur soumission', 'error');
      btn.disabled = false;
      btn.textContent = 'Lancer l\'analyse ➜';
    }
  });
}
```

---

## 2. Checkpoint (step 4, output_type="checkpoint")

### Remplacer `attachCheckpointHandlers(step)` par :

```js
function attachCheckpointHandlers(step) {
  document.getElementById('btn-checkpoint-approve')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-checkpoint-approve');
    btn.disabled = true;
    btn.textContent = 'Validation...';
    try {
      await window.API.validateStep(currentSessionId, step.id, { approved: true });
      window.showToast && window.showToast('Génération lancée !');
      await showPipelineView(currentProspectId);
      startPolling();
    } catch (err) {
      window.showToast && window.showToast(err.message, 'error');
      btn.disabled = false;
      btn.textContent = '✅ Valider — Lancer la génération';
    }
  });

  document.getElementById('btn-checkpoint-reject')?.addEventListener('click', async () => {
    if (!confirm('Abandonner ce pipeline ? La session sera terminée.')) return;
    try {
      await window.API.validateStep(currentSessionId, step.id, { approved: false });
      window.showToast && window.showToast('Pipeline abandonné');
      stopPolling();
      await showPipelineView(currentProspectId);
    } catch (err) {
      window.showToast && window.showToast(err.message, 'error');
    }
  });
}
```

---

## 3. Export (step 8, output_type="export")

Quand le dernier step (export) est COMPLETED, afficher la liste des fichiers et le bouton ZIP.

### Modifier `renderPipelineActionZone(session)` pour gérer le cas export :

Remplacer la fonction entière par :

```js
function renderPipelineActionZone(session) {
  const zone = document.getElementById('pipeline-action-zone');

  // Cas 1 : step en WAITING_VALIDATION
  const waiting = session.steps?.find(s => s.status === 'WAITING_VALIDATION');
  if (waiting) {
    zone.style.display = 'block';
    switch (waiting.output_type) {
      case 'form':
        zone.innerHTML = renderSaisieForm(waiting);
        attachSaisieHandlers(waiting);
        break;
      case 'checkpoint':
        zone.innerHTML = renderCheckpointZone(waiting);
        attachCheckpointHandlers(waiting);
        break;
      default:
        zone.innerHTML = renderGenericWaiting(waiting);
        attachGenericHandlers(waiting);
    }
    return;
  }

  // Cas 2 : session COMPLETED → afficher zone export si step 8 completed
  if (session.status === 'COMPLETED') {
    const exportStep = session.steps?.find(s => s.step_name === 'export' && s.status === 'COMPLETED');
    if (exportStep) {
      zone.style.display = 'block';
      zone.innerHTML = renderExportZone();
      attachExportHandlers();
      return;
    }
  }

  zone.style.display = 'none';
}
```

### Ajouter `renderExportZone()` et `attachExportHandlers()` :

```js
function renderExportZone() {
  return `
    <div class="mc-action-header">
      <h3>🎉 Démo générée avec succès !</h3>
      <p class="text-muted">Les fichiers sont prêts à être exportés.</p>
    </div>
    <div id="export-files-list" style="margin:1rem 0">
      <div class="spinner" style="margin:1rem auto"></div>
    </div>
    <div class="mc-validation-actions">
      <a id="btn-export-zip" class="btn-primary" style="text-decoration:none;display:inline-block">
        ⬇️ Télécharger le ZIP
      </a>
      <button id="btn-mark-contacted" class="btn-secondary">Marquer comme contacté</button>
    </div>
  `;
}

async function attachExportHandlers() {
  // Charger la liste des fichiers
  try {
    const { files } = await window.API.listProspectFiles(currentProspectId);
    const listEl = document.getElementById('export-files-list');
    if (!listEl) return;
    if (!files || files.length === 0) {
      listEl.innerHTML = '<p class="text-muted">Aucun fichier trouvé</p>';
    } else {
      listEl.innerHTML = `
        <div class="export-file-list">
          ${files.map(f => `
            <div class="export-file-row">
              <span class="export-file-name">📄 ${f.name}</span>
              <span class="text-muted export-file-size">${f.size_kb} KB</span>
            </div>
          `).join('')}
        </div>
      `;
    }
  } catch (e) {
    const listEl = document.getElementById('export-files-list');
    if (listEl) listEl.innerHTML = '<p class="text-muted">Impossible de charger la liste</p>';
  }

  // Lien ZIP
  const zipBtn = document.getElementById('btn-export-zip');
  if (zipBtn) {
    zipBtn.href = window.API.exportProspectZip(currentProspectId);
  }

  // Marquer contacté
  document.getElementById('btn-mark-contacted')?.addEventListener('click', async () => {
    try {
      await window.API.patchProspect(currentProspectId, { statut: 'contacte' });
      window.showToast && window.showToast('Statut mis à jour : Contacté');
    } catch (err) {
      window.showToast && window.showToast(err.message, 'error');
    }
  });
}
```

---

## 4. CSS supplémentaire — ajouter à la fin de `style.css`

```css
/* ── Atelier Pipeline ─────────────────────────────────────── */

.form-label {
  display: block;
  margin-bottom: 0.4rem;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.form-input {
  width: 100%;
  padding: 8px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 0.9rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent);
}

.form-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.saisie-tools-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.saisie-tool-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--text-primary);
  transition: border-color 0.15s;
}

.saisie-tool-toggle:hover {
  border-color: var(--accent);
}

.saisie-tool-toggle input[type="checkbox"] {
  accent-color: var(--accent);
}

/* Export zone */
.export-file-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem;
}

.export-file-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--border);
}

.export-file-row:last-child {
  border-bottom: none;
}

.export-file-name {
  font-size: 0.85rem;
  color: var(--text-primary);
}

.export-file-size {
  font-size: 0.75rem;
}
```

---

## 5. Amélioration de l'affichage des steps — expand au clic

Dans `atelier.js`, modifier `renderAtlierStepCard(step)` pour rendre les steps COMPLETED cliquables et afficher l'output complet en expand :

```js
function renderAtlierStepCard(step) {
  const statusClass = getStepStatusClass(step.status);
  const indicator = getStepIndicator(step.status);
  const isExpandable = step.status === 'COMPLETED' && step.output_data && step.output_data.length > 80;

  let outputPreview = '';
  if (step.status === 'COMPLETED' && step.output_data) {
    const preview = step.output_data.substring(0, 100);
    outputPreview = `
      <div class="step-output step-output--preview" data-full="${encodeURIComponent(step.output_data)}">
        ${preview}${step.output_data.length > 100 ? '...' : ''}
        ${isExpandable ? '<span class="step-expand-hint text-muted"> ▶ voir plus</span>' : ''}
      </div>
    `;
  }

  let errorHTML = '';
  if ((step.status === 'FAILED' || step.status === 'ERROR') && step.error_message) {
    errorHTML = `<div class="step-error">❌ ${step.error_message}</div>`;
  }

  return `
    <div class="step-card ${statusClass} ${isExpandable ? 'step-card--expandable' : ''}" data-step-id="${step.id}">
      <div class="step-card-left">
        <div class="step-indicator">${indicator}</div>
        <div class="step-index">${step.step_index + 1}</div>
      </div>
      <div class="step-card-body">
        <div class="step-name">${step.step_display_name || step.step_name}</div>
        <div class="step-meta"><span class="text-muted">${step.model_used || step.model_type || ''}</span></div>
        ${outputPreview}
        ${errorHTML}
      </div>
    </div>
  `;
}
```

Et dans `renderPipelineSteps(session)`, après avoir généré le HTML, attacher les événements expand :

```js
function renderPipelineSteps(session) {
  const container = document.getElementById('pipeline-steps-list');
  if (!session.steps?.length) {
    container.innerHTML = '<p style="color:var(--text-muted);padding:2rem">Aucun step</p>';
    return;
  }
  const sorted = [...session.steps].sort((a, b) => a.step_index - b.step_index);
  container.innerHTML = sorted.map(step => renderAtlierStepCard(step)).join('');

  // Expand au clic
  container.querySelectorAll('.step-card--expandable').forEach(card => {
    card.addEventListener('click', () => {
      const previewEl = card.querySelector('.step-output--preview');
      if (!previewEl) return;
      const isExpanded = card.classList.toggle('step-card--expanded');
      if (isExpanded) {
        const full = decodeURIComponent(previewEl.dataset.full);
        const md = window.renderMarkdown || ((t) => t.replace(/\n/g, '<br>'));
        previewEl.innerHTML = md(full);
      } else {
        const full = decodeURIComponent(previewEl.dataset.full);
        const preview = full.substring(0, 100);
        previewEl.innerHTML = `${preview}${full.length > 100 ? '...' : ''}<span class="step-expand-hint text-muted"> ▶ voir plus</span>`;
        previewEl.dataset.full = encodeURIComponent(full);
      }
    });
  });
}
```

Ajouter dans `style.css` :

```css
.step-card--expandable {
  cursor: pointer;
}

.step-card--expandable:hover {
  border-color: var(--accent);
}

.step-expand-hint {
  font-size: 0.75rem;
  margin-left: 0.25rem;
}

.step-card--expanded .step-output--preview {
  max-height: none;
  font-size: 0.85rem;
  white-space: pre-wrap;
  overflow: auto;
}
```

---

## 6. Vérification finale

Tester les scénarios suivants avec le serveur JARVIS lancé :

### Scénario A — Nouveau prospect complet
1. Ouvrir `atelier.html` → kanban s'affiche
2. Créer un prospect "Test AC_04" avec URL `https://example.com`
3. Cliquer sur la carte → vue pipeline
4. Cliquer "Lancer l'analyse" → bouton "Lancer le step suivant" disparaît, le step 0 passe en WAITING_VALIDATION
5. Le formulaire SAISIE s'affiche avec les champs observations + checkboxes outils
6. Remplir les observations, cocher "Événements", cliquer "Lancer l'analyse ➜"
7. La qualification (step 1) démarre automatiquement (spinner visible si LLM lent)
8. **Sans LLM configuré** : les steps LLM passeront en FAILED, c'est attendu — vérifier surtout que le formulaire se soumet sans erreur

### Scénario B — Checkpoint
9. Forcer en base ou via mock : step 4 en WAITING_VALIDATION avec output_data = texte de proposition
10. Vérifier que la zone d'action affiche le texte + boutons VALIDER / ABANDONNER
11. Cliquer ABANDONNER → confirm popup → pipeline ABORTED

### Scénario C — Export
12. Forcer en base : session COMPLETED, step "export" COMPLETED
13. Vérifier zone export avec liste fichiers et bouton ZIP

### Scénario D — Expand step
14. Sur un step COMPLETED avec output_data long
15. Cliquer → l'output s'étend
16. Recliquer → se réduit

---

## Rappel : ne pas modifier dans cette mission
- `module-code.js` — pas toucher, les deux modules sont indépendants
- `pipeline_engine.py` — backend déjà complet
- Les routes API backend — déjà tous implémentés en AC_01/AC_02
