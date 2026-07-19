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
| 2026-07-11 | Adresse de retour Spotify (redirect URI) figée : `http://127.0.0.1:8000/api/spotify/callback` — identique côté app Spotify et côté JARVIS. Loopback `127.0.0.1` obligatoire (Spotify refuse « localhost ») |
| 2026-07-15 | **Amendement** : JARVIS passe du port **8000 → 8010** (le 8000 est occupé par un autre projet). Redirect URI = `http://127.0.0.1:8010/api/spotify/callback`. **À reporter sur la fiche app Spotify** avant toute reconnexion (le jeton actuel continue de fonctionner sans ça). |

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

---

## 11. Journal de construction

| Mission | État | Détail |
|---|---|---|
| **1. Connexion Spotify** | ✅ **Terminée** (2026-07-13, commit 8847f57) | OAuth + lecture playlists. Page `/app/spotify.html`. Testé end-to-end (compte « Keamder », playlists lues, préfixes `g.`/`m.` repérés). |
| **2. Le cerveau + rangement par lots (Genre)** | ✅ **Validée en vrai** (2026-07-13) | Classification IA multi-genres, chips éditables, ajout dans G. (anti-doublon) + retrait pile. Formats API /items résolus : add=`{"uris":[...]}`, remove=`{"items":[{"uri":...}]}`. |
| **3. Phase « Recenser » (base locale)** | ✅ **Validée en vrai** (2026-07-13) | Migration v8 (3 tables), recensement en tâche de fond + progression, incrémental via snapshot_id. Test réel : 2437 titres, 38 genres, 27 moods, pile. |
| **4. Brancher la base locale dans le tri** | ⏳ Prochaine | Signatures du cerveau sur contenu local complet (meilleure justesse) + affichage par titre « déjà dans : … » (get_track_memberships). |

### Cadre Mission 2 (décidé le 2026-07-13)

**Périmètre :** le DISQUAIRE apprend les genres depuis les playlists `G.`, puis traite la pile
« On est parti pour trier » **par lots** : pour chaque titre d'un lot, il propose une/des
playlist(s) `G.`, Kinder revoit tout le lot, valide, et le DISQUAIRE **range lui-même**
(ajout dans les `G.` + retrait de la pile).

**Décisions Kinder :**
- Traitement **par lots** directement (pas titre par titre).
- Le DISQUAIRE **applique automatiquement** après validation (écrit dans le compte).

**Garde-fous (car on écrit dans le compte réel) :**
- Détection des préfixes **insensible à la casse** (`G.` = `g.`).
- **Revue du lot entier AVANT tout écrit** : Kinder peut décocher/corriger chaque ligne.
- Lots de **taille raisonnable** (≈ 25 titres) pour rester revoyable + respecter les limites Spotify.
- **Anti-doublon** : si un titre est déjà dans la playlist `G.` cible, on ne le rajoute pas.
- On **ne retire de la pile que** les titres effectivement rangés.
- `megacompil` **jamais touchée** — la pile est une copie de travail (pire cas = titre mal rangé, corrigé d'un clic).

**Je décide (technique) :** modèle d'IA du tri (économique d'abord, montée en gamme si faible),
résumé compact des playlists `G.` pour rester léger, ordre de traitement (haut de pile).

### Cadre Mission 3 — Phase « Recenser » (préparé le 2026-07-13)

**Objectif :** aspirer une fois toute la bibliothèque Spotify dans la base locale de JARVIS,
pour que le tri travaille sur une copie locale complète (idée de Kinder).

**Ce qu'on stocke (3 tables dans jarvis.db) :**
- `disquaire_tracks` : catalogue des titres (uri, nom, artistes).
- `disquaire_playlists` : id, nom, **type** (megacompil / genre / mood / pile / autre), snapshot_id, date de synchro.
- `disquaire_membership` : quel titre est dans quelle playlist (le lien).

**Le geste « Recenser » :**
- Un bouton → JARVIS parcourt les playlists pertinentes et remplit la base locale.
- **Tâche de fond avec barre de progression** (≈ 1-3 min pour ~2235 titres + 38 genres + moods + pile).
- **Rejouable** : un « Rafraîchir » qui ne relit que ce qui a changé (via snapshot_id Spotify).
- On recense **tout** (y compris Mood) en une fois.

