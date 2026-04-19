# FRONT-06 — project.html : lancement sans friction

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Dans `frontend/project.html`, deux boutons d'action :

```html
<button id="btn-new-chat" class="btn-primary">✏️ Nouveau Chat</button>
<button id="btn-new-module" class="btn-secondary">⚡ Nouveau Module Code</button>
```

Dans `frontend/assets/js/project.js`, ces boutons appellent les handlers de `sidebar.js` :
- `btn-new-chat` → `handleNewChat()` → **ouvre une modal avec sélection de projet**
- `btn-new-module` → `handleNewModule()` → **ouvre une modal avec sélection de projet + workflow**

Les deux redemandent de choisir un projet alors qu'on est DÉJÀ sur la page projet. C'est du friction inutile.

De plus, dans `project.js`, les sessions et conversations sont dans une liste unifiée nommée "Conversations" — le titre est trompeur puisque les sessions Module Code ne sont pas des conversations.

---

## Objectif

1. **"Nouveau Chat"** depuis project.html → créer directement sans modal (projet courant est connu)
2. **"Nouveau Module Code"** depuis project.html → ouvrir modal avec projet pré-rempli + désactivé
3. **Renommer** la section "Conversations" en "Activité du projet" pour être précis

---

## Fichiers à modifier

1. `frontend/assets/js/project.js`
2. `frontend/project.html` (renommage titre section)

---

## Modifications détaillées

### 1. `project.js` — handler "Nouveau Chat" direct

Dans la fonction `attachEventListeners()`, remplacer le handler `btn-new-chat` :

**Avant (appel sidebar) :**
```js
document.getElementById('btn-new-chat')?.addEventListener('click', () => {
  if (window.handleNewChat) window.handleNewChat();
});
```

**Après (création directe) :**
```js
document.getElementById('btn-new-chat')?.addEventListener('click', async () => {
  try {
    const conv = await window.API.createConversation({
      project_id: parseInt(projectId),
      title: 'Nouvelle conversation'
    });
    window.location.href = `chat.html?id=${conv.id}&project_id=${projectId}`;
  } catch (error) {
    if (window.showToast) window.showToast(error.message, 'error');
  }
});
```

### 2. `project.js` — handler "Nouveau Module Code" pré-rempli

Remplacer le handler `btn-new-module` :

**Avant :**
```js
document.getElementById('btn-new-module')?.addEventListener('click', () => {
  if (window.handleNewModule) window.handleNewModule();
});
```

**Après :**
```js
document.getElementById('btn-new-module')?.addEventListener('click', () => {
  if (window.handleNewModulePreset) {
    window.handleNewModulePreset(projectId, null);
  } else if (window.handleNewModule) {
    window.handleNewModule();
  }
});
```

`handleNewModulePreset` a été ajouté dans `sidebar.js` par la mission FRONT-01. Il ouvre une modal avec le projet pré-sélectionné et désactivé.

**Prérequis :** FRONT-01 doit être terminé.

### 3. `project.html` — renommer titre section

Dans `frontend/project.html`, remplacer :
```html
<div class="project-conversations">
  <h2 class="section-title">Conversations</h2>
```
Par :
```html
<div class="project-conversations">
  <h2 class="section-title">Activité du projet</h2>
```

### 4. `project.js` — améliorer les labels de la liste unifiée

Dans `renderConversationItem()` (ou la fonction qui rend chaque item), s'assurer que :
- Les items type `chat` affichent un badge "Chat"
- Les items type `module` affichent le `workflow_type` et un badge statut coloré

Vérifier que la fonction existante `renderConversationItem` fait déjà ça — si pas, ajouter les badges.

---

## Tests manuels

1. Aller sur project.html?id=X
2. Cliquer "✏️ Nouveau Chat" → **pas de modal** → redirige directement vers chat.html?id=NEW&project_id=X ✓
3. Cliquer "⚡ Nouveau Module Code" → modal s'ouvre → projet PRÉ-REMPLI et grisé (non modifiable), workflow dropdown avec descriptions (FRONT-01), textarea demande ✓
4. Saisir une demande → cliquer Lancer → redirect vers module-code.html ✓
5. La section s'appelle "Activité du projet" ✓
6. Les items de la liste distinguent visuellement chat vs module code ✓

---

## FIN DE MISSION

- [ ] Build OK
- [ ] "Nouveau Chat" depuis project.html = 0 modal, direct
- [ ] "Nouveau Module Code" depuis project.html = projet pré-rempli
- [ ] Section renommée "Activité du projet"
- [ ] PROJET_CONTEXTE.md section 8 et CHANGELOG.md mis à jour
