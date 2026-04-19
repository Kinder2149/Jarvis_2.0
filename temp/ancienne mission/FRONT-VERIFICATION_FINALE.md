# FRONT-VERIFICATION — Audit final UX + technique

> À exécuter APRÈS que les missions FRONT-01 à FRONT-06 soient toutes terminées.
> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Objectif

Vérifier que :
1. Toutes les missions sont correctement implémentées (tests fonctionnels)
2. Aucune régression n'a été introduite sur les flows existants
3. Identifier les défauts d'implémentation restants (qualité, cohérence, lacunes)
4. Émettre une critique pratico-technique du résultat

---

## PARTIE A — Tests fonctionnels mission par mission

### A1 — FRONT-01 : CTA post-session Module Code

**Préparer :** avoir un projet avec au moins une session terminée ou en créer une.

- [ ] Lancer une session Module Code → l'abandonner → page affiche "⛔ Session abandonnée" + boutons
- [ ] Cliquer "📁 Retour au projet" → navigue vers project.html ✓
- [ ] Cliquer "🔄 Relancer ce workflow" → modal avec workflow pré-sélectionné ✓
- [ ] Lancer une session → la laisser se terminer (COMPLETED) → page affiche "✅ Session terminée" + boutons ✓
- [ ] Cliquer "⚡ Nouvelle session" → modal ouverte ✓
- [ ] **Régression** : une session en WAITING_VALIDATION affiche toujours la zone de validation (diff ou generic) ✓
- [ ] **Régression** : bouton 🔄 sur step ERROR fonctionne toujours ✓

### A2 — FRONT-02 : CTA post-session Atelier

- [ ] Lancer pipeline Atelier → abandonner → page affiche "⛔ Pipeline abandonné" + bouton retour kanban ✓
- [ ] Cliquer "← Retour kanban" → retour vers atelier.html (vue kanban) ✓
- [ ] Provoquer un step FAILED (si possible) → bouton 🔄 visible sur la step card ✓
- [ ] Cliquer 🔄 → step relancé + polling redémarre ✓
- [ ] **Régression** : flow normal Atelier (form → checkpoint → export ZIP) toujours fonctionnel ✓
- [ ] **Régression** : export ZIP téléchargeable ✓

### A3 — FRONT-03 : Compteur sidebar Atelier

- [ ] `GET /atelier/prospects` en DevTools → chaque prospect a `session_status` (null si pas de session) ✓
- [ ] Lancer pipeline Atelier → laisser bloquer au step 0 (form saisie) → badge sidebar = 1 ✓
- [ ] Soumettre le formulaire → pipeline reprend (RUNNING) → badge sidebar passe à 0 ✓
- [ ] **Régression** : `GET /atelier/prospects` renvoie tous les autres champs intacts ✓

### A4 — FRONT-04 : Kanban badges visuels

- [ ] Prospect sans session → aucun icône sur la card ✓
- [ ] Prospect avec session WAITING_VALIDATION → icône ⏸️ orange ✓
- [ ] Prospect avec session RUNNING → icône ⚙️ ✓
- [ ] Prospect avec session COMPLETED → icône ✅ ✓
- [ ] **Régression** : clic card navigue vers atelier.html?prospect_id=X ✓
- [ ] **Régression** : bouton 🗑 suppression fonctionne ✓

### A5 — FRONT-05 : Dashboard section waiting