**Ce que ça débloque pour le tri (répond aux 3 retours Kinder) :**
- Signatures de genre construites sur le contenu **complet** (plus 60 titres) → tri plus juste.
- Affichage par titre « déjà présent dans : G. Rock, M. Chill ».
- Suivi de progression (rangés / restants), anti-doublon parfait, rapidité (plus d'appels Spotify en direct pour trier).

**Ensuite :** le tri Genre (Mission 2) bascule sur la base locale ; puis Mood (Last.fm) + automatisation.

---

## 12. VISION DES GENRES — figée le 2026-07-14

> Restructuration complète des playlists `G.` après audit de la base réelle.
> Méthode : Vision → **Figer** → Plan → Exécution. Cette liste est la référence du tri.

### Principe de classement (figé)
- **Genre = IDENTITÉ musicale** (style, scène). **Mood = énergie / moment** (quand et dans quel état on écoute).
- Un titre = **1 genre + 1 à n moods**.
- **3 axes INTERDITS comme genres** (les « maladies ») : **langue/origine · énergie/moment · époque**.
- Interdit aussi : **un artiste/groupe** pris pour un genre.
- La liste des genres autorisés = **exactement les playlists `G.` du compte, lues en direct à chaque tri** (rien en dur, aucun cache).

### Exceptions assumées (dérogations volontaires au principe)
| Exception | Axe dérogé | Cas concernés |
|---|---|---|
| **Formats dans les genres** | format | `Live`, `Reprise`, `Freestyle`, `BO film`, `Disney` |
| **Chill-X** | énergie (sous-scène réelle) | `Chill pop`, `Électro Chill` |
| **Énergie = sous-scène nommée** | énergie (sous-scène réelle) | `Pop dance` (electropop), `Fat Beat` (électro festival) |
| **Époque assumée** | époque | `Rap old school` (nom conservé par choix) |
| **Artiste-genre** | artiste | `Chinese-man crew` |

### Cas particuliers de nommage (identité, pas langue)
- **`Variété`** : nomme la **tradition** chanson/variété francophone (Piaf → Pokora), pas la langue —
  au même titre que Reggae (jamaïcain) ou Fado (portugais). C'est pourquoi il est autorisé alors
  qu'un couple « Pop FR / Pop international » (= découpe par langue) resterait **interdit**.

### LISTE FIGÉE — 27 genres
| Famille | Genres (`G.`) |
|---|---|
| **Rap** | Rap de rue · Rap old school · Pop Culture *(rap mainstream FR mélodique)* · Rap US |
| **Rock** | Rock · Rock soul |
| **Pop** | Pop *(pop-rock/mainstream, fourre-tout surveillé)* · Pop dance · Chill pop · **Variété** *(nouveau)* |
| **Électro** | House · Électro Chill · Dub · Dub Singing · Fat Beat · Drop d'un autre temps |
| **Monde** | **Monde / Latino** *(nouveau)* |
| **Autres** | Jazz · Reggae · Classique · Beauf · Chinese-man crew |
| **Formats** | Live · Reprise · Freestyle · BO film · Disney |

### Changements vs l'état antérieur
- **Créés** : `Variété`, `Monde / Latino`.
- **Supprimé** : `Progressif` (énergie pure + doublon) → titres versés dans `Fat Beat`.
- Reste inchangé (23 genres).

### Points sous surveillance (règle : ne pas pré-découper, trancher sur titres réels si ça explose)
- **`Pop`** : accueille la pop-rock internationale ; si gonflement, prochain découpage par **style** (pas par langue).
- **`Chill pop`** : dans la base, ~95 % rap FR mélodique → chevauche `Pop Culture`. À surveiller.

### Trou de couverture assumé
- Titres sans genre correspondant → **restent dans la pile** « On est parti pour trier » (pas de rangement forcé, conforme au principe).

---

## 13. MOODS — automatisation ABANDONNÉE (décision figée le 2026-07-15)

> **Ne pas rouvrir ce sujet sans nouvelle source de données.** Les 3 sources possibles ont été
> testées en vrai sur la bibliothèque de Kinder — pas supposées. Toutes échouent.

### Pourquoi le mood est un problème différent du genre
Un **genre** est une identité : l'IA *connaît* les artistes, et là où elle bute on lui donne les
genres d'artiste Spotify (branchés le 2026-07-15). Un **mood** est une **énergie ressentie** :
il faut *entendre* le morceau. L'IA ne peut que deviner depuis le titre et le nom de l'artiste.

**Preuve vécue :** sur `Fat Beat`, l'IA a signalé à tort 3 titres (Bagarre, Salut C'est Cool ×2)
en raisonnant sur la réputation de l'artiste (« électro pop légère ») alors que les morceaux sont
du « gros boom boom ». Seul Kinder, qui les a écoutés, pouvait trancher. Sur 2452 titres et
31 moods qui se chevauchent déjà à 46-65 %, ce biais serait systématique.

