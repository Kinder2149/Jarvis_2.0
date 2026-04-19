# MISSION 11 — UX Complet : Navigation, Gestion, Modèle Chat

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : UX Complet — 6 corrections d'expérience utilisateur

OBJECTIF :
Corriger 6 lacunes UX identifiées sur le frontend V2 en production :
1. Clic projet sidebar → ne navigue pas vers la vue projet
2. Pas de retour au dashboard
3. Pas de création de projet depuis l'UI
4. Pas de gestion des conversations (renommer, supprimer) dans la sidebar
5. Pas de sélecteur de modèle dans le chat
6. CSS cassé sur les labels de modèles dans les paramètres

PÉRIMÈTRE :
Backend — 1 fichier à modifier :
- backend/routers/chat.py  (ajouter endpoint PATCH /chat/conversations/{id})

Frontend — fichiers à modifier :
- frontend/assets/js/sidebar.js
- frontend/assets/js/api.js
- frontend/assets/js/chat.js
- frontend/assets/style.css
- frontend/chat.html
- frontend/index.html

---

## CORRECTION 1 — Clic projet dans la sidebar → naviguer vers project.html

Fichier : frontend/assets/js/sidebar.js

**Problème :** Cliquer sur un nom de projet dans la sidebar déplie/replie la liste
de conversations mais ne navigue pas vers la vue projet.

**Correction :**
La zone cliquable doit être divisée en deux :
- Clic sur la flèche ▶/▼ → toggle expand/collapse (comportement actuel)
- Clic sur le NOM du projet → navigate vers `project.html?id={project.id}`

Dans la génération HTML de renderSidebar(), modifier le nav-project-header :

```html
<!-- AVANT (tout clique = toggle) -->
<div class="nav-project-header" data-project-id="${project.id}">
  <span class="nav-project-toggle">${isExpanded ? '▼' : '▶'}</span>
  <span class="sidebar-text">${project.name}</span>
  ${hasActivePipeline ? '<span class="active-dot"></span>' : ''}
</div>

<!-- APRÈS (flèche = toggle, nom = navigate) -->
<div class="nav-project-header" data-project-id="${project.id}">
  <span class="nav-project-toggle nav-project-toggle-btn" data-project-id="${project.id}">
    ${isExpanded ? '▼' : '▶'}
  </span>
  <a class="nav-project-name sidebar-text" href="project.html?id=${project.id}">
    ${project.name}
  </a>
  ${hasActivePipeline ? '<span class="active-dot"></span>' : ''}
</div>
```

Modifier le listener en conséquence :
- Les `.nav-project-toggle-btn` gèrent le toggle
- Les `.nav-project-header` ne gèrent plus le toggle global (éviter double déclenchement)

CSS à ajouter :
```css
.nav-project-name {
  color: var(--text-primary);
  text-decoration: none;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}
.nav-project-name:hover { color: var(--accent); }
```

---

## CORRECTION 2 — Logo JARVIS = retour au dashboard

Fichier : frontend/assets/js/sidebar.js

**Problème :** Aucun moyen de revenir au dashboard (index.html).

**Correction :**
Dans la génération HTML de renderSidebar(), la `.sidebar-logo` devient un lien :

```html
<!-- AVANT -->
<div class="sidebar-logo">⚡ <span class="sidebar-text">JARVIS</span></div>

<!-- APRÈS -->
<a href="index.html" class="sidebar-logo" title="Tableau de bord">
  ⚡ <span class="sidebar-text">JARVIS</span>
</a>
```

CSS à ajouter/modifier :
```css
.sidebar-logo {
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 700;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sidebar-logo:hover { color: var(--accent); }
```

---

## CORRECTION 3 — Créer un projet depuis l'UI

### 3a. Bouton dans la sidebar
Fichier : frontend/assets/js/sidebar.js

Ajouter un bouton "+ Projet" dans la section `.sidebar-actions`, à côté des boutons existants.

```html
<button id="btn-new-project" class="btn-sidebar-action">
  <span class="sidebar-text">📁 Nouveau Projet</span>
  <span class="sidebar-collapsed-text" style="display:none">📁</span>
</button>
```

