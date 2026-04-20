# FIX-03 — Module Code : statut FAILED visible + logs d'erreur utilisateur

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Quand une étape de pipeline échoue, le backend écrit le statut `FAILED` et stocke le message d'erreur
dans `error_message`. Mais le frontend `module-code.js` ne gère pas `FAILED` — il ne gère que `ERROR`.

Résultat visible par l'utilisateur :
- La session s'arrête
- Les cartes des étapes n'ont aucune couleur d'erreur (fond gris neutre comme PENDING)
- Aucun message d'erreur affiché sur la carte
- L'utilisateur ne sait pas ce qui a échoué ni pourquoi

Deux fonctions sont incomplètes :
- `getStepStatusClass()` : pas de mapping pour `FAILED`
- `getStepIndicator()` : pas de mapping pour `FAILED`
- `renderStepCard()` : affiche `errorHTML` uniquement si `step.status === 'ERROR'`

---

## Objectif

Traiter `FAILED` exactement comme `ERROR` dans toute l'interface du Module Code.
Afficher clairement le message d'erreur sur la carte de l'étape concernée.

---

## Fichier à modifier : `frontend/assets/js/module-code.js`

### Modification 1 — `getStepStatusClass()`

Chercher le bloc exact :
```javascript
  function getStepStatusClass(status) {
    const map = {
      'PENDING': 'step-card--pending',
      'RUNNING': 'step-card--running',
      'COMPLETED': 'step-card--completed',
      'ERROR': 'step-card--error',
      'WAITING_VALIDATION': 'step-card--waiting'
    };
    return map[status] || '';
  }
```

Remplacer par :
```javascript
  function getStepStatusClass(status) {
    const map = {
      'PENDING': 'step-card--pending',
      'RUNNING': 'step-card--running',
      'COMPLETED': 'step-card--completed',
      'ERROR': 'step-card--error',
      'FAILED': 'step-card--error',
      'WAITING_VALIDATION': 'step-card--waiting'
    };
    return map[status] || '';
  }
```

---

### Modification 2 — `getStepIndicator()`

Chercher le bloc exact :
```javascript
  function getStepIndicator(status) {
    const map = {
      'PENDING': '<span style="color:var(--text-muted)">○</span>',
      'RUNNING': '<div class="spinner"></div>',
```

Le bloc complet se termine par un `return map[status] || '○';`.

Ajouter `'FAILED'` dans ce map, juste après la ligne `'ERROR'` :
```javascript
      'FAILED': '<span style="color:var(--danger)">✕</span>',
```

---

### Modification 3 — `renderStepCard()` : afficher l'erreur pour FAILED aussi

Chercher le bloc exact :
```javascript
    let errorHTML = '';
    if (step.status === 'ERROR' && step.error_message) {
      errorHTML = `<div class="step-error">❌ ${step.error_message}</div>`;
    }

    let buttonsHTML = '';
    if (step.status === 'ERROR') {
      buttonsHTML = `<button class="btn-icon" onclick="window.retryStep(${step.id})" title="Relancer">🔄</button>`;
    }
```

Remplacer par :
```javascript
    let errorHTML = '';
    if ((step.status === 'ERROR' || step.status === 'FAILED') && step.error_message) {
      errorHTML = `<div class="step-error">❌ ${step.error_message}</div>`;
    }

    let buttonsHTML = '';
    if (step.status === 'ERROR' || step.status === 'FAILED') {
      buttonsHTML = `<button class="btn-icon" onclick="window.retryStep(${step.id})" title="Relancer">🔄</button>`;
    }
```

---

### Modification 4 — Zone d'action session FAILED : afficher le détail de l'erreur

Dans `renderActionZone()`, chercher le bloc qui construit le HTML pour les sessions terminales.
Actuellement pour `FAILED` il affiche juste "Session échouée" sans détail.

Chercher la ligne :
```javascript
      const isSuccess = session.status === 'COMPLETED';
```

Juste après le bloc `actionZone.innerHTML = ...` (après le `return;` final de la branche terminal),
**avant** ce `return`, ajouter la recherche de l'étape en échec pour afficher son message.

Modifier le bloc `actionZone.innerHTML` pour les sessions FAILED. Chercher :
```javascript
      actionZone.innerHTML = `
        <div class="mc-action-header">
          <h3>${emoji} ${label}</h3>
        </div>
        <div class="mc-validation-actions">
          ${backBtn}
          ${relanceBtn}
          ${nouvelleBtn}
          ${deleteBtn}
        </div>
      `;
```

Remplacer par :
```javascript
      // Chercher l'étape en échec pour afficher son message d'erreur
      const failedStep = session.steps?.find(s => s.status === 'FAILED' || s.status === 'ERROR');
      const errorDetail = failedStep?.error_message
        ? `<div class="mc-error-detail">
             <strong>Étape échouée :</strong> ${failedStep.step_display_name || failedStep.step_type}<br>
             <code>${failedStep.error_message}</code>
           </div>`
        : '';

      actionZone.innerHTML = `
        <div class="mc-action-header">
          <h3>${emoji} ${label}</h3>
          ${errorDetail}
        </div>
        <div class="mc-validation-actions">
          ${backBtn}
          ${relanceBtn}
          ${nouvelleBtn}
          ${deleteBtn}
        </div>
      `;
```

---

### Modification 5 — CSS : style pour `.mc-error-detail`

Chercher dans `frontend/assets/css/module-code.css` (ou le fichier CSS principal si le style du module
code est dans `main.css`) la section des styles du module code.

Ajouter à la fin de cette section :
```css
.mc-error-detail {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(166, 72, 72, 0.12);
  border-left: 3px solid var(--danger);
  border-radius: 0 4px 4px 0;
  font-size: 0.85rem;
  color: var(--text-main);
  word-break: break-word;
}

.mc-error-detail code {
  display: block;
  margin-top: 0.4rem;
  font-family: monospace;
  font-size: 0.82rem;
  color: var(--danger);
  white-space: pre-wrap;
}
```

---

## Ce qu'on ne touche pas

- `backend/services/pipeline_engine.py` — le backend écrit bien le message dans `error_message`, c'est correct
- Les routes API — aucune modification
- La logique de retry — elle fonctionne déjà pour `ERROR`, elle marchera aussi pour `FAILED` après ce fix
- Les autres pages frontend (chat, atelier, settings)

---

## Test manuel (3 étapes)

1. Lancer un workflow `mission_complexe` sur un projet qui a un chemin invalide ou une clé API vide
   → la session doit échouer → les étapes en échec doivent apparaître en rouge avec le message d'erreur
   visible sur la carte

2. Dans la zone d'action en bas (qui affiche "Session échouée"), le message d'erreur de l'étape
   concernée doit apparaître avec le nom de l'étape et le détail de l'erreur

3. Le bouton 🔄 "Relancer" doit apparaître sur la carte de l'étape FAILED (comme pour ERROR)

---

## FIN DE MISSION

- [ ] Build sans erreur
- [ ] Test manuel 3 étapes validé
- [ ] `getStepStatusClass()` : FAILED → même classe CSS que ERROR
- [ ] `getStepIndicator()` : FAILED → icône ✕ rouge
- [ ] `renderStepCard()` : message d'erreur affiché pour FAILED
- [ ] `renderActionZone()` : détail de l'étape échouée visible
- [ ] Style `.mc-error-detail` ajouté
- [ ] Aucun fichier créé hors périmètre
- [ ] Aucune dépendance ajoutée
