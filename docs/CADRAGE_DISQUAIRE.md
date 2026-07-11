# CADRAGE — Le DISQUAIRE (rangement musical Spotify)

> Document de référence figé. Rédigé le 2026-07-11.
> Nouvel outil greffé dans JARVIS. Statut : cadrage validé, **pas encore construit**.
> Toute construction doit respecter ce document.

---

## 1. Objet

Un agent JARVIS — **le DISQUAIRE** — qui aide Kinder à **trier et ranger ses titres Spotify**
dans son système de playlists personnel, en agissant directement dans son compte, avec
validation humaine par lots.

Le workflow logique existe déjà dans la tête de Kinder. Ce que l'outil apporte : **le temps**.

---

## 2. Le système personnel de Kinder (la cible du rangement)

| Élément | Rôle | Règle |
|---|---|---|
| **`megacompil`** | Coffre-fort : tous les titres | Un titre y est **toujours** |
| Dossier **`Genre`** (playlists préfixées **`g.`**) | Une playlist par genre | Un titre va dans **≥ 1** playlist `g.` — **obligatoire** |
| Dossier **`Mood`** (playlists préfixées **`m.`**) | Une playlist par ambiance | Un titre **peut** y aller (0, 1 ou plusieurs) — **optionnel** |

**Flux quotidien (= étape 2, plus tard) :** playlist `Nouveauté` → Kinder valide → rangement
direct, ou dépôt dans `Validé -- à trier`.

**Pile à trier maintenant :** `On est parti pour trier` (copie de `megacompil`). Tri manuel
commencé, mais trop long → c'est l'entrée de l'étape 1.

**Convention de nommage (décidée) :** Kinder renomme ses playlists avec préfixe **`g.`** (Genre)
et **`m.`** (Mood) → repérage automatique par l'outil, zéro configuration manuelle.

---

## 3. Faisabilité — vérifiée le 2026-07-11

**Verdict : réalisable**, sous 3 contraintes fermes issues des règles Spotify récentes.

| # | Contrainte | Impact | Statut |
|---|---|---|---|
| 1 | **Compte Premium obligatoire** pour toute app en mode développement (règle fév. 2026) | Sans Premium, aucune action possible | ✅ Kinder est Premium |
| 2 | **Les dossiers Spotify sont invisibles** via l'API (limitation de conception, jamais levée) | L'agent ne voit pas les dossiers `Genre`/`Mood`, seulement les **playlists** dedans | ✅ Contourné par les préfixes `g.`/`m.` |
| 3 | **Analyse audio Spotify supprimée** pour les nouvelles apps (énergie/ambiance/tempo, déc. 2024) | Pas d'ambiance fournie par Spotify → source externe pour le Mood | ⚠️ Concerne le **Mood** (étape 2), pas le Genre |

**Ce qu'une app perso peut faire sur SON compte (confirmé) :** créer des playlists, lire/ajouter/
enlever/réordonner les titres de ses playlists, gérer ses Titres Likés. C'est exactement le
rangement voulu.

**Mécanique d'autorisation (sécurité) :** les droits sont donnés **à JARVIS**, pas à un tiers.
Kinder autorise **une fois** via l'écran officiel Spotify ; JARVIS reçoit un jeton renouvelable.
Le mot de passe Spotify n'est jamais saisi par l'outil ni par l'assistant.

**Sources :** blog Spotify 2026-02-06 (mode dev + Premium), guide migration fév. 2026,
blog Spotify 2024-11-27 (analyse audio), doc Playlists (dossiers).

---

## 4. L'équipe — UN agent + des connecteurs

On ne réutilise **aucun** agent existant (MENTOR/FORGE/CASCADE/SENTINELLE/ATELIER/MEDIA/DISC
font tous autre chose). Mais on réutilise **l'infrastructure** JARVIS (système multi-agents,
validation par checkpoint, tableaux de bord, base de données, routage des modèles). DISC et
ATELIER servent de **modèles de patron** (agent-expert / agent qui agit avec validation).

**Distinction clé :**
- **Plomberie = connecteurs** (pas des agents) : la connexion Spotify, plus tard Last.fm.
  Posés une fois, réutilisables.
- **Cerveau = 1 seul agent, le DISQUAIRE.** Il fait 3 gestes internes (collecter → profiler →
  ranger), mais c'est **un** cerveau, pas trois. Plus simple à construire et à comprendre.

Comment le DISQUAIRE décide : il **apprend de Kinder** en lisant ce qui est déjà dans chaque
playlist `g.` (ses frontières à lui), complété par les genres d'artiste Spotify et les
connaissances musicales de l'IA. Rangement **multi-étiquettes** : il propose un *jeu* de
destinations par titre, pas une case unique.