### Les 3 sources testées le 2026-07-15 — résultats
| Source | Ce qu'elle donnerait | Résultat réel mesuré |
|---|---|---|
| **Spotify `/audio-features`** (énergie, valence, dansabilité) | La donnée idéale | **HTTP 403** — coupé par Spotify pour les apps récentes (déc. 2024). Confirme le § 3. |
| **Spotify `/audio-analysis`** (tempo détaillé) | Complément | **HTTP 403** |
| **Last.fm — tags de TITRE** | Ambiance communautaire | **8 %** de couverture (5/60 titres tirés au hasard dans megacompil) |
| **Last.fm — tags d'ARTISTE** | — | 100 % de couverture, mais **uniquement du genre et de la langue** (« rap », « french », « rap francais », « belgian ») → inutilisable, et contraire au principe (langue/origine interdites) |

**Détail Last.fm :** les tags de titre n'existent que pour les classiques anglo-saxons
(Queen, Bob Marley → 10 tags). **Zéro tag** sur les artistes français, même les plus connus :
Orelsan *Basique*, Stromae *Alors On Danse*, Daft Punk *Get Lucky*. La bibliothèque étant
massivement francophone, Last.fm est aveugle sur ~90 % d'elle.

### Décision
- **Pas de tri automatique des moods.** Seuil annoncé avant le test : 50 % de titres avec une
  ambiance exploitable. Résultat : **8 %**. No-go.
- Les moods restent **100 % manuels** (comme la famille `P.`, cf. ci-dessous).
- **Réouvrir uniquement si** une nouvelle source d'ambiance par titre apparaît (retour des
  audio-features Spotify, ou autre fournisseur). Le connecteur Last.fm n'a **pas** été construit.

### État de la famille Mood (audit du 2026-07-15, aucune action prise)
- **31 playlists `M.`** · couverture : **55 %** de megacompil a ≥1 mood → **1113 titres (45 %) n'en ont aucun**.
- **Chevauchements forts** (non tranchés) : `Douceur`/`Chill relax` **59 %** · `Party`/`Calor` **65 %** ·
  `Party`/`DANCING` **61 %** · `Chill relax`/`Wake up chill` 46 %.
- **Playlists mortes** : `M.Jazz Beat` (vide) · `M.Reage` (1 titre, déjà dans `G.Dub Singing`).
- **Coquilles** : `M.Elctro de fond` · `M.24K - Sunchine` · `M.Lets get's ready` ·
  `M.Une étoile au millieu` · `M. DANCING` (espace parasite).
- **Orphelins** (aucun genre) : *Thank God* (Rilès) · *Sweet Child O' Mine* (Guns N' Roses).

