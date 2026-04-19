# PROJET_CONTEXTE — L'ATELIER CONNECTÉ
> **RÉFÉRENCE CLAUDE** — Contexte général de L'Atelier Connecté. Ne pas copier dans le dossier client.
> Ce fichier est lu par Claude dans ce projet pour comprendre le contexte métier global.
> Le dossier client ne contient que 2 fichiers : `CLAUDE.md` + `PROMPT_CASCADE_[NOM].md`.

---

## QUI CONSTRUIT CE PROJET

**L'Atelier Connecté** est une micro-entreprise de services numériques de proximité, basée à Villeurbanne (Lyon, 69100). Elle aide les commerçants, artisans, associations et indépendants locaux à simplifier leur organisation numérique.

Contact : atelierconnecte.contact@gmail.com · 07.50.48.35.80
Site : https://kinder2149.github.io/L-Atelier_connect-/

---

## OBJECTIF DE CETTE DÉMO

Ce dossier contient une **démo client personnalisée**, construite AVANT le premier contact commercial. Ce n'est pas un site en production — c'est une preuve de valeur, fonctionnelle et visuelle, pensée pour convaincre un prospect local en lui montrant exactement ce qu'on pourrait faire pour lui.

**Ce que la démo doit accomplir :**
1. Ressembler immédiatement à l'univers du prospect (couleurs, textes, images réels)
2. Démontrer une solution concrète à sa douleur principale (formulaire + espace admin)
3. Être utilisable en démo en direct à partir d'un lien GitHub Pages

---

## POSTURE

- Pas d'agence, pas de jargon : l'outil doit être compréhensible par un non-technicien en 10 secondes
- Chaque libellé est en langage métier (jamais "Submit", "Dashboard", "API")
- L'espace admin est le cœur de la démonstration — c'est ce qu'on vend
- La démo est déployée sur GitHub Pages avant l'envoi du mail

---

## STRUCTURE GÉNÉRIQUE DE CHAQUE DÉMO

```
[nom-client]/
├── index.html        ← site public du prospect
├── admin.html        ← espace de gestion (le cœur)
├── styles.css        ← styles partagés
├── script.js         ← logique formulaire + localStorage
├── admin.js          ← logique admin + éditeur
└── assets/           ← images réelles extraites du site original
```

---

## DÉPLOIEMENT

```
Compte GitHub  : atelier-connecte
Convention URL : https://atelier-connecte.github.io/[nom-client]/
```

Commandes de déploiement :
```bash
git init
git add .
git commit -m "Demo [Nom du Client]"
git branch -M main
git remote add origin [URL repo]
git push -u origin main
# Settings → Pages → main → /root → Save
```

---

*Générique — version 2026-04-14*
