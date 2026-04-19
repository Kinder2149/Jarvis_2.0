# MISSION 09 — Audit & Corrections Frontend V2

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Audit et corrections Frontend V2

OBJECTIF :
Auditer et corriger le frontend V2 JARVIS avant les tests automatiques.
Des bugs ont été identifiés par analyse statique du code. Corriger chacun,
puis vérifier l'ensemble des fichiers pour détecter d'autres incohérences.

PÉRIMÈTRE :
Fichiers à modifier :
- frontend/assets/js/sidebar.js
- frontend/assets/js/module-code.js
- frontend/assets/style.css
- frontend/assets/js/shared.js (si nécessaire)
- frontend/assets/js/explorer.js (si nécessaire)
- frontend/assets/js/project.js (si nécessaire)

Fichiers à supprimer :
- frontend/pipeline.html (ancienne page, app.js supprimé = crash garanti)

---

## CORRECTIONS OBLIGATOIRES

### BUG 1 — CRITIQUE : Mauvais parsing de la réponse startPipeline
Fichier : frontend/assets/js/sidebar.js, fonction handleNewModule()

**Problème :**
`POST /api/pipelines/start` retourne `{"session": {...}, "execution_result": {...}}`.
Le code actuel fait `session.id` mais `session` ici est l'objet entier de la réponse,
donc `session.id` vaut `undefined` et l'URL de redirection est cassée.

**Correction dans handleNewModule() :**
```js
// AVANT (cassé) :
const session = await window.API.startPipeline({...})
window.location.href = `module-code.html?session=${session.id}&project_id=${projectId}`;

// APRÈS (correct) :
const result = await window.API.startPipeline({...})
const sessionId = result.session?.id || result.id;
if (!sessionId) throw new Error('Session ID non trouvé dans la réponse');
window.location.href = `module-code.html?session=${sessionId}&project_id=${projectId}`;
```

Appliquer la même correction dans `project.js` si le bouton "Nouveau Module Code"
y fait aussi un appel à `API.startPipeline()`.

---

### BUG 2 — CRITIQUE : Diff renderer incorrect dans module-code
Fichier : frontend/assets/js/module-code.js, fonction renderDiffValidation()

**Problème :**
Le code utilise `renderMarkdown(step.output_data)` pour afficher un diff.
`renderMarkdown` transforme les `+` en balises HTML incorrectes.
Il faut utiliser `window.renderDiff()` qui est conçu pour ça.

**Correction dans renderDiffValidation() :**
```js
// AVANT (cassé) :
const diffContent = typeof step.output_data === 'string' 
  ? renderMarkdown(step.output_data) 
  : JSON.stringify(step.output_data, null, 2);

// APRÈS (correct) :
const renderDiffFn = window.renderDiff || ((text) => `<pre>${text}</pre>`);
const diffContent = typeof step.output_data === 'string'
  ? renderDiffFn(step.output_data)
  : `<pre>${JSON.stringify(step.output_data, null, 2)}</pre>`;
```

---

### BUG 3 — MOYEN : Polling ne démarre pas pour status 'CREATED'
Fichier : frontend/assets/js/module-code.js, fonction loadSession()

**Problème :**
La condition de démarrage du polling est :
`if (['RUNNING', 'WAITING', 'PENDING'].includes(session.status))`
Mais une session peut avoir status `'CREATED'` après startPipeline.
Résultat : le polling ne démarre pas et la page reste figée.

**Correction :**
```js
// AVANT :
if (['RUNNING', 'WAITING', 'PENDING'].includes(session.status)) {
  startPolling();
}

// APRÈS :
const ACTIVE_STATUSES = ['CREATED', 'RUNNING', 'WAITING', 'PENDING', 'WAITING_VALIDATION'];
if (ACTIVE_STATUSES.includes(session.status)) {
  startPolling();
} else if (['COMPLETED', 'ABORTED', 'ERROR'].includes(session.status)) {
  stopPolling();
}
```

Même correction pour la condition de stopPolling dans l'intervalle du polling :
```js
// Dans setInterval :
if (['COMPLETED', 'ABORTED', 'ERROR'].includes(session.status)) {
  stopPolling();
}
```
Vérifier que cette condition est déjà complète (ne manque pas 'ABORTED').

---

