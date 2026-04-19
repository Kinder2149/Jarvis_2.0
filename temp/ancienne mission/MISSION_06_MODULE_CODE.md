# MISSION 06 — Module Code

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2 — lire entièrement)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Module Code — Exécution et suivi des workflows IA

OBJECTIF :
Implémenter la page Module Code de JARVIS (ex "Pipeline").
C'est la page où l'utilisateur suit en temps réel l'exécution d'un workflow IA,
valide les checkpoints humains, voit les diffs de fichiers, et peut abandonner la session.
La page doit fonctionner en deux modes : ACTIF (polling temps réel + validation)
et HISTORIQUE (lecture seule d'une session terminée).

ATTENTION : C'est la page la plus critique. Les boutons de validation doivent
fonctionner en accord avec l'état RÉEL retourné par le backend.
Aucun bouton de validation ne doit apparaître si le backend ne le demande pas.

PÉRIMÈTRE :
Fichiers à modifier :
- frontend/module-code.html  (ajouter le contenu dans #page-module-code)

Fichiers à créer :
- frontend/assets/js/module-code.js

Prérequis : Mission 02 terminée.

---

INSTRUCTIONS DÉTAILLÉES :

### frontend/module-code.html

Ajouter dans `#page-module-code` :

```html
<div id="page-module-code">

  <!-- Header session -->
  <div class="mc-header">
    <div class="mc-header-info">
      <div class="mc-title">
        <span id="mc-workflow-type">...</span>
        <span id="mc-status-badge"></span>
      </div>
      <div class="mc-meta">
        <span id="mc-project-link"></span>
        <span id="mc-start-time" class="text-muted"></span>
        <span id="mc-total-cost"></span>
      </div>
    </div>
    <button id="btn-abort" class="btn-danger" style="display:none">⛔ Abandonner</button>
  </div>

  <!-- Stepper (liste des steps) -->
  <div class="mc-steps" id="mc-steps-list"></div>

  <!-- Zone d'action courante (validation, diff...) -->
  <div id="mc-action-zone" style="display:none" class="mc-action-zone card"></div>

</div>
```

---

### frontend/assets/js/module-code.js

**Variables globales du module :**
```js
let sessionId = null
let projectId = null
let pollInterval = null
let lastStatus = null
```

**Initialisation :**
```
sessionId = getURLParam('session')
projectId = getURLParam('project_id')
```
Si pas de sessionId → afficher erreur.
Charger la session une première fois → render → si active, démarrer le polling.

**Fonction principale : loadSession()**
1. `const session = await API.getPipeline(sessionId)`
2. Appeler `renderSession(session)`
3. Si session active → démarrer polling (si pas déjà démarré)
4. Si session terminée → arrêter polling

**Polling :**
```js
function startPolling() {
  if (pollInterval) return
  pollInterval = setInterval(async () => {
    try {
      const session = await API.getPipeline(sessionId)
      renderSession(session)
      if (['COMPLETED', 'ABORTED', 'ERROR'].includes(session.status)) {
        stopPolling()
      }
    } catch(e) {
      // Log silencieux, ne pas afficher toast en boucle
    }
  }, 2000)
}

function stopPolling() {
  clearInterval(pollInterval)
  pollInterval = null
}
```

**renderSession(session) — Rendu complet :**

1. **Header** :
   - `#mc-workflow-type` → `session.workflow_type` (remplacer _ par espaces, capitaliser)
   - `#mc-status-badge` → `statusBadge(session.status)`
   - `#mc-start-time` → `formatDate(session.created_at)`
   - `#mc-total-cost` → charger `API.getPipelineCosts(sessionId)` si session terminée
   - `#btn-abort` → visible seulement si status NOT IN ['COMPLETED', 'ABORTED', 'ERROR']
   - `#mc-project-link` → si projectId : `<a href="project.html?id={projectId}">📁 {nom}</a>`

2. **Steps list** (`#mc-steps-list`) :
   Vider et reconstruire depuis `session.steps` (tableau ordonné par step_index).
   Pour chaque step, rendre un `.step-card` :

   ```html
   <div class="step-card step-card--{status_class}" data-step-id="{step.id}">
     <div class="step-card-left">
       <div class="step-indicator">{indicateur visuel}</div>
       <div class="step-index">{step.step_index + 1}</div>
     </div>
     <div class="step-card-body">
       <div class="step-name">{step.step_display_name}</div>
       <div class="step-meta">
         <span class="text-muted">{step.model_used || step.model_type}</span>
         {si completed : durée approximative si dispo}
       </div>
       {si completed et output_data : <div class="step-output">{preview output 120 chars}</div>}
       {si error : <div class="step-error">{step.error_message}</div>}
     </div>
     <div class="step-card-right">
       {boutons contextuels — voir ci-dessous}
     </div>
   </div>
   ```

   **Indicateurs visuels par status :**
   - `PENDING` : `○` (cercle vide, text-muted)
   - `RUNNING` : `<div class="spinner"></div>`
   - `COMPLETED` : `✅`
   - `ERROR` : `❌`
   - `WAITING_VALIDATION` : `⏸️`

   **Classes CSS par status :**
   - PENDING → `step-card--pending`
   - RUNNING → `step-card--running`
   - COMPLETED → `step-card--completed`
   - ERROR → `step-card--error`
   - WAITING_VALIDATION → `step-card--waiting`

   **Boutons contextuels dans step-card-right :**
   - Si `step.status === 'ERROR'` : bouton `[🔄 Relancer]` → `API.retryStep(sessionId, step.id)` → `loadSession()`
   - Aucun autre bouton dans la step card elle-même

3. **Zone d'action courante (`#mc-action-zone`) :**
   Trouver le step actif = premier step avec status `WAITING_VALIDATION` ou `RUNNING`.

   Si un step est `WAITING_VALIDATION` :
   → Afficher la zone d'action, masquer si aucun step en attente.
   
   Contenu de la zone d'action selon le step :

   **Cas A : `step.requires_validation === 1` et `step.output_type === 'diff'`**
   (Le step propose des modifications de fichiers)
   ```html
   <div class="mc-action-header">
     <h3>⏸️ {step.step_display_name} — Validation requise</h3>
     <p class="text-muted">L'IA propose les modifications suivantes :</p>
   </div>
   <div class="mc-diff-container">
     {renderDiff(step.output_data)}
   </div>
   <div class="mc-validation-form">
     <label>Feedback (optionnel)</label>
     <textarea id="mc-feedback-input" placeholder="Commentaires pour l'IA..." rows="2"></textarea>
     <div class="mc-validation-actions">
       <button id="btn-approve" class="btn-primary">✅ Approuver et continuer</button>
       <button id="btn-reject" class="btn-danger">❌ Rejeter</button>
     </div>
   </div>
   ```

   **Cas B : `step.requires_validation === 1` et `step.output_type !== 'diff'`**
   (Checkpoint humain sans diff)
   ```html
   <div class="mc-action-header">
     <h3>⏸️ {step.step_display_name} — Validation requise</h3>
   </div>
   {si step.output_data : <div class="mc-output-preview">{renderMarkdown(step.output_data)}</div>}
   <div class="mc-validation-form">
     <label>Feedback (optionnel)</label>
     <textarea id="mc-feedback-input" placeholder="Commentaires..." rows="2"></textarea>
     <div class="mc-validation-actions">
       <button id="btn-approve" class="btn-primary">✅ Approuver et continuer</button>
       <button id="btn-reject" class="btn-danger">❌ Rejeter</button>
     </div>
   </div>
   ```

   **Handlers validation :**
   ```js
   // Approuver
   document.getElementById('btn-approve').addEventListener('click', async () => {
     const feedback = document.getElementById('mc-feedback-input').value
     disableValidationButtons()
     try {
       await API.validateStep(sessionId, waitingStep.id, { approved: true, feedback })
       await loadSession()
     } catch(e) {
       showToast(e.message, 'error')
       enableValidationButtons()
     }
   })

   // Rejeter
   document.getElementById('btn-reject').addEventListener('click', async () => {
     const feedback = document.getElementById('mc-feedback-input').value
     if (!feedback.trim()) {
       showToast('Un feedback est requis pour rejeter', 'warning')
       return
     }
     disableValidationButtons()
     try {
       await API.validateStep(sessionId, waitingStep.id, { approved: false, feedback })
       await loadSession()
     } catch(e) {
       showToast(e.message, 'error')
       enableValidationButtons()
     }
   })
   ```

   **Bouton Abandonner :**
   Clic → `showModal("Abandonner le module code ?", "La session sera arrêtée définitivement.", [{label: "Abandonner", type: "danger"}, {label: "Annuler", type: "secondary"}])`
   Confirmation → `API.abortPipeline(sessionId)` → `loadSession()`

4. **Mode HISTORIQUE (session COMPLETED ou ABORTED) :**
   - Pas de polling
   - Zone d'action cachée
   - Bouton Abandonner caché
   - Afficher le coût total récupéré depuis `API.getPipelineCosts(sessionId)`
   - Optionnel : bouton "Retour au projet" → `project.html?id={projectId}`

**CSS spécifique à ajouter dans style.css :**
```
.mc-header : display flex, justify-content space-between, align-items flex-start, margin-bottom 1.5rem, padding-bottom 1rem, border-bottom 1px solid var(--border)
.mc-title : display flex, align-items center, gap 10px, font-size 1.3rem, font-weight 600, margin-bottom 4px
.mc-meta : display flex, align-items center, gap 12px, font-size 0.85rem, color var(--text-muted)
.mc-steps : display flex, flex-direction column, gap 6px, margin-bottom 1.5rem
.step-card : display flex, align-items flex-start, gap 12px, padding 12px 16px, border-radius 8px, border 1px solid var(--border), background var(--bg-card), transition 0.2s
.step-card--running : border-color var(--accent), background rgba(99,102,241,0.05)
.step-card--completed : border-color rgba(34,197,94,0.3)
.step-card--error : border-color rgba(239,68,68,0.3), background rgba(239,68,68,0.05)
.step-card--waiting : border-color rgba(245,158,11,0.4), background rgba(245,158,11,0.05)
.step-card-left : display flex, flex-direction column, align-items center, gap 4px, min-width 32px
.step-indicator : font-size 1.1rem, line-height 1
.step-index : font-size 0.7rem, color var(--text-muted)
.step-card-body : flex 1, min-width 0
.step-name : font-weight 500
.step-meta : font-size 0.8rem, color var(--text-muted), margin-top 2px
.step-output : font-size 0.82rem, color var(--text-muted), margin-top 6px, overflow hidden, text-overflow ellipsis, white-space nowrap
.step-error : font-size 0.82rem, color var(--danger), margin-top 4px
.mc-action-zone : margin-top 0.5rem, padding 1.5rem
.mc-action-header : margin-bottom 1rem
.mc-action-header h3 : font-size 1rem, font-weight 600
.mc-diff-container : max-height 400px, overflow-y auto, margin 1rem 0, border-radius 6px
.mc-output-preview : background var(--bg-input), border-radius 6px, padding 1rem, margin 1rem 0, max-height 300px, overflow-y auto
.mc-validation-form label : font-size 0.85rem, color var(--text-muted), display block, margin-bottom 4px
.mc-validation-form textarea : width 100%, background var(--bg-input), border 1px solid var(--border), border-radius 6px, padding 8px, color var(--text-primary), resize vertical
.mc-validation-actions : display flex, gap 8px, margin-top 12px
```

---

TESTS MANUELS (3 étapes) :

1. Ouvrir une session terminée (COMPLETED) via la sidebar ou l'URL directe →
   Tous les steps s'affichent avec ✅, aucune zone d'action, aucun bouton Abandonner.
   Le coût total s'affiche dans le header.

2. Lancer un nouveau workflow depuis une page projet (Nouveau Module Code → session_start) →
   La page module-code.html s'ouvre, les steps défilent en temps réel (polling toutes 2s).
   Le spinner tourne sur le step en cours.

3. Si un checkpoint de validation est atteint : la zone d'action s'affiche avec les boutons
   ✅ Approuver et ❌ Rejeter. Approuver → le workflow continue, le step passe à COMPLETED,
   le suivant commence. Rejeter sans feedback → toast warning. Rejeter avec feedback → le workflow 
   prend le feedback en compte (comportement backend).

FIN DE MISSION :
- Tests manuels validés
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
