# FRONT-02 — CTA post-session + retry step Atelier

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

### Problème 1 — Page morte FAILED/ABORTED

Dans `frontend/assets/js/atelier.js`, la fonction `renderPipelineActionZone(session)` :

```js
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

zone.style.display = 'none';  // ← toujours atteint pour FAILED/ABORTED
```

Résultat : si pipeline FAILED ou ABORTED → `zone.style.display = 'none'` → page morte.

### Problème 2 — Pas de retry step

Dans `renderAtlierStepCard(step)`, il n'y a aucun bouton de retry pour les steps en ERROR/FAILED, contrairement à Module Code qui a :
```js
if (step.status === 'ERROR') {
  buttonsHTML = `<button class="btn-icon" onclick="window.retryStep(${step.id})" title="Relancer">🔄</button>`;
}
```

---

## Objectif

1. Ajouter une zone d'action pour FAILED/ABORTED dans `renderPipelineActionZone`
2. Ajouter un bouton retry sur les step cards Atelier en ERROR/FAILED
3. Exposer `window.retryAtelierStep` (utilise la même API : `POST /pipelines/{sessionId}/retry/{stepId}`)

---

## Fichier à modifier

`frontend/assets/js/atelier.js`

---

## Modifications détaillées

### 1. Fonction `renderPipelineActionZone` — ajouter cas FAILED/ABORTED

Remplacer :
```js
zone.style.display = 'none';
```
(la dernière ligne de la fonction, après le bloc COMPLETED) par :

```js
// Cas 3 : session FAILED ou ABORTED → zone d'état
if (['FAILED', 'ABORTED'].includes(session.status)) {
  zone.style.display = 'block';
  const isAborted = session.status === 'ABORTED';
  const emoji = isAborted ? '⛔' : '❌';
  const label = isAborted ? 'Pipeline abandonné' : 'Pipeline échoué';
  zone.innerHTML = `
    <div class="mc-action-header">
      <h3>${emoji} ${label}</h3>
      <p class="text-muted">
        ${isAborted
          ? 'Ce pipeline a été interrompu.'
          : 'Une ou plusieurs étapes ont échoué. Consultez les steps en erreur ci-dessus.'}
      </p>
    </div>
    <div class="mc-validation-actions">
      <button class="btn-secondary" onclick="document.getElementById('btn-back-kanban').click()">← Retour kanban</button>
    </div>
  `;
  return;
}

zone.style.display = 'none';
```

### 2. Fonction `renderAtlierStepCard` — ajouter bouton retry

Dans la fonction `renderAtlierStepCard(step)`, après la définition de `errorHTML`, ajouter :

```js
let retryBtnHTML = '';
if (step.status === 'FAILED' || step.status === 'ERROR') {
  retryBtnHTML = `
    <div class="step-card-right">
      <button class="btn-icon" onclick="window.retryAtelierStep(${step.id})" title="Relancer ce step">🔄</button>
    </div>
  `;
}
```

Et dans le template HTML retourné, ajouter `${retryBtnHTML}` avant la fermeture du `</div>` principal de la card.

Le template complet devient :
```js
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
    ${retryBtnHTML}
  </div>
`;
```

### 3. Exposer `window.retryAtelierStep`

Ajouter à la fin du module (avant `window.addEventListener('beforeunload', stopPolling)`) :

```js
window.retryAtelierStep = async function(stepId) {
  if (!currentSessionId) {
    window.showToast && window.showToast('Session non trouvée', 'error');
    return;
  }
  try {
    await window.API.retryStep(currentSessionId, stepId);
    window.showToast && window.showToast('Step relancé');
    await showPipelineView(currentProspectId);
    startPolling();
  } catch (err) {
    window.showToast && window.showToast(err.message || 'Erreur relance', 'error');
  }
};
```

---

## Tests manuels

1. Aller sur un prospect Atelier → lancer le pipeline → l'abandonner avec "⛔ Abandonner"
2. **Page ABORTED** : zone doit afficher "⛔ Pipeline abandonné" + bouton "← Retour kanban"
3. Cliquer "← Retour kanban" → retour vers atelier.html kanban ✓
4. Simuler un step en FAILED (ou vérifier s'il en existe un) → bouton 🔄 doit apparaître sur la step card
5. Cliquer 🔄 → step relancé → polling redémarre ✓
6. Vérifier que le flow normal (form → checkpoint → export) n'est pas affecté

---

## FIN DE MISSION

- [ ] Build OK
- [ ] Test manuel : ABORTED affiche zone, FAILED affiche zone avec retry sur steps
- [ ] Flow normal non régressé (form saisie, checkpoint, export)
- [ ] PROJET_CONTEXTE.md section 8 et CHANGELOG.md mis à jour