Ajouter le listener : `document.getElementById('btn-new-project').addEventListener('click', handleNewProject)`

### 3b. Fonction handleNewProject()
Ouvrir un modal avec ce formulaire :

```html
<div style="display:flex;flex-direction:column;gap:12px">
  <div>
    <label style="display:block;margin-bottom:4px;color:var(--text-muted);font-size:0.85rem">
      Nom du projet *
    </label>
    <input type="text" id="modal-project-name"
      style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)"
      placeholder="Mon Projet">
  </div>
  <div>
    <label style="display:block;margin-bottom:4px;color:var(--text-muted);font-size:0.85rem">
      Chemin du dossier JARVIS * <span style="font-size:0.75rem">(doit exister)</span>
    </label>
    <input type="text" id="modal-project-path"
      style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-family:monospace"
      placeholder="C:\DEV\PROJETS\mon-projet">
  </div>
  <div>
    <label style="display:block;margin-bottom:4px;color:var(--text-muted);font-size:0.85rem">
      Type de projet
    </label>
    <select id="modal-project-type"
      style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
      <option value="dev">dev</option>
      <option value="data">data</option>
      <option value="content">content</option>
      <option value="other">other</option>
    </select>
  </div>
  <div>
    <label style="display:block;margin-bottom:4px;color:var(--text-muted);font-size:0.85rem">
      Dossier local lié (optionnel)
    </label>
    <input type="text" id="modal-project-local-path"
      style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-family:monospace"
      placeholder="C:\chemin\vers\dossier\local">
  </div>
</div>
```

Actions du modal : [Annuler] + [Créer le projet]

Clic "Créer le projet" :
```js
const name = document.getElementById('modal-project-name').value.trim()
const path = document.getElementById('modal-project-path').value.trim()
const type = document.getElementById('modal-project-type').value
const local_path = document.getElementById('modal-project-local-path').value.trim() || null

if (!name || !path) {
  window.showToast('Nom et chemin sont requis', 'error')
  return
}

const project = await window.API.createProject({ name, path, type, local_path, instructions: '' })
window.closeModal()
window.showToast(`Projet "${project.name}" créé`, 'success')
// Recharger la sidebar puis naviguer vers le projet
window.location.href = `project.html?id=${project.id}`
```

En cas d'erreur (chemin inexistant, doublon) → `showToast(error.message, 'error')`.

---

## CORRECTION 4 — Gestion conversations dans la sidebar (renommer, supprimer)

### 4a. Backend : endpoint PATCH /chat/conversations/{id}
Fichier : backend/routers/chat.py

Ajouter ce schéma Pydantic (en haut du fichier, avec les autres) :
```python
class ConversationUpdate(BaseModel):
    title: str | None = None
```

Ajouter cette route (après la route DELETE existante ou après PATCH folder) :
```python
@router.patch("/conversations/{conv_id}")
def update_conversation(conv_id: int, data: ConversationUpdate):
    """Met à jour le titre d'une conversation."""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    
    if data.title is not None:
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (data.title, now, conv_id)
        )
        db.commit()
    
    db.close()
    return {"message": "Conversation mise à jour", "id": conv_id, "title": data.title}
```

### 4b. api.js : ajouter la fonction updateConversation
Fichier : frontend/assets/js/api.js

Dans l'objet `window.API`, ajouter (après `updateConversationFolder`) :
```js
updateConversation: (id, data) => _patch(`/chat/conversations/${id}`, data),
```

### 4c. sidebar.js : hover actions sur les nav-items conversations

Pour chaque item conversation dans la sidebar, ajouter des boutons d'action au hover :

```html
<div class="nav-item-wrapper">
  <a href="chat.html?id=${conv.id}..." class="nav-item nav-item--chat ${isActive ? 'nav-item--active' : ''}">
    <span class="sidebar-text">💬 ${conv.title}</span>
  </a>
  <div class="nav-item-actions">
    <button class="nav-item-action-btn" data-action="rename" data-conv-id="${conv.id}" data-conv-title="${conv.title}" title="Renommer">✏️</button>
    <button class="nav-item-action-btn" data-action="delete" data-conv-id="${conv.id}" data-conv-title="${conv.title}" title="Supprimer">🗑️</button>
  </div>
</div>
```

