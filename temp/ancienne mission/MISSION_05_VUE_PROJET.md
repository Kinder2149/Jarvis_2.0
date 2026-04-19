# MISSION 05 — Vue Projet

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2 — lire entièrement)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Vue Projet — Hub central

OBJECTIF :
Implémenter la page projet de JARVIS, inspirée de la page "Projet" de Claude.ai.
C'est le hub de chaque projet : on voit les informations du projet, ses instructions,
et toutes ses conversations (chats + modules code) dans une liste unifiée.
C'est depuis ici qu'on lance un nouveau chat ou un nouveau module code dans le projet.

PÉRIMÈTRE :
Fichiers à modifier :
- frontend/project.html  (ajouter le contenu dans #page-project)

Fichiers à créer :
- frontend/assets/js/project.js

Prérequis : Missions 01 + 02 terminées (backend instructions + fondation).

---

INSTRUCTIONS DÉTAILLÉES :

### frontend/project.html

Ajouter dans `#page-project` :

```html
<div id="page-project">

  <!-- Header projet -->
  <div class="project-header">
    <div class="project-header-main">
      <h1 class="project-title" id="project-name">Chargement...</h1>
      <div class="project-path" id="project-path"></div>
    </div>
    <button id="btn-delete-project" class="btn-icon btn-danger-icon" title="Supprimer le projet">🗑️</button>
  </div>

  <!-- Instructions du projet -->
  <div class="project-instructions card" id="instructions-section">
    <div class="card-header">
      <span class="card-label">Instructions du projet</span>
      <button id="btn-edit-instructions" class="btn-icon">✏️</button>
    </div>
    <div id="instructions-display" class="instructions-text"></div>
    <div id="instructions-edit" style="display:none">
      <textarea id="instructions-input" class="instructions-textarea"
        placeholder="Décris ce projet, son contexte, ses règles... Cette instruction sera disponible dans tes chats et modules code."></textarea>
      <div class="instructions-edit-actions">
        <button id="btn-save-instructions" class="btn-primary">💾 Sauvegarder</button>
        <button id="btn-cancel-instructions" class="btn-secondary">Annuler</button>
      </div>
    </div>
  </div>

  <!-- Dossier local lié -->
  <div class="project-local-path card">
    <div class="card-header">
      <span class="card-label">📂 Dossier local lié</span>
      <button id="btn-edit-local-path" class="btn-icon">✏️</button>
    </div>
    <div id="local-path-display"></div>
    <div id="local-path-edit" style="display:none">
      <input type="text" id="local-path-input" class="input-field"
        placeholder="C:\Chemin\vers\le\dossier">
      <div class="local-path-actions">
        <button id="btn-save-local-path" class="btn-primary">💾 Sauvegarder</button>
        <button id="btn-cancel-local-path" class="btn-secondary">Annuler</button>
      </div>
    </div>
  </div>

  <!-- Actions rapides -->
  <div class="project-actions">
    <button id="btn-new-chat" class="btn-primary">✏️ Nouveau Chat</button>
    <button id="btn-new-module" class="btn-secondary">⚡ Nouveau Module Code</button>
  </div>

  <!-- Conversations du projet (liste unifiée) -->
  <div class="project-conversations">
    <h2 class="section-title">Conversations</h2>
    <div id="conversations-list"></div>
  </div>

</div>
```

---

### frontend/assets/js/project.js

**Initialisation :**
```
projectId = getURLParam('id')
```
Si pas de projectId → afficher erreur.

Charger en parallèle :
- `API.getProject(projectId)` → infos projet + session active
- `API.getConversations(projectId)` → conversations chat
- `API.getProjectSessions(projectId)` → sessions modules code

**Rendu infos projet :**
- `#project-name` → `project.name`
- `#project-path` → `project.path` (style text-muted, font-size small)

**Rendu instructions :**
Si `project.instructions` est non vide :
→ `#instructions-display` affiche le texte avec `renderMarkdown(instructions)`
→ Bouton [✏️] bascule en mode édition (hide display, show edit + pré-remplir textarea)

Si `project.instructions` est vide :
→ `#instructions-display` affiche un texte placeholder grisé :
"Aucune instruction définie. Cliquer sur ✏️ pour ajouter le contexte de ce projet."

Mode édition instructions :
→ [💾 Sauvegarder] : `API.updateProject(projectId, {instructions: textarea.value})` → refresh display, `showToast("Instructions sauvegardées")`
→ [Annuler] : retour au mode display sans sauvegarder

**Rendu dossier local lié :**
Si `project.local_path` défini :
→ afficher le chemin + `showToast` si l'explorateur s'est activé
Si vide :
→ afficher "Aucun dossier lié" grisé

Mode édition local_path :
→ [💾 Sauvegarder] : `API.updateProject(projectId, {local_path: input.value})`
→ Après sauvegarde : `EventBus.emit('project:local-path-updated', {projectId, local_path})` pour que l'explorateur se mette à jour
→ Reload de la page pour que l'explorateur s'initialise

**Bouton Nouveau Chat :**
`API.createConversation({project_id: projectId, title: "Nouvelle conversation"})`
→ redirect vers `chat.html?id=X&project_id=Y`

**Bouton Nouveau Module Code :**
Ouvrir modal avec :
- Dropdown `workflow_type` : session_start, session_end, bug_simple, mission_complexe, nouveau_projet, projet_existant
- Textarea `initial_input` placeholder "Contexte initial du workflow..."
- Bouton [⚡ Lancer]

`API.startPipeline({project_id: projectId, workflow_type, initial_input})`
→ redirect vers `module-code.html?session=X&project_id=Y`

**Construction liste conversations unifiée :**
Fusionner conversations chat et sessions module code dans une liste triée par date DESC.
Même logique que le dashboard mais filtrée au projet courant.

Rendu d'un item :
```html
<div class="conversation-item card card--interactive" onclick="navigate">
  <div class="conversation-item-icon">{💬 ou ⚙️}</div>
  <div class="conversation-item-content">
    <div class="conversation-item-title">{titre}</div>
    <div class="conversation-item-meta">
      <span>{formatDate(date)}</span>
      {si module : statusBadge(status)}
      {si module et cost : costBadge(cost)}
      {si chat et preview : <span class="text-muted">{preview 60 chars}</span>}
    </div>
  </div>
  {si chat : <button class="btn-icon btn-delete-conv" title="Supprimer">🗑️</button>}
</div>
```

Clic sur item → navigation vers chat.html ou module-code.html
Clic sur 🗑️ conversation → `showModal` confirmation → `API.deleteConversation(id)` → refresh liste

**Suppression projet :**
Clic 🗑️ en header → modal avec message d'avertissement fort :
"Supprimer le projet '{name}' ? Toutes les conversations et sessions seront perdues définitivement."
Confirmation → `API.deleteProject(projectId)` → redirect vers `index.html`

**Initialiser l'explorateur :**
Si `project.local_path` défini → `initExplorer(projectId)` (fonction de explorer.js)
Retirer la class `explorer--hidden` de `#explorer`

**CSS spécifique à ajouter dans style.css :**
```
.project-header : display flex, justify-content space-between, align-items flex-start, margin-bottom 1.5rem
.project-header-main : flex 1
.project-title : font-size 1.6rem, font-weight 600
.project-path : font-size 0.85rem, color var(--text-muted), margin-top 4px, font-family monospace
.project-instructions, .project-local-path : margin-bottom 1rem
.card-header : display flex, justify-content space-between, align-items center, margin-bottom 8px
.card-label : font-weight 500, font-size 0.9rem
.instructions-text : color var(--text-primary), line-height 1.7, min-height 2rem
.instructions-text:empty::before : content attr(data-placeholder), color var(--text-muted), font-style italic
.instructions-textarea : width 100%, min-height 100px, background var(--bg-input), border 1px solid var(--border), border-radius 6px, padding 10px, color var(--text-primary), font-size 0.9rem, resize vertical
.instructions-textarea:focus : border-color var(--accent), outline none
.instructions-edit-actions, .local-path-actions : display flex, gap 8px, margin-top 8px
.input-field : width 100%, background var(--bg-input), border 1px solid var(--border), border-radius 6px, padding 8px 12px, color var(--text-primary)
.project-actions : display flex, gap 8px, margin-bottom 1.5rem
.project-conversations : margin-top 0.5rem
.conversation-item : display flex, align-items center, gap 12px, padding 12px 16px, margin-bottom 6px, cursor pointer
.conversation-item-icon : font-size 1.1rem, flex-shrink 0
.conversation-item-content : flex 1, min-width 0
.conversation-item-title : font-weight 500, white-space nowrap, overflow hidden, text-overflow ellipsis
.conversation-item-meta : display flex, align-items center, gap 8px, margin-top 2px, font-size 0.8rem, color var(--text-muted)
.btn-danger-icon : hover color var(--danger)
```

---

TESTS MANUELS (3 étapes) :

1. Cliquer sur un projet dans la sidebar → la page projet s'affiche avec le nom,
   le chemin, le champ instructions (vide ou rempli), et la liste des conversations.

2. Cliquer sur [✏️] instructions → textarea apparaît pré-rempli.
   Modifier le texte → [💾 Sauvegarder] → toast "Instructions sauvegardées" + affichage mis à jour.
   Cliquer [Annuler] → retour sans changement.

3. Cliquer [✏️ Nouveau Chat] → modal de sélection workflow OU création directe → redirection vers chat.html
   avec project_id en paramètre URL. Vérifier que le badge projet s'affiche dans le chat.

FIN DE MISSION :
- Tests manuels validés
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
