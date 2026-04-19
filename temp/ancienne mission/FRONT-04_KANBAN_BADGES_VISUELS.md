# FRONT-04 — Kanban : badges visuels de statut session

> Lire PROJET_CONTEXTE.md en entier avant toute action.
> **Prérequis :** FRONT-03 doit être terminé. `GET /atelier/prospects` retourne maintenant `session_status`.

---

## Problème exact

Dans `frontend/assets/js/atelier.js`, la fonction `renderProspectCard(prospect)` :

```js
const hasPipeline = prospect.session_id ? '⚙️ ' : '';
```

Tous les prospects avec une session affichent le même `⚙️`, qu'elle soit RUNNING, WAITING_VALIDATION ou FAILED. L'utilisateur ne peut pas distinguer d'un coup d'œil quels prospects ont besoin de son attention.

---

## Objectif

Remplacer le `⚙️` générique par un indicateur visuel différencié selon `session_status` :

| session_status | Indicateur | Sens |
|---|---|---|
| `WAITING_VALIDATION` | `⏸️` (orange) | Attend TON action |
| `RUNNING` | `⚙️` (avec animation pulse) | IA en cours |
| `COMPLETED` | `✅` | Pipeline terminé |
| `FAILED` / `ERROR` | `❌` | Erreur |
| `ABORTED` | `⛔` | Abandonné |
| null / autre | `` | Pas encore démarré |

---

## Fichier à modifier

`frontend/assets/js/atelier.js`

---

## Modifications détaillées

### 1. Fonction `renderProspectCard` — remplacer l'indicateur

Remplacer :
```js
const hasPipeline = prospect.session_id ? '⚙️ ' : '';
```

Par :
```js
function getSessionIndicator(sessionStatus) {
  const map = {
    'WAITING_VALIDATION': '<span title="En attente de validation" style="color:#f59e0b">⏸️</span> ',
    'RUNNING': '<span title="IA en cours..." style="color:#6366f1">⚙️</span> ',
    'COMPLETED': '<span title="Terminé" style="color:#22c55e">✅</span> ',
    'FAILED': '<span title="Erreur" style="color:#ef4444">❌</span> ',
    'ERROR': '<span title="Erreur" style="color:#ef4444">❌</span> ',
    'ABORTED': '<span title="Abandonné" style="color:#64748b">⛔</span> ',
  };
  return map[sessionStatus] || '';
}
const sessionIndicator = getSessionIndicator(prospect.session_status);
```

Et dans le template HTML de la card, remplacer `${hasPipeline}${prospect.nom}` par `${sessionIndicator}${prospect.nom}`.

**Note :** déclarer `getSessionIndicator` comme fonction locale dans `renderProspectCard` ou comme fonction module-level (avant `renderProspectCard`).

### 2. CSS — classe pulse pour RUNNING (optionnel mais recommandé)

Dans `frontend/assets/style.css`, ajouter si pas déjà présent :

```css
@keyframes pulse-icon {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.session-running-icon {
  display: inline-block;
  animation: pulse-icon 1.5s ease-in-out infinite;
}
```

Et dans `getSessionIndicator` pour RUNNING :
```js
'RUNNING': '<span title="IA en cours..." class="session-running-icon" style="color:#6366f1">⚙️</span> ',
```

---

## Tests manuels

1. Kanban avec un prospect sans session → pas d'icône, juste le nom ✓
2. Lancer pipeline sur un prospect → step 0 (form saisie) → statut WAITING_VALIDATION → badge ⏸️ orange visible sur la card ✓
3. Soumettre le formulaire → pipeline passe en RUNNING → badge ⚙️ (si rechargement page) ✓
4. Pipeline terminé → badge ✅ ✓
5. **Test critique** : ouvrir kanban → identifier d'un coup d'œil les prospects ⏸️ → cliquer l'un d'eux → voir le formulaire en attente ✓

---

## FIN DE MISSION

- [ ] Build OK
- [ ] Kanban : icônes différenciées selon session_status
- [ ] ⏸️ visible pour WAITING_VALIDATION
- [ ] Pas de régression sur les interactions kanban (clic card, suppression)
- [ ] PROJET_CONTEXTE.md section 8 et CHANGELOG.md mis à jour
