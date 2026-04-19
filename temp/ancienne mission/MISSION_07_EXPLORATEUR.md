# MISSION 07 — Explorateur de Fichiers Droit

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2 — lire entièrement)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Explorateur de fichiers — Panneau droit Windsurf-like

OBJECTIF :
Implémenter le panneau explorateur droit visible depuis les pages projet, chat, et module code.
L'explorateur ressemble à l'explorateur de fichiers de Windsurf/VS Code :
arborescence avec dossiers repliables, clic sur fichier pour voir son contenu.
Il s'affiche automatiquement dès qu'un projet a un dossier local lié (local_path).

PÉRIMÈTRE :
Fichiers à créer :
- frontend/assets/js/explorer.js

Fichiers à modifier (ajouter script explorer.js dans le head) :
- frontend/chat.html
- frontend/project.html
- frontend/module-code.html

Prérequis : Mission 02 terminée.

---

INSTRUCTIONS DÉTAILLÉES :

### frontend/assets/js/explorer.js

Ce fichier expose `window.initExplorer(projectId)` appelé par les pages qui ont un projet.

**Structure HTML injectée dans `#explorer` :**

```html
<div class="explorer-container">
  <div class="explorer-header">
    <span class="explorer-title">📂 Fichiers</span>
    <div class="explorer-header-actions">
      <button id="btn-graphify" class="btn-icon" title="Analyser avec Graphify">🗺️</button>
      <button id="btn-explorer-collapse" class="btn-icon" title="Fermer">→</button>
    </div>
  </div>

  <div class="explorer-path" id="explorer-path">
    <!-- chemin du dossier local -->
  </div>

  <div class="explorer-tree" id="explorer-tree">
    <!-- arborescence générée dynamiquement -->
  </div>

  <div class="explorer-preview" id="explorer-preview" style="display:none">
    <div class="explorer-preview-header">
      <span id="explorer-preview-filename"></span>
      <button id="btn-close-preview" class="btn-icon">✕</button>
    </div>
    <pre id="explorer-preview-content"></pre>
  </div>
</div>
```

**Logique `initExplorer(projectId)` :**

1. Appeler `API.getProject(projectId)` pour obtenir `local_path`
2. Si `local_path` est null ou vide :
   - Injecter dans `#explorer` un message : "Aucun dossier lié. Aller dans le projet pour en ajouter un."
   - Garder `#explorer` avec class `explorer--hidden`
   - Retourner (ne rien faire de plus)

3. Si `local_path` défini :
   - Retirer class `explorer--hidden` de `#explorer`
   - Injecter le HTML de l'explorateur
   - `#explorer-path` → afficher le chemin tronqué (derniers 40 chars si long)
   - Appeler `loadFileTree(projectId)`

**loadFileTree(projectId) :**
1. `const files = await API.listLocalFiles(projectId)`
2. Le backend retourne une liste de chemins relatifs (ex: `["backend/main.py", "frontend/index.html", ...]`)
3. Convertir en arborescence : `buildTree(files)` → objet hiérarchique
4. Rendre l'arborescence dans `#explorer-tree` via `renderTree(tree, container, depth=0)`

**buildTree(paths) :**
Convertit un tableau de chemins en objet arborescent :
```
["backend/main.py", "backend/routers/chat.py", "frontend/index.html"]
→ {
    backend: {
      "main.py": null,
      routers: { "chat.py": null }
    },
    frontend: { "index.html": null }
  }
```

**renderTree(node, container, depth, currentPath='') :**
Pour chaque clé de `node` :
- Si valeur null → c'est un fichier :
  ```html
  <div class="tree-file" data-path="{fullPath}" style="padding-left: {depth*12 + 8}px">
    {icône selon extension} {nom}
  </div>
  ```
- Si valeur objet → c'est un dossier :
  ```html
  <div class="tree-folder">
    <div class="tree-folder-name" style="padding-left: {depth*12}px">
      <span class="tree-folder-arrow">▶</span>
      📁 {nom}
    </div>
    <div class="tree-folder-children" style="display:none">
      {sous-arbre récursif}
    </div>
  </div>
  ```

**Icônes par extension :**
- `.py` → 🐍
- `.js` → 📜
- `.html` → 🌐
- `.css` → 🎨
- `.md` → 📝
- `.json` → `{}`
- `.db`, `.sqlite` → 🗄️
- Autres → 📄

**Interactions arborescence :**

Clic sur `.tree-folder-name` :
→ Toggle class `tree-folder--open` sur `.tree-folder`
→ Toggle flèche : ▶ (fermé) / ▼ (ouvert)
→ Toggle display des `.tree-folder-children` (show/hide)

Clic sur `.tree-file` :
→ Marquer le fichier comme actif (class `tree-file--active`, retirer des autres)
→ Appeler `previewFile(projectId, filePath)`

**previewFile(projectId, filePath) :**
1. `const result = await API.readFile(projectId, filePath)`
2. Afficher `#explorer-preview` (retirer display:none)
3. `#explorer-preview-filename` → nom du fichier uniquement (sans le chemin)
4. `#explorer-preview-content` → `result.content` en texte brut (échapper HTML)
5. Ajouter classe CSS selon extension pour coloration basique si faisable (optionnel)
6. Scroll preview vers le haut

Bouton [✕] dans preview → cacher `#explorer-preview`, désactiver le fichier actif.

**Bouton [→ collapse] :**
Ajouter class `explorer--hidden` sur `#explorer`.
Ajouter un bouton flottant `[📂]` dans le header de la page principale pour rouvrir :
```html
<button id="btn-open-explorer" class="btn-icon explorer-toggle-btn" title="Ouvrir explorateur">📂</button>
```
Ce bouton est injecté dans `.mc-header` / `.chat-header` / `.project-header`.
Clic → retirer `explorer--hidden`, cacher le bouton flottant.

**Bouton [🗺️ Graphify] :**
Pour cette mission : afficher un toast "Graphify — Fonctionnalité à venir" et loguer un `console.log`.
(L'intégration graphify réelle sera une évolution future.)

**Collapse persisté :**
`localStorage.setItem('explorer_hidden', 'true/false')`
Sur init, lire cet état et appliquer.

---

### Pages à modifier

Dans `chat.html`, `project.html`, `module-code.html` :
Ajouter `<script src="assets/js/explorer.js"></script>` AVANT le script de la page.

Les pages `project.js` et `chat.js` appellent déjà (ou doivent appeler) :
```js
const project = await API.getProject(projectId)
if (project.local_path) {
  await initExplorer(projectId)
}
```

Pour `module-code.js` : si `projectId` est défini, appeler `initExplorer(projectId)`.

---

TESTS MANUELS (3 étapes) :

1. Ouvrir un projet qui a un dossier local lié → le panneau explorateur apparaît à droite
   avec l'arborescence complète des fichiers. Les dossiers sont repliables (clic → toggle).

2. Cliquer sur un fichier `.py` ou `.js` → le panneau preview s'ouvre en bas de l'explorateur
   avec le contenu brut du fichier. Le fichier est marqué actif (surligné).
   Cliquer sur [✕] → le preview se ferme.

3. Cliquer sur [→] pour fermer l'explorateur → il se cache, le bouton [📂] apparaît dans le header.
   Recharger la page → l'explorateur reste caché (état persisté). Cliquer [📂] → il se rouvre.

FIN DE MISSION :
- Tests manuels validés
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
