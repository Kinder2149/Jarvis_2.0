# FIX-02 — Atelier : renforcement STACK_STANDARD (mot de passe admin + hero CSS)

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Les démos générées par l'atelier ont deux bugs récurrents :

**Bug 1 — Mot de passe admin incorrect** : `STACK_STANDARD.md` indique bien `admin` en texte, mais le
modèle génère des mots de passe différents (`admin123`, `restaurant123`, etc.) parce que la règle est
en prose. Il faut un bloc de code JS exact que le modèle reproduit littéralement.

**Bug 2 — Image hero recouvre toute la page** : Le modèle génère le hero avec `position: fixed` ou
un `z-index` élevé, ce qui fait que l'image de couverture couvre toutes les sections en dessous.
L'utilisateur peut scroller mais tout le contenu reste sous l'image. La spec existe déjà mais en texte
descriptif — il faut un bloc CSS exact.

---

## Objectif

Modifier `backend/data/atelier/resources/STACK_STANDARD.md` uniquement.
Ajouter des blocs de code exacts aux deux endroits concernés.

---

## Fichier à modifier : `backend/data/atelier/resources/STACK_STANDARD.md`

### Modification 1 — Mot de passe admin

Chercher la ligne exacte :
```
**Mot de passe admin :** `admin` — codé en dur dans admin.js (pas de vrai backend)
```

Remplacer par :

```
**Mot de passe admin :** `admin` — codé en dur dans admin.js (pas de vrai backend)

Code de validation obligatoire dans admin.js — reproduire exactement, ne pas modifier le mot de passe :

```javascript
const MOT_DE_PASSE_ADMIN = 'admin';

function verifierMotDePasse(saisie) {
  return saisie === MOT_DE_PASSE_ADMIN;
}
```

> ⚠️ INTERDIT : `admin123`, `password`, tout autre valeur. Le mot de passe est toujours `admin`, sans exception.
```

---

### Modification 2 — Hero CSS

Chercher le bloc qui commence par :
```
### Hero (section d'ouverture)
```

La section contient déjà des règles de position et z-index en prose. Après toutes les règles textuelles
de cette section (avant `### Sections du corps`), ajouter ce bloc CSS exact :

```
CSS obligatoire pour le hero — reproduire exactement, ne pas modifier les valeurs de position ni z-index :

```css
/* === HERO — STRUCTURE OBLIGATOIRE === */
.hero {
  position: relative;        /* JAMAIS fixed, JAMAIS sticky, JAMAIS absolute */
  z-index: 1;                /* JAMAIS supérieur à 10 */
  min-height: 90vh;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  inset: 0;                  /* équivalent top:0 right:0 bottom:0 left:0 */
  background: rgba(0, 0, 0, 0.40);
  z-index: 1;                /* derrière le contenu hero, devant l'image */
}

.hero-content {
  position: relative;
  z-index: 2;                /* devant l'overlay, mais pas plus */
}

/* Sections APRÈS le hero — toujours visibles, jamais cachées */
section:not(.hero) {
  position: relative;
  z-index: 0;                /* en dessous du hero — c'est NORMAL et VOULU */
}
```

> ⚠️ INTERDIT sur .hero : `position: fixed`, `position: sticky`, `z-index > 10`, `overflow: visible` avec contenu absolu.
> ⚠️ INTERDIT : image dans le hero via `<img>` — uniquement `background-image` CSS.
```

---

## Ce qu'on ne touche pas

- Aucun fichier backend Python
- Aucun fichier frontend
- Les autres sections de `STACK_STANDARD.md` (localStorage, KPI, etc.)
- Les ressources atelier (`CADRAGE_STRATEGIQUE.md`, `CATEGORIES_CLIENT_RESTAURATION.md`, etc.)

---

## Test manuel (3 étapes)

1. Lancer un workflow `atelier_restauration` complet sur un prospect test
2. Ouvrir `admin.html` généré → tenter de se connecter avec `admin` → doit fonctionner
   → tenter avec `admin123` → doit être refusé
3. Ouvrir `index.html` généré → scroller jusqu'en bas → toutes les sections doivent être
   visibles et accessibles, aucune ne doit être cachée derrière l'image hero

---

## FIN DE MISSION

- [ ] Build sans erreur (pas de Python à compiler, juste vérifier que le serveur démarre)
- [ ] Test manuel 3 étapes validé
- [ ] `STACK_STANDARD.md` modifié aux deux endroits uniquement
- [ ] Aucun autre fichier modifié
