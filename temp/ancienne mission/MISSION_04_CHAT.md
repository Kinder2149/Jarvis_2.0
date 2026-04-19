# MISSION 04 — Chat

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2 — lire entièrement)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Chat — Interface de conversation

OBJECTIF :
Implémenter la page de conversation chat de JARVIS.
Interface épurée inspirée de Claude.ai : historique des messages, zone de saisie,
titre éditable, badge du projet associé. 95% de l'usage quotidien passe par cette page.

PÉRIMÈTRE :
Fichiers à modifier :
- frontend/chat.html  (ajouter le contenu dans #page-chat)

Fichiers à créer :
- frontend/assets/js/chat.js

Prérequis : Mission 02 terminée.

---

INSTRUCTIONS DÉTAILLÉES :

### frontend/chat.html

Ajouter dans `#page-chat` :

```html
<div id="page-chat" class="chat-layout">
  <!-- Header conversation -->
  <div class="chat-header">
    <div class="chat-header-left">
      <h1 class="chat-title" id="chat-title" title="Double-cliquer pour renommer">
        Chargement...
      </h1>
      <div id="chat-project-badge"></div>
    </div>
    <div class="chat-header-right">
      <button id="btn-delete-conversation" class="btn-icon" title="Supprimer cette conversation">🗑️</button>
    </div>
  </div>

  <!-- Zone messages -->
  <div id="chat-messages" class="chat-messages"></div>

  <!-- Zone saisie -->
  <div class="chat-input-area">
    <div class="chat-input-wrapper">
      <textarea
        id="chat-input"
        placeholder="Votre message..."
        rows="1"
        maxlength="10000"
      ></textarea>
      <button id="btn-send" class="btn-send" title="Envoyer (Ctrl+Entrée)">
        <span id="btn-send-text">↑</span>
        <span id="btn-send-spinner" class="spinner" style="display:none"></span>
      </button>
    </div>
    <div class="chat-input-hint">Ctrl+Entrée pour envoyer</div>
  </div>
</div>
```

---

### frontend/assets/js/chat.js

**Initialisation :**
```
conversationId = getURLParam('id')
projectId = getURLParam('project_id')
```
Si pas de conversationId → afficher erreur "Conversation non trouvée".

Charger `API.getConversation(conversationId)` → rendre les messages + mettre à jour le titre + badge projet.

**Rendu du badge projet :**
Si `projectId` défini, charger `API.getProject(projectId)` → afficher :
`<a class="project-badge" href="project.html?id={id}">📁 {name}</a>`

**Rendu d'un message :**
```html
<!-- Message utilisateur -->
<div class="message message--user">
  <div class="message-content">{contenu en texte brut}</div>
  <div class="message-time">{formatDate(created_at)}</div>
</div>

<!-- Message IA -->
<div class="message message--assistant">
  <div class="message-avatar">⚡</div>
  <div class="message-body">
    <div class="message-content">{renderMarkdown(contenu)}</div>
    <div class="message-time">{formatDate(created_at)}</div>
  </div>
</div>
```

**Envoi d'un message :**
1. Lire le contenu du textarea (trim, rejeter si vide)
2. Désactiver le textarea et le bouton d'envoi
3. Afficher le message utilisateur immédiatement dans la liste (optimistic UI)
4. Afficher un message "assistant" avec spinner pendant la réponse :
   ```html
   <div class="message message--assistant message--loading">
     <div class="message-avatar">⚡</div>
     <div class="message-body"><div class="spinner"></div></div>
   </div>
   ```
5. Appeler `API.sendMessage(conversationId, content)`
6. Remplacer le message loading par la vraie réponse
7. Réactiver textarea + bouton
8. Auto-scroll vers le bas
9. En cas d'erreur → `showToast(erreur, 'error')`, supprimer le message loading

**Raccourci clavier :**
- `Ctrl+Entrée` → envoyer
- `Entrée` seul → nouvelle ligne dans le textarea
- Auto-resize du textarea (height: auto, scrollHeight)

**Titre éditable :**
Double-clic sur `.chat-title` → remplace le texte par un `<input>` pré-rempli.
Blur ou Entrée → `API.getConversation` n'a pas d'endpoint titre... 
Note : le titre est fixé à la création. Implémenter le renommage si `PATCH /chat/conversations/{id}` existe,
sinon laisser le titre affiché en lecture seule (ne pas implémenter le double-clic si pas d'endpoint).
Vérifier dans la SPEC si l'endpoint de renommage existe. Si non → titre en lecture seule.

**Suppression conversation :**
Clic sur 🗑️ → `showModal("Supprimer ?", "Cette conversation sera supprimée définitivement.", [{label: "Supprimer", type: "danger", ...}, {label: "Annuler", type: "secondary", ...}])`
Confirmation → `API.deleteConversation(conversationId)` → redirect vers `index.html`

**Auto-scroll :**
Après chaque rendu de message → `chatMessages.scrollTop = chatMessages.scrollHeight`

**CSS spécifique à ajouter dans style.css :**
```
.chat-layout : display flex, flex-direction column, height 100%, gap 0
.chat-header : padding 1rem 1.5rem, border-bottom 1px solid var(--border), display flex, justify-content space-between, align-items center, flex-shrink 0
.chat-header-left : display flex, align-items center, gap 12px
.chat-title : font-size 1.1rem, font-weight 600, cursor default, white-space nowrap, overflow hidden, text-overflow ellipsis, max-width 400px
.project-badge : display inline-flex, align-items center, gap 4px, font-size 0.8rem, color var(--accent), text-decoration none, background rgba(99,102,241,0.1), padding 2px 10px, border-radius 9999px, hover background rgba(99,102,241,0.2)
.chat-messages : flex 1, overflow-y auto, padding 1.5rem, display flex, flex-direction column, gap 1rem
.message : display flex, gap 12px, max-width 85%
.message--user : align-self flex-end, flex-direction row-reverse
.message--assistant : align-self flex-start
.message-avatar : width 32px, height 32px, border-radius 50%, background var(--accent), display flex, align-items center, justify-content center, font-size 0.9rem, flex-shrink 0
.message-body : display flex, flex-direction column, gap 4px
.message-content : background var(--bg-card), border 1px solid var(--border), border-radius 12px, padding 10px 14px, line-height 1.6
.message--user .message-content : background rgba(99,102,241,0.15), border-color rgba(99,102,241,0.3)
.message-time : font-size 0.75rem, color var(--text-muted)
.message--user .message-time : text-align right
.chat-input-area : padding 1rem 1.5rem, border-top 1px solid var(--border), flex-shrink 0
.chat-input-wrapper : display flex, gap 8px, align-items flex-end
.chat-input-wrapper textarea : flex 1, background var(--bg-input), border 1px solid var(--border), border-radius 12px, padding 10px 14px, color var(--text-primary), font-size 0.95rem, resize none, max-height 200px, overflow-y auto
.chat-input-wrapper textarea:focus : border-color var(--accent), outline none
.btn-send : width 40px, height 40px, border-radius 50%, background var(--accent), border none, color white, font-size 1.1rem, cursor pointer, flex-shrink 0, display flex, align-items center, justify-content center, hover background var(--accent-hover)
.btn-send:disabled : opacity 0.5, cursor not-allowed
.chat-input-hint : font-size 0.75rem, color var(--text-muted), margin-top 6px
```

---

TESTS MANUELS (3 étapes) :

1. Ouvrir une conversation existante via la sidebar → les messages s'affichent correctement,
   le titre est visible, le badge projet pointe vers la bonne page projet.

2. Saisir un message et envoyer (bouton ou Ctrl+Entrée) → le message utilisateur apparaît
   immédiatement, le spinner s'affiche, puis la réponse IA s'affiche avec markdown rendu.
   Le textarea se vide après envoi et le scroll est en bas.

3. Cliquer sur 🗑️ → modal de confirmation s'ouvre → cliquer "Annuler" → rien ne se passe.
   Re-cliquer → confirmer "Supprimer" → redirection vers le dashboard.

FIN DE MISSION :
- Tests manuels validés
- CHANGELOG.md mis à jour
- PROJET_CONTEXTE.md section 8 mis à jour
```
