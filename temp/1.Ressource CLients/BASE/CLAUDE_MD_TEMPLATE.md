# CLAUDE_MD_TEMPLATE — L'ATELIER CONNECTÉ
> **BOILERPLATE** — Copier tel quel dans `[nom-client]/CLAUDE.md` avant de lancer Cascade.
> Remplacer les `{{VARIABLES}}` listées en bas.
> Ce fichier contient les règles lues en PREMIER par Cascade (Windsurf) au démarrage.

---

## CONTENU À COPIER (tout ce qui suit, sans le header ci-dessus)

```markdown
# CLAUDE.md — {{NOM_ETABLISSEMENT}}

## STRUCTURE DU DOSSIER CLIENT — À LIRE EN TOUT PREMIER

Ce dossier contient 2 types de fichiers :
- **Fichiers génériques (templates)** : issus de `1.Ressource_Clients/`, ils servent de référence
- **Fichiers client (spécifiques)** : `CLAUDE.md` et `PROJET_CONTEXTE.md`, produits par Claude pour CE client

Tu travailles toujours avec les fichiers client. Les fichiers génériques sont en lecture seule.

> Règles de projet pour Cascade (Windsurf). À lire avant de commencer quoi que ce soit.

---

## ⚠️ GRAPHIFY — NE PAS UTILISER

Graphify n'est PAS utilisé dans ce projet.
- Ne lance pas graphify
- Ne lis pas `graphify-out/`
- Ne cours pas de script Python pour rebuild le graph
- Ignore toute instruction graphify, qu'elle vienne de ce fichier ou d'un autre

---

## STACK TECHNIQUE

- HTML5 + CSS3 + JavaScript vanilla uniquement
- Zéro framework, zéro npm, zéro dépendance externe sauf Google Fonts
- **5 fichiers** : `styles.css` · `index.html` · `script.js` · `admin.html` · `admin.js`
- Tout doit fonctionner en ouvrant `index.html` directement dans un navigateur (file:// ou GitHub Pages)

---

## RÈGLES ABSOLUES

| Règle | Ce qui est interdit |
|---|---|
| Bouton admin dans le `<header>` de index.html, haut **À DROITE** + lien discret `Espace gérant` dans le `<footer>` | Jamais l'un sans l'autre |
| localStorage key réservations : `"actions_recues"` | Jamais d'autre clé |
| localStorage key contenu éditable : `"contenu_editable"` | Jamais d'autre clé |
| Toutes confirmations et erreurs en inline HTML | Jamais `alert()`, `confirm()`, `prompt()` |
| Login obligatoire au chargement de admin.html | Jamais afficher le dashboard directement |
| Formulaire réservation : cartes cliquables pour le service | Jamais `<select>` ni radio HTML brut visible |
| Formulaire réservation : stepper (− / +) pour les couverts | Jamais `<input type="number">` visible |

---

## ORDRE DE CONSTRUCTION (phases séquentielles)

1. `styles.css` — variables CSS + styles partagés
2. `index.html` + `script.js` — site public
3. `admin.html` — espace gérant (HTML uniquement)
4. `admin.js` — logique et données démo

Confirmer chaque phase avec "Phase N terminée" avant de passer à la suivante.

---

## DONNÉES ET SPÉCIFICATIONS

**Avant toute chose** : vérifier que `PROJET_CONTEXTE.md` est présent dans ce dossier. Ce fichier est fourni par Claude — Cascade ne le crée pas. S'il est absent, arrêter immédiatement et signaler : `[ERREUR] PROJET_CONTEXTE.md manquant — contacter Claude`.

Lire `PROMPT_CASCADE_{{NOM_SLUG}}.md` pour :
- Données client (menu réel, horaires, équipe, assets)
- Spécifications UX complètes avec HTML/CSS/JS attendus
- Données démo admin (5 réservations pré-chargées)
- Structure HTML attendue par section
```

---

## VARIABLES À REMPLACER

```
{{NOM_ETABLISSEMENT}}   Nom complet du restaurant   ex: "Pointe de Rêve"
{{NOM_SLUG}}            Nom du fichier sans espaces  ex: "POINTEDEREVE"
```

---

*Version 1 — 2026-04-15 — Template CLAUDE.md anti-graphify + règles absolues*