### Exceptions assumées par Kinder (famille Mood)
| Cas | Décision |
|---|---|
| **Famille `P.`** (17 playlists : Runner's high, Démarrage en douceur, 🚗❤🚗…) | **Hors périmètre de l'outil** — ce sont « les pépites », curation 100 % manuelle. Les doublons M./P. relevés (`Décibels vocaux`/`Besoin de chanter` 83 %, `Old School vibes`/`Nostalgie` 90 %) sont donc **voulus**. |
| **`P.🚗❤🚗`** (376 titres, chevauche tout) | **Fourre-tout assumé.** |
| **`M.Multi connu`** (notoriété) · **`M.Pépite Auditive`** (qualité) · **`M.Passe partout`** (polyvalence) · **`M.Parole consciente`** (thème de texte) | **Assumées** : ne décrivent ni une énergie ni un moment, mais conservées volontairement. |
| **`M.Flow Kiffant`** · **`M.Mix Drop`** · **`M.Elctro de fond`** | **Conservées.** D'abord suspectées d'être des genres déguisés — vérification faite, leur contenu traverse 6 genres chacune (ex. `Mix Drop` → Variété 28, Rock 18, Freestyle 18, Électro 17). Ce sont de **vrais moods mal nommés**, jugés à tort sur leur nom. |

---

## 14. MODE « MOOD ASSISTÉ » — cadrage figé le 2026-07-16

> **Amende la section 13** : le tri *automatique* des moods reste abandonné (sources d'ambiance
> inexistantes — chiffres § 13). Ce qui est validé ici est un **mode ASSISTÉ** : l'IA dégrossit,
> **Kinder valide tout**, et un fort taux de « sans proposition » est **attendu et accepté**
> (c'est le premier tri manuel voulu). La différence avec le fiasco évité : les **définitions
> écrites de Kinder** (référentiel ci-dessous) remplacent la devinette sur les noms.

### Principe
Le pipeline Genre existant, à destination des `M.` : Kinder remplit la pile « On est parti pour
trier » → Recenser → analyse complète → par titre : 🟢 moods à ajouter + 🔵 moods déjà en place
avec **proposition de retrait** si incohérent → validation → application.

### Règles
- 0 à n moods par titre. Sans proposition → le titre **reste dans la pile** (rien de forcé).
- Sort de la pile uniquement un titre validé avec ≥ 1 mood.
- L'IA revoit AUSSI les placements existants (retraits proposés).
- `P.` (pépites) · `megacompil` · genres `G.` : **intouchés**.
- Indices fournis à l'IA : définitions de Kinder (mot pour mot) + genres d'artiste Spotify +
  tags Last.fm de titre quand ils existent (~8 % — bonus gratuit, jamais décisif seul).

### RÉFÉRENTIEL DES MOODS — 6 axes, définitions de Kinder (source de vérité du prompt)

**Axe 1 · Ça bouge comment ? (danse)**
| Mood | Définition | Frontière |
|---|---|---|
| `Party` | Électro dancefloor, let's go | danse **électro club** |
| `Son de teuf` | Gros boom boom de teufeur | plus dur que Party — la **teuf** |
| `Calor` | Rythme espagnol, tango, déhanché | la danse **latine** |
| `DANCING` | Besoin de bouger, danser | **le reste** qui fait danser (funk, rock'n'roll, disco) — ni électro ni latin |

**Axe 2 · Ça m'énergise ? (boost)**
| `Patate d'enfer` | Coup de punch, go go go | boost générique |
| `Lets' get ready` | Séance de salle, motivation sport | boost **d'effort** |
| `Sombre Dynamique` | Rap sombre, méchant et boostant | boost **agressif** |

**Axe 3 · Ça m'apaise ? (calme)**
| `Douceur` | Tout doux, **presque pas de texte** | quasi instrumental — critère discriminant |
| `Chill relax` | Tranquille, détendu | posé **avec** voix/texte |
| `Wake up chill` | Dimanche matin, réveil café | le calme **du matin** |

**Axe 4 · Ça me fait quoi ? (émotion)**
| `Mélancolie` | Triste, rupture, ça va pas |
| `24K - Sunshine` | Joyeux, soleil, ça donne envie |
| `Espoir Héroïque` | Donne espoir, on se sent fort, héroïque |
| `You're crazy of course` | Zinzin, un peu débile, ça fait du bien |
| `Une étoile au milieu de la nuit` | Tête dans les étoiles, la mélodie m'emporte (rêverie ≠ tristesse) |
| `Voyage` | Envie de partir, inspiration internationale (1 titre — sera nourrie par le tri, candidats naturels : `G.Monde`) |
| `Mignon` | Toutes les chansons d'amour — mode « loveur » *(définie le 2026-07-16, entre au tri)* |

**Axe 5 · Je l'écoute quand/comment ? (usage)**
| `Casque Session` | Au casque, puissance mélodique monstrueuse, variations |
| `Au bistrot` | Accordéon, chorale, chanson à boire |
| `Électro de fond` | Électro d'arrière-plan |

**Axe 6 · Je le connais ? (mémoire & notoriété)**
| `Memories` | Titres **2000-2018**, époque collège/lycée, écoutés en boucle |
| `Multi connu` | Les titres que tout le monde connaît (notoriété universelle) |
| `Besoin de chanter ?🎤` | Connu par cœur, à chanter à tue-tête |

**Rap à texte (transverse)**
| `Flow Kiffant` | La **forme** : flow musical, beat entraînant | 
| `Parole consciente` | Le **fond** : paroles fortes, remise en question, philosophie |

**Cohérence globale :** un titre peut cumuler des moods d'axes différents ; deux moods du même
axe sur un titre = exception à justifier, pas la norme.

### Exclus du tri (les playlists restent, l'outil n'y touche jamais)
`Pépite Auditive` (goût de Kinder) · `Mix Drop` · `Passe partout` · toute la famille `P.`

### Décisions d'organisation prises le 2026-07-16
- **`M.Nostalgie` (456 titres) supprimée** par Kinder ; `M.Memories - Collège` renommée `M.Memories`
  et devient LE mood mémoire (déf. 2000-2018). **Sauvegarde du contenu supprimé :
  `docs/backup_nostalgie.txt`** (456 titres, exportés avant purge de la base locale).
- `M.Jazz Beat` (vide) et `M.Reage` (1 titre) **supprimées**.
- Coquilles corrigées : Sunshine · milieu · Électro de fond.

### En suspens
- Cosmétique : `M. DANCING` (espace parasite) · `M.Lets' get ready` (apostrophe mal placée).
- **La construction du mode mood est une mission à part** (prompt mood, bascule genre/mood,
  apply vers `M.`) — cadrée ici, à construire et tester avant tout lancement.
- Coût estimé d'une passe complète (~2450 titres) : **1,50-2 $** (mesurable au journal).