- [ ] Dashboard sans session active → section masquée ✓
- [ ] Session Module Code en WAITING_VALIDATION → banner orange "⏸️ 1 session attend ta validation" en haut ✓
- [ ] Session Atelier en WAITING_VALIDATION → apparaît dans la même banner ✓
- [ ] 2 sessions waiting (1 MC + 1 Atelier) → "⏸️ 2 sessions attendent ta validation" ✓
- [ ] Clic "→ Valider" session Module Code → module-code.html?session=X&project_id=Y ✓
- [ ] Clic "→ Valider" session Atelier → atelier.html?prospect_id=X ✓
- [ ] Session RUNNING → section "⚡ En cours" visible en dessous ✓
- [ ] Session CREATED > 1h → section "⚠️ bloquée" repliable en bas ✓
- [ ] **Régression** : abandonSession() fonctionne ✓
- [ ] **Régression** : filtres date (aujourd'hui/hier/semaine) et timeline inchangés ✓
- [ ] **Régression** : stats semaine correctes ✓

### A6 — FRONT-06 : project.html lancement inline

- [ ] Sur project.html, cliquer "✏️ Nouveau Chat" → redirige directement vers chat.html (0 modal) ✓
- [ ] La conversation créée est bien liée au projet courant ✓
- [ ] Cliquer "⚡ Nouveau Module Code" → modal avec projet pré-rempli (dropdown grisé) ✓
- [ ] Dropdown workflow avec descriptions (pas juste les noms bruts) ✓
- [ ] Section du bas s'appelle "Activité du projet" ✓
- [ ] **Régression** : liste des sessions+chats s'affiche toujours ✓

---

## PARTIE B — Tests de régression généraux

### Navigation

- [ ] Logo JARVIS → retour index.html ✓
- [ ] Flèche sidebar projet → toggle expand/collapse (pas navigation) ✓
- [ ] Nom projet dans sidebar → navigue vers project.html ✓
- [ ] Lien projet dans module-code.html → navigue vers project.html ✓
- [ ] Sidebar collapse/expand → fonctionne sur toutes les pages ✓

### Sidebar

- [ ] Nouvelles sessions apparaissent sous le bon projet dans la sidebar ✓
- [ ] Sessions terminées (COMPLETED/ABORTED) disparaissent de la sidebar ✓
- [ ] Recherche sidebar filtre correctement ✓

### Backend

- [ ] `GET /atelier/prospects` → réponse rapide, pas de N+1 queries ✓
- [ ] Serveur démarre sans erreur (vérifier logs uvicorn) ✓
- [ ] Aucune erreur 500 dans la console JS ✓

---

## PARTIE C — Critique pratico-technique

Après avoir testé toutes les missions, répondre honnêtement à ces questions :

### C1 — Qualité d'implémentation

Évaluer chaque point :

1. **FRONT-01 CTA** : le bouton "Retour au projet" est-il visuellement dans un endroit logique et visible ? Ou est-il perdu dans une zone compacte ?
2. **FRONT-01 Modal preset** : quand le projet est pré-rempli, le dropdown est-il clairement désactivé/grisé, ou ambigu ?
3. **FRONT-02 Retry Atelier** : le bouton 🔄 est-il sur la step card en position cohérente avec Module Code ?
4. **FRONT-03 session_status** : dans la réponse API, `session_status: null` pour les prospects sans session — est-ce que ça affiche correctement `undefined` ou `null` dans la sidebar (devrait être transparent) ?
5. **FRONT-04 Icônes** : les icônes dans le kanban sont-elles assez visibles ? La distinction ⏸️ vs ⚙️ est-elle suffisamment claire au premier coup d'œil ?
6. **FRONT-05 Banner** : si on a 5+ sessions waiting, le banner devient-il encombrant ? Est-il responsive ?
7. **FRONT-06 Chat direct** : si la création de conversation échoue, le message d'erreur est-il visible ?

### C2 — Cohérence UX

1. Sur module-code.html, le lien projet `📁 NomProjet` dans l'en-tête existe déjà. Après FRONT-01, il y a maintenant deux chemins vers le projet (le lien header ET le bouton CTA). Est-ce redondant ou complémentaire ?
2. La terminologie est-elle cohérente ? "Session" vs "Pipeline" vs "Module Code" — est-ce que Cascade a introduit des incohérences ?
3. Le dashboard montre maintenant les sessions Atelier waiting. Mais si un utilisateur clique "→ Valider" sur une session Atelier et que le step est le formulaire initial, arrive-t-il bien sur la zone d'action (form saisie) ou juste sur la vue kanban ?

### C3 — Ce qui manque encore

Identifier honnêtement ce qui n'est PAS fait et si ça manque en pratique :

1. Aucune notification push (browser notification API) quand une session passe en WAITING_VALIDATION pendant que tu es sur une autre page. Est-ce manquant ou superflu pour usage solo ?
2. Pas de "relancer" pour les sessions Atelier FAILED (on peut seulement retenter un step individuel). Est-ce suffisant ?
3. Le dashboard ne montre pas les sessions Atelier RUNNING (seulement WAITING_VALIDATION). Manquant ou OK ?

### C4 — Performance

1. Combien d'appels API fait le dashboard au chargement ? (compter dans DevTools → Network)
   - Attendu : getProjects, getConversations, getProspects, N×getProjectSessions (parallèles)
   - Acceptable ? Pour usage solo local, oui. À noter si > 10 appels.
2. La sidebar fait ses propres appels en parallèle du dashboard — est-ce qu'il y a des doublons d'appels (même endpoint appelé 2x) ?

---

## PARTIE D — Synthèse finale

Produire un bilan en 2 sections :

**Ce qui est solide :**
- Liste des points qui fonctionnent bien et sont bien implémentés

**Ce qui reste à améliorer (BACKLOG) :**
- Liste priorisée des défauts restants, avec estimation effort
- Indiquer si c'est un bug (à corriger maintenant) ou une amélioration (backlog)

---

## FIN DE MISSION VÉRIFICATION

- [ ] Toutes les cases A1-A6 cochées
- [ ] Tests de régression B passés
- [ ] Critique C rédigée avec honnêteté (pas "tout est parfait")
- [ ] PROJET_CONTEXTE.md section 8 mis à jour : "UX Refactoring terminé, résultat : X/Y missions OK"
- [ ] Bugs identifiés en C → ajoutés en section 4 "❌ Bugs connus" de PROJET_CONTEXTE.md
- [ ] CHANGELOG.md entrée "UX Refactoring Frontend V2" avec liste des 6 missions
- [ ] Section 9 BACKLOG de PROJET_CONTEXTE.md mise à jour avec les points de C3