CSS à ajouter :
```css
.nav-item-wrapper {
  display: flex;
  align-items: center;
  position: relative;
}
.nav-item-wrapper .nav-item {
  flex: 1;
  min-width: 0;
}
.nav-item-actions {
  display: none;
  gap: 2px;
  flex-shrink: 0;
  padding-right: 4px;
}
.nav-item-wrapper:hover .nav-item-actions {
  display: flex;
}
.nav-item-action-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 2px 3px;
  border-radius: 3px;
  opacity: 0.6;
  color: var(--text-muted);
}
.nav-item-action-btn:hover {
  opacity: 1;
  background: var(--bg-input);
}
```

Après `renderSidebar()`, ajouter les listeners sur les `.nav-item-action-btn` :

```js
document.querySelectorAll('.nav-item-action-btn').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    e.preventDefault()
    e.stopPropagation()
    const action = btn.dataset.action
    const convId = btn.dataset.convId
    const convTitle = btn.dataset.convTitle

    if (action === 'rename') {
      await handleRenameConversation(convId, convTitle)
    } else if (action === 'delete') {
      await handleDeleteConversation(convId, convTitle)
    }
  })
})
```

Fonction `handleRenameConversation(convId, currentTitle)` :
```js
window.showModal('Renommer la conversation', `
  <input type="text" id="rename-input"
    value="${currentTitle}"
    style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary)">
`, [
  { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
  { label: '💾 Renommer', type: 'primary', onClick: async () => {
    const newTitle = document.getElementById('rename-input').value.trim()
    if (!newTitle) { window.showToast('Titre vide', 'warning'); return }
    await window.API.updateConversation(convId, { title: newTitle })
    window.closeModal()
    window.showToast('Conversation renommée')
    await window.initSidebar()  // rafraîchir la sidebar
  }}
])
// Focus auto sur l'input
setTimeout(() => document.getElementById('rename-input')?.focus(), 100)
```

Fonction `handleDeleteConversation(convId, title)` :
```js
window.showModal(
  'Supprimer la conversation',
  `Supprimer "<strong>${title}</strong>" ? Cette action est définitive.`,
  [
    { label: 'Annuler', type: 'secondary', onClick: () => window.closeModal() },
    { label: '🗑️ Supprimer', type: 'danger', onClick: async () => {
      await window.API.deleteConversation(convId)
      window.closeModal()
      window.showToast('Conversation supprimée')
      // Si on est sur cette conversation → redirect vers index.html
      const currentConvId = window.getURLParam('id')
      if (currentConvId == convId) {
        window.location.href = 'index.html'
      } else {
        await window.initSidebar()
      }
    }}
  ]
)
```

---

## CORRECTION 5 — Sélecteur de modèle dans le chat

Le backend supporte déjà `model` dans `POST /chat/conversations/{id}/messages`.
Il suffit de passer ce paramètre depuis le frontend.

### 5a. api.js : mettre à jour sendMessage
Fichier : frontend/assets/js/api.js

```js
// AVANT :
sendMessage: (conversationId, content) => _post(`/chat/conversations/${conversationId}/messages`, { content }),

// APRÈS :
sendMessage: (conversationId, content, model = null) => {
  const body = { content }
  if (model) body.model = model
  return _post(`/chat/conversations/${conversationId}/messages`, body)
},
```

### 5b. chat.html : ajouter le sélecteur dans la zone input
Fichier : frontend/chat.html

Dans la zone `.chat-input-area`, ajouter AVANT le `.chat-input-wrapper` :

```html
<div class="chat-model-selector">
  <span class="chat-model-label">Modèle :</span>
  <select id="chat-model-select" class="chat-model-select">
    <option value="">Par défaut</option>
    <!-- Options chargées dynamiquement -->
  </select>
</div>
```

### 5c. chat.js : charger les modèles et utiliser la sélection
Fichier : frontend/assets/js/chat.js