### BUG 4 — MOYEN : pipeline.html référençait app.js (supprimé)
Action : **Supprimer** `frontend/pipeline.html`.
Ce fichier est l'ancienne implémentation remplacée par `module-code.html`.
`app.js` a été supprimé en Mission 08, donc `pipeline.html` crashe à l'ouverture.
Si un lien vers `pipeline.html` existe quelque part (dans d'autres HTML, dans le backend),
le remplacer par `module-code.html`.

Vérifier dans tous les fichiers HTML + backend/main.py si "pipeline.html" est référencé.

---

## AUDIT GÉNÉRAL — Vérifications supplémentaires

Après avoir corrigé les 4 bugs ci-dessus, effectuer ces vérifications :

### 1. Vérifier les IDs HTML dans chaque page HTML
Chaque JS attend des éléments HTML avec des IDs précis. Vérifier que chaque HTML contient bien
les IDs que son JS tente de lire/modifier.

Checklist :
- `index.html` contient : `#dashboard-subtitle`, `#active-pipeline-section`, `#active-pipeline-list`, `#activity-timeline`, `#dashboard-stats`
- `chat.html` contient : `#chat-title`, `#chat-project-badge`, `#chat-messages`, `#chat-input`, `#btn-send`, `#btn-delete-conversation`
- `project.html` contient : `#project-name`, `#project-path`, `#instructions-display`, `#instructions-edit`, `#instructions-input`, `#btn-edit-instructions`, `#btn-save-instructions`, `#btn-cancel-instructions`, `#local-path-display`, `#local-path-edit`, `#local-path-input`, `#btn-edit-local-path`, `#btn-save-local-path`, `#btn-cancel-local-path`, `#conversations-list`, `#btn-new-chat`, `#btn-new-module`, `#btn-delete-project`
- `module-code.html` contient : `#mc-workflow-type`, `#mc-status-badge`, `#mc-project-link`, `#mc-start-time`, `#mc-total-cost`, `#btn-abort`, `#mc-steps-list`, `#mc-action-zone`
- `settings.html` contient : `#key-display-openrouter`, `#key-display-anthropic`, `#key-display-google`, `#badge-openrouter`, `#badge-anthropic`, `#badge-google`, `#model-routing`, `#model-code`, `#model-analysis`, `#btn-save-models`

Corriger tout ID manquant dans le HTML correspondant.

### 2. Vérifier le CSS sidebar collapse
Vérifier que `style.css` contient ces règles CSS :
```css
.sidebar--collapsed .sidebar-text { display: none !important; }
.sidebar--collapsed .sidebar-collapsed-text { display: inline !important; }
```
Si absent, les ajouter. Sans ces règles, le collapse sidebar ne cache pas les textes via CSS.

### 3. Vérifier l'initialisation de l'explorateur dans project.js
Chercher la fonction `initializeExplorer()` dans `project.js`.
Elle doit faire :
```js
function initializeExplorer() {
  if (project.local_path && window.initExplorer) {
    window.initExplorer(projectId);
  }
}
```
Si elle est absente ou incorrecte, la corriger.

### 4. Vérifier que l'explorateur retire bien la classe explorer--hidden
Dans `explorer.js`, la fonction `initExplorer()` doit faire :
```js
document.getElementById('explorer').classList.remove('explorer--hidden');
```
Vérifier que c'est bien présent.

### 5. Vérifier que settings.js gère bien la structure de retour de getConfig()
`GET /api/config/` retourne une structure avec les clés API masquées.
Vérifier dans le code réel (`backend/routers/models.py` ou `backend/routers/config.py`)
la structure exacte retournée et s'assurer que `settings.js` utilise les bons noms de champs.
Les noms peuvent être `openrouter_api_key`, `openrouter_key`, etc. — aligner settings.js.

### 6. Vérifier que les boutons test connexion utilisent le bon format
`POST /api/config/test` attend `{"provider": "openrouter"|"anthropic"|"google"}`.
Vérifier que settings.js envoie bien ce format (pas `{"provider": "openrouter_api_key"}` etc.).

### 7. Vérifier que chat.js a la fonction escapeHtml définie
`chat.js` utilise `escapeHtml(msg.content)` pour les messages user.
Vérifier que cette fonction est définie dans `chat.js` ou dans `shared.js`.
Si absente, l'ajouter :
```js
function escapeHtml(text) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}
```

### 8. Vérifier le retour de startPipeline dans project.js
Dans `project.js`, le bouton "Nouveau Module Code" fait appel à `API.startPipeline()`.
Vérifier que la réponse est parsée comme `result.session.id` (pas `result.id`),
cohérent avec la correction du Bug 1.

---

## APRÈS LES CORRECTIONS

Après toutes les corrections, rédiger un rapport concis :
```
CORRECTIONS APPLIQUÉES :
- Bug 1 : [décrit ce qui a été corrigé]
- Bug 2 : [décrit ce qui a été corrigé]
- Bug 3 : [décrit ce qui a été corrigé]
- Bug 4 : [pipeline.html supprimé / liens mis à jour]

VÉRIFICATIONS AUDIT :
- IDs HTML : [OK / problèmes trouvés et corrigés]
- CSS sidebar : [OK / ajouté]
- Explorer init : [OK / corrigé]
- escapeHtml : [OK / ajouté]
- Config/settings : [structure API confirmée]

PROBLÈMES SUPPLÉMENTAIRES TROUVÉS ET CORRIGÉS : [liste]
```

FIN DE MISSION :
- Serveur redémarre sans erreur
- Aucun fichier JS de référence croisée manquante
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