---

## 5. Quelles informations on va chercher (par titre)

| Source | Apport | Étape |
|---|---|---|
| **Spotify** | Titre, artiste(s), album, année, popularité, **genres de l'artiste**, playlist d'origine | 1 |
| **Contenu des playlists `g.` existantes** | Apprentissage de la taxonomie personnelle | 1 |
| **Connaissances de l'IA** | Contexte artiste/morceau | 1 |
| **Last.fm** (tags communautaires d'ambiance) | Le **Mood** (chill, nuit, mélancolique…) | 2 |

**Simplification étape 1 :** le Genre n'a **pas besoin de Last.fm**. Une seule connexion externe
(Spotify) suffit pour le premier passage.

---

## 6. ÉTAPE 1 (MVP) — périmètre figé

**But :** vider la pile `On est parti pour trier` en rangeant chaque titre dans ses playlists
**Genre** (`g.`). Mood **hors scope** de ce passage.

**Tout dans JARVIS.** Aucun logiciel séparé. La seule « app » à créer est la **fiche
d'inscription Spotify** (un formulaire, pas un logiciel).

**Les 5 briques :**

| Brique | Nature | Qui |
|---|---|---|
| 1. Fiche app Spotify (→ 2 identifiants) | Formulaire d'inscription développeur | Kinder, ~10 min |
| 2. Connexion Spotify dans JARVIS | À construire | Construction |
| 3. Agent DISQUAIRE (apprend `g.`, propose un genre) | À construire | Construction |
| 4. Écran de validation par lots | À construire | Construction |
| 5. Coller les identifiants dans Paramètres JARVIS | Config, comme les autres clés | Kinder, ~2 min |

**Déroulé :**
1. **Une fois :** créer la fiche Spotify → coller les 2 identifiants dans JARVIS → cliquer
   « Autoriser ». (+ renommer les playlists en `g.`/`m.`)
2. **Une fois, auto :** le DISQUAIRE lit les playlists `g.` pour apprendre les genres de Kinder.
3. **Grand rangement :** il parcourt la pile, propose des genres par lots → Kinder valide/corrige
   → il range dans les bonnes `g.` → le titre validé **sort de la pile**.

---

## 7. ÉTAPE 2 — plus tard (hors scope actuel)

- **Passage Mood** : ambiance via Last.fm (connecteur à ajouter).
- **Automatisation** : surveiller la playlist `Nouveauté` en continu (le planificateur interne
  de JARVIS existe déjà) → proposer un rangement à chaque nouveau titre.

---

## 8. Décisions figées

| Date | Décision |
|---|---|
| 2026-07-11 | Le nouvel outil est **un agent JARVIS** (le DISQUAIRE), pas un logiciel séparé — tout dans JARVIS |
| 2026-07-11 | **Un seul agent**, pas trois. Les connexions Spotify/Last.fm sont des connecteurs, pas des agents |
| 2026-07-11 | Étape 1 = **Genre uniquement**, sur la pile `On est parti pour trier`. Mood + automatisation = étape 2 |
| 2026-07-11 | Repérage des playlists cibles par **préfixes `g.` / `m.`** (dossiers Spotify invisibles via l'API) |
| 2026-07-11 | Étape 1 **sans Last.fm** — une seule connexion externe (Spotify) |
| 2026-07-11 | Autorisation Spotify donnée à JARVIS via l'écran officiel, jeton renouvelable — jamais de mot de passe saisi par l'outil |

---

## 9. Pré-requis AVANT de construire (nettoyage de la base)

Rappel du point de départ : solidifier la base avant d'ajouter un étage. À solder d'abord :

1. **Chantier WIP non rangé** : dernier commit marqué « en cours » + 3 fichiers modifiés non
   enregistrés → nettoyer / clôturer.
2. **Incohérence doc MEDIA** : PROJET_CONTEXTE dit « bascule vers fal.ai » alors que le dernier
   changement est revenu à Pollinations → réaligner la fiche projet.
3. **Acter les nouveaux services** : le DISQUAIRE + connecteur Spotify ajoutent des services
   (limite des 20 dépassée — Kinder a validé le dépassement pour ce projet) → mettre à jour
   PROJET_CONTEXTE (architecture + décisions figées).

---

## 10. À trancher plus tard (non figé)

- Comment Kinder valide « par lots » concrètement (taille des lots, écran) — à préciser à la
  construction de la brique 4.
- Faut-il retirer les titres de `On est parti pour trier` automatiquement après rangement, ou
  après un second OK ?
- Nom définitif de l'agent (« DISQUAIRE » est provisoire, cosmétique).
