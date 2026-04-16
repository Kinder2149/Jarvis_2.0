# STACK STANDARD — Choix technologiques

> Copier à la racine de chaque projet au démarrage.
> Lu par Claude et Cascade avant toute action.
> Aucune technologie hors de ce cadre sans justification écrite.

---

## CONTEXTE UTILISATEUR

Non-développeur. Je pilote des projets entièrement générés par IA.
Mon rôle : définir la vision, valider, tester manuellement.
Règle absolue : si je ne peux pas tester manuellement, la mission est incomplète.

---

## APPLICATION MOBILE

| Élément | Choix | Rôle |
|---|---|---|
| Framework | Flutter | Génère l'appli Android depuis un seul code |
| Langage | Dart | Langage de Flutter |
| Auth + données cloud | Firebase Auth + Firestore | Connexions + stockage cloud |
| Stockage fichiers | Firebase Storage | Images et fichiers utilisateurs |
| État de l'affichage | Provider | Mise à jour automatique des écrans |
| Distribution | Google Play Store | Publication Android |

---

## APPLICATION WEB FULL-STACK

| Élément | Choix | Rôle |
|---|---|---|
| Frontend | Angular + TypeScript | Pages web et comportement |
| Backend | Express.js + TypeScript | Serveur + API |
| Base de données | PostgreSQL + Prisma | Données structurées + ORM |
| Auth | Supabase Auth | Connexions, sessions |
| Stockage images | Cloudinary | Hébergement images |
| Déploiement | Vercel | Mise en ligne automatique |

---

## OUTIL IA / AGENT

| Élément | Choix | Rôle |
|---|---|---|
| Serveur | FastAPI (Python) | Reçoit les demandes, orchestre les agents |
| IA | À définir par projet | Claude ou Gemini selon besoin |
| Stockage | JSON ou SQLite | Historique simple |
| Interface | HTML/CSS/JS simple | Sans framework lourd |

---

## RÈGLES DE CHOIX

1. Identifier le type : Mobile / Web / Outil IA → stack correspondante
2. Projet similaire existant → copier exactement sa stack
3. Sortie du cadre standard → justification écrite obligatoire avant validation

---

## LIMITES DE COMPLEXITÉ

- Maximum 20 services/modules par projet
- Maximum 5 fichiers de documentation
- Maximum 3 couches : UI / Logique / Données
- Zéro structure vide "pour le futur"
- Zéro dépendance sans demande explicite

---

## GRAPHIFY — Réduction de tokens (obligatoire sur tous les projets)

graphify cartographie le projet une fois. L'IA navigue par la carte au lieu de lire
tous les fichiers à chaque session. Résultat : 10x à 70x moins de tokens consommés.

| Action | Commande |
|---|---|
| Installation (1 fois/machine) | `pip install graphifyy` |
| Intégration Claude Code (1 fois) | `graphify install` |
| Initialisation projet | `graphify claude install && graphify .` |
| Mise à jour après changements | `graphify . --update` |
| Reconstruction complète | `graphify .` |

Règle session : lire `graphify-out/GRAPH_REPORT.md` avant toute action de code.
Si absent : initialiser graphify en priorité absolue, avant tout autre travail.
