# MISSION 08 — Paramètres

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2 — lire entièrement)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Paramètres — Configuration clés API et modèles

OBJECTIF :
Implémenter la page de configuration de JARVIS.
Elle est rarement utilisée (configuration initiale + changements occasionnels).
Elle doit être simple, fonctionnelle, avec des états visuels clairs :
- Clé définie → afficher masqué + œil pour révéler + bouton modifier
- Clé non définie → indiquer clairement + bouton configurer
- Test connexion → badge vert/rouge instantané
- Modèles → dropdowns alimentés depuis le backend
À la fin de cette mission, supprimer `frontend/assets/app.js` (remplacé par les modules V2).

PÉRIMÈTRE :
Fichiers à modifier :
- frontend/settings.html  (ajouter le contenu dans #page-settings)

Fichiers à créer :
- frontend/assets/js/settings.js

Fichiers à supprimer :
- frontend/assets/app.js  (contenu migré dans api.js, shared.js, ui.js)

Prérequis : Mission 02 terminée.

---

INSTRUCTIONS DÉTAILLÉES :

### frontend/settings.html

Ajouter dans `#page-settings` :

```html
<div id="page-settings">

  <div class="settings-header">
    <h1>⚙️ Paramètres</h1>
    <p class="text-muted">Configuration de JARVIS. Les clés API ne sont jamais transmises à l'extérieur.</p>
  </div>

  <!-- Section Clés API -->
  <div class="settings-section card">
    <h2 class="settings-section-title">Clés API</h2>

    <!-- OpenRouter -->
    <div class="api-key-row" id="key-row-openrouter">
      <div class="api-key-info">
        <span class="api-key-provider">OpenRouter</span>
        <span class="api-key-description text-muted">Modèles Google, Anthropic via OpenRouter</span>
      </div>
      <div class="api-key-controls">
        <div class="api-key-value-group" id="key-display-openrouter">
          <!-- Rendu par settings.js -->
        </div>
        <button class="btn-test-connection" data-provider="openrouter">Tester</button>
        <span class="connection-badge" id="badge-openrouter"></span>
      </div>
    </div>

    <!-- Anthropic -->
    <div class="api-key-row" id="key-row-anthropic">
      <div class="api-key-info">
        <span class="api-key-provider">Anthropic</span>
        <span class="api-key-description text-muted">Accès direct API Claude</span>
      </div>
      <div class="api-key-controls">
        <div class="api-key-value-group" id="key-display-anthropic"></div>
        <button class="btn-test-connection" data-provider="anthropic">Tester</button>
        <span class="connection-badge" id="badge-anthropic"></span>
      </div>
    </div>

    <!-- Google -->
    <div class="api-key-row" id="key-row-google">
      <div class="api-key-info">
        <span class="api-key-provider">Google</span>
        <span class="api-key-description text-muted">Accès direct API Gemini</span>
      </div>
      <div class="api-key-controls">
        <div class="api-key-value-group" id="key-display-google"></div>
        <button class="btn-test-connection" data-provider="google">Tester</button>
        <span class="connection-badge" id="badge-google"></span>
      </div>
    </div>
  </div>

  <!-- Section Modèles -->
  <div class="settings-section card" id="models-section">
    <h2 class="settings-section-title">Modèles par type</h2>
    <p class="text-muted settings-section-desc">
      JARVIS choisit automatiquement le modèle selon le type de tâche.
    </p>

    <div class="model-row">
      <div class="model-info">
        <span class="model-label">Routage / Décision</span>
        <span class="text-muted model-desc">Choix du prochain step, décisions rapides</span>
      </div>
      <select id="model-routing" class="model-select"></select>
    </div>

    <div class="model-row">
      <div class="model-info">
        <span class="model-label">Code / Analyse</span>
        <span class="text-muted model-desc">Génération de code, analyse de fichiers</span>
      </div>
      <select id="model-code" class="model-select"></select>
    </div>

    <div class="model-row">
      <div class="model-info">
        <span class="model-label">Missions complexes</span>
        <span class="text-muted model-desc">Raisonnement long, missions critiques</span>
      </div>
      <select id="model-analysis" class="model-select"></select>
    </div>

    <div class="models-actions">
      <button id="btn-save-models" class="btn-primary">💾 Sauvegarder les modèles</button>
    </div>
  </div>

</div>
```

---

### frontend/assets/js/settings.js

**Initialisation :**
Charger en parallèle :
- `API.getConfig()` → retourne `{openrouter_api_key: "...xxxx", anthropic_api_key: "...xxxx", google_api_key: "...xxxx", models: {routing: ..., code: ..., analysis: ...}}`
- `API.getAvailableModels()` → liste des modèles disponibles

Puis : `renderApiKeys(config)` + `renderModelSelects(models, config.models)`

**renderApiKey(provider, maskedValue, containerId) :**

Cas 1 — Clé définie (maskedValue non null et non vide) :
```html
<div class="key-defined-state">
  <span class="key-masked" id="key-val-{provider}">●●●●●●●●●●</span>
  <button class="btn-icon btn-reveal" data-provider="{provider}" title="Révéler">👁️</button>
  <button class="btn-secondary btn-sm btn-edit-key" data-provider="{provider}">✏️ Modifier</button>
  <span class="key-status-ok">✅ Configurée</span>
</div>
```

Clic [👁️] : toggle entre afficher "●●●●●●●●●●" et la valeur masquée réelle (ex: "sk-or-...xxxx")
→ L'œil alterne entre 👁️ (caché) et 🙈 (révélé)

Clic [✏️ Modifier] : remplacer le `.key-defined-state` par le formulaire d'édition (Cas 3 ci-dessous)

Cas 2 — Clé non définie (maskedValue null ou vide) :
```html
<div class="key-undefined-state">
  <span class="key-status-missing">⚠️ Non configurée</span>
  <button class="btn-primary btn-sm btn-set-key" data-provider="{provider}">+ Configurer</button>
</div>
```

Clic [+ Configurer] : afficher formulaire d'édition

Cas 3 — Formulaire d'édition (commun) :
```html
<div class="key-edit-state">
  <input type="password" class="input-field key-input" id="key-input-{provider}"
    placeholder="Coller la clé API ici...">
  <button class="btn-icon btn-reveal-input" data-provider="{provider}">👁️</button>
  <button class="btn-primary btn-sm btn-save-key" data-provider="{provider}">💾 Sauvegarder</button>
  <button class="btn-secondary btn-sm btn-cancel-key" data-provider="{provider}">Annuler</button>
</div>
```

[👁️] sur l'input → toggle type="password" / type="text"
[💾 Sauvegarder] :
```js
const keyValue = document.getElementById(`key-input-${provider}`).value.trim()
if (!keyValue) { showToast('Clé vide', 'warning'); return }
await API.saveConfig({ [`${provider}_api_key`]: keyValue })
showToast('Clé sauvegardée', 'success')
// Re-charger config et re-rendre cette ligne
```
[Annuler] : retour à l'état précédent (définie ou non définie)

**Test connexion :**
Chaque bouton [Tester] data-provider={provider} :
1. Afficher spinner dans le badge : `<div class="spinner spinner--sm"></div>`
2. `await API.testConnection({provider})`
3. Si succès : `<span class="badge badge--success">✅ OK</span>`
4. Si erreur : `<span class="badge badge--error">❌ Échec</span>` + showToast(erreur, 'error')

**renderModelSelects(availableModels, currentModels) :**
`availableModels` est un objet `{routing: [...], code: [...], analysis: [...]}` ou une liste plate.
Adapter selon ce que retourne `GET /config/models/available`.

Pour chaque select (routing, code, analysis) :
- Remplir avec les options disponibles
- Sélectionner la valeur courante (`currentModels.routing`, etc.)

[💾 Sauvegarder les modèles] :
```js
const models = {
  routing: document.getElementById('model-routing').value,
  code: document.getElementById('model-code').value,
  analysis: document.getElementById('model-analysis').value,
}
await API.saveConfig({ models })
showToast('Modèles sauvegardés', 'success')
```

**CSS spécifique à ajouter dans style.css :**
```
.settings-header : margin-bottom 2rem
.settings-section : margin-bottom 1.5rem, padding 1.5rem
.settings-section-title : font-size 1rem, font-weight 600, margin-bottom 1rem, padding-bottom 0.5rem, border-bottom 1px solid var(--border)
.settings-section-desc : font-size 0.85rem, margin-bottom 1rem, margin-top -0.5rem
.api-key-row : display flex, justify-content space-between, align-items center, padding 12px 0, border-bottom 1px solid var(--border), gap 16px
.api-key-row:last-child : border-bottom none
.api-key-info : flex 1
.api-key-provider : font-weight 500, display block
.api-key-description : font-size 0.82rem, display block, margin-top 2px
.api-key-controls : display flex, align-items center, gap 8px, flex-shrink 0
.key-masked : font-family monospace, letter-spacing 2px, color var(--text-muted)
.key-status-ok : font-size 0.82rem, color var(--success)
.key-status-missing : font-size 0.82rem, color var(--warning)
.key-input : width 240px
.btn-reveal, .btn-reveal-input : font-size 0.9rem, padding 4px
.connection-badge : min-width 24px
.model-row : display flex, justify-content space-between, align-items center, padding 10px 0, border-bottom 1px solid var(--border), gap 16px
.model-row:last-of-type : border-bottom none
.model-info : flex 1
.model-label : font-weight 500, display block
.model-desc : font-size 0.82rem, display block
.model-select : background var(--bg-input), border 1px solid var(--border), border-radius 6px, padding 6px 10px, color var(--text-primary), min-width 200px
.model-select:focus : border-color var(--accent), outline none
.models-actions : margin-top 1rem, display flex, justify-content flex-end
.btn-sm : padding 4px 10px, font-size 0.82rem
.spinner--sm : width 12px, height 12px, border-width 1.5px
```

---

### Suppression app.js

Après avoir vérifié que :
1. Toutes les pages chargent api.js + shared.js + ui.js à la place de app.js
2. Aucune page ne référence encore app.js dans une balise `<script>`

→ Supprimer `frontend/assets/app.js`

Si une référence reste dans une page HTML → la retirer dans cette mission.

---

TESTS MANUELS (3 étapes) :

1. Ouvrir http://localhost:8000/app/settings.html → la page s'affiche.
   Les 3 providers s'affichent avec leur état : clé configurée → "●●●●●●●●●● ✅ Configurée",
   clé manquante → "⚠️ Non configurée".

2. Cliquer [👁️] sur une clé configurée → "sk-or-...xxxx" s'affiche.
   Cliquer [✏️ Modifier] → formulaire input apparaît. Taper une nouvelle valeur → [💾 Sauvegarder]
   → toast "Clé sauvegardée" → retour à l'état "configurée".

3. Cliquer [Tester] sur un provider configuré → spinner → badge vert ✅ OK.
   Les dropdowns de modèles sont remplis avec les modèles disponibles.
   Modifier un modèle → [💾 Sauvegarder les modèles] → toast "Modèles sauvegardés".

FIN DE MISSION :
- Tests manuels validés
- app.js supprimé, aucune erreur JS console
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