Dans la fonction d'initialisation (DOMContentLoaded), après `loadConversation()` :

```js
// Charger les modèles disponibles pour le sélecteur
try {
  const models = await window.API.getAvailableModels()
  const select = document.getElementById('chat-model-select')
  if (select && models) {
    // models peut être {routing: [...], code: [...], analysis: [...]} ou une liste plate
    let allModels = []
    if (Array.isArray(models)) {
      allModels = models
    } else {
      // Fusionner toutes les listes, dédupliquer
      const seen = new Set()
      Object.values(models).flat().forEach(m => {
        const id = typeof m === 'string' ? m : m.id
        if (id && !seen.has(id)) { seen.add(id); allModels.push(id) }
      })
    }
    allModels.forEach(m => {
      const opt = document.createElement('option')
      opt.value = m
      opt.textContent = m
      select.appendChild(opt)
    })
  }
} catch(e) {
  console.warn('Modèles non disponibles:', e)
}
```

Dans la fonction d'envoi du message, lire le modèle sélectionné :

```js
// Avant l'appel API.sendMessage :
const selectedModel = document.getElementById('chat-model-select')?.value || null

// Appel avec modèle :
const result = await window.API.sendMessage(conversationId, content, selectedModel || null)
```

CSS à ajouter :
```css
.chat-model-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  margin-bottom: 6px;
}
.chat-model-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  flex-shrink: 0;
}
.chat-model-select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 3px 8px;
  color: var(--text-primary);
  font-size: 0.8rem;
  max-width: 280px;
}
.chat-model-select:focus { border-color: var(--accent); outline: none; }
```

---

## CORRECTION 6 — CSS cassé : labels modèles dans les paramètres

**Problème visible sur la capture :** Les labels "Routage / Décision", "Code / Analyse", "Missions complexes"
s'affichent avec leur description en dessous et tout se mélange verticalement avec les dropdowns.

**Cause :** La règle `.model-row` a un `flex` mais la colonne `.model-info` prend trop de place,
forçant le select à passer en dessous.

Fichier : frontend/assets/style.css

Remplacer les règles `.model-row` et `.model-info` existantes par :

```css
.model-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  gap: 16px;
  flex-wrap: nowrap;
}
.model-row:last-of-type { border-bottom: none; }
.model-info {
  flex: 0 0 200px;    /* largeur fixe, ne grossit pas */
  min-width: 0;
}
.model-label {
  font-weight: 500;
  font-size: 0.9rem;
  display: block;
  white-space: nowrap;
}
.model-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.model-select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
  color: var(--text-primary);
  flex: 1;           /* prend tout l'espace restant */
  min-width: 180px;
  max-width: 400px;
  font-size: 0.9rem;
}
.model-select:focus { border-color: var(--accent); outline: none; }
```

---

## VÉRIFICATIONS FINALES APRÈS CORRECTIONS

1. Redémarrer le serveur FastAPI (pour prendre en compte le nouveau endpoint PATCH /chat/conversations/{id})

2. Vérifier dans Swagger (http://localhost:8000/docs) que le nouveau endpoint apparaît :
   `PATCH /chat/conversations/{conv_id}` avec body `{"title": "..."}`

3. Tester manuellement les 6 corrections :
   - Clic nom projet dans sidebar → navigate vers project.html ✓
   - Clic logo JARVIS → retour index.html ✓
   - Bouton "📁 Nouveau Projet" → modal → créer → navigate vers le projet ✓
   - Hover conversation → boutons ✏️ 🗑️ visibles → renommer → sidebar rafraîchie ✓
   - Chat → sélecteur de modèle visible → envoyer message avec modèle spécifique ✓
   - Paramètres → labels modèles sur une ligne, dropdown prend l'espace restant ✓

---

TESTS AUTOMATIQUES :
Après les corrections, relancer les tests E2E pour vérifier qu'aucune régression :
```bash
python -m pytest tests/test_frontend_e2e.py -v --tb=short 2>&1
```

FIN DE MISSION :
- Serveur redémarre sans erreur
- 6 corrections appliquées et vérifiées
- Tests E2E repassés (41/43 minimum)
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
