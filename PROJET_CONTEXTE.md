# PROJET_CONTEXTE — JARVIS

> Source de vérité absolue. Lire EN ENTIER avant toute action.
> Toute décision qui contredit ce fichier est interdite.

---

## 1. IDENTITÉ

|
 Champ 
|
 Valeur 
|
|
---
|
---
|
|
 Nom 
|
 JARVIS 
|
|
 Type 
|
 Outil IA / Agent 
|
|
 Objectif 
|
 Interface locale d'orchestration de workflows IA multi-modèles, remplaçant Claude Projects + Cascade. Tourne sur localhost, écrit les fichiers projet directement, orchestre des appels vers plusieurs modèles via OpenRouter. 
|
|
 Statut 
|
 En développement 
|
|
 Utilisateurs 
|
 1 (usage personnel, Windows 10, localhost uniquement) 
|
|
 Dernière mise à jour 
|
 2026-04-16 
|

---

## 2. STACK TECHNIQUE

**Frontend :** HTML5 + CSS3 + JavaScript vanilla (fetch natif, zero framework)
**Backend :** FastAPI Python 3.11+ — port 8000
**Base de données :** SQLite natif Python (`sqlite3`) — fichier `backend/data/jarvis.db`
**Gestion chemins :** `pathlib.Path` systématiquement (compatibilité Windows)
**Appels modèles :** OpenRouter API via `httpx` (async) — endpoint : `https://openrouter.ai/api/v1/chat/completions`
**Clés directes optionnelles :** Anthropic, Google (fallback si OpenRouter indisponible)
**Config :** Table `app_config` dans `jarvis.db` (clés API) + `backend/data/config.json` (préférences modèles uniquement)
**Workflows :** `backend/data/pipelines.json` (6 workflows définis comme données)
**Prompts :** `backend/data/prompts.json` (44 templates par étape, variables `{{var}}`)
**Diff :** `difflib` Python stdlib (unified diff) — rendu CSS côté frontend
**Démarrage :** `start.bat` à la racine (lance uvicorn + ouvre navigateur)

---

## 3. ARCHITECTURE


JARVIS/
├── start.bat                  ← démarrage Windows (double-clic)
├── requirements.txt
├── PROJET_CONTEXTE.md
├── CHANGELOG.md
├── backend/
│   ├── main.py                ← FastAPI app, CORS, routes, static files, migration SQLite
│   ├── database.py            ← get_connection, migrations tables
│   ├── routers/
│   │   ├── projects.py        ← CRUD projets (+ champ instructions, local_path)
│   │   ├── pipelines.py       ← start, status, validate step, retry step, abort, logs
│   │   ├── models.py          ← config clés API (SQLite), test connexion, modèles disponibles
│   │   ├── files.py           ← read, write, diff, apply, archive docs, local-list
│   │   ├── chat.py            ← conversations, messages, titrage auto
│   │   ├── atelier.py         ← CRUD prospects, start pipeline atelier, export ZIP
│   │   └── config.py          ← routes clés API génériques + profil utilisateur (FIX-01)
│   ├── services/
│   │   ├── pipeline_engine.py ← state machine, orchestration, persistance
│   │   ├── model_router.py    ← sélection modèle, appel API, log décisions
│   │   ├── context_manager.py ← construction context envelopes par étape
│   │   ├── file_service.py    ← pathlib, diff, rollback all-or-nothing
│   │   ├── chat_service.py    ← historique messages, titrage auto, lecture dossier local, web search
│   │   └── atelier_service.py ← logique pipeline atelier, export ZIP fichiers démo
│   ├── schemas/
│   │   ├── project.py
│   │   ├── pipeline.py
│   │   └── config.py
│   └── data/
│       ├── jarvis.db          ← SQLite (tables: projects, sessions, pipeline_steps, conversations, messages, app_config, prospects)
│       ├── config.json        ← model_preferences uniquement (clés API dans jarvis.db)
│       ├── pipelines.json     ← 6 workflows Module Code + workflow atelier_prospection
│       └── prompts.json       ← templates prompts par step
└── frontend/
    ├── index.html             ← dashboard (timeline activité, sessions actives/bloquées, stats)
    ├── dossier.html           ← hub projet/dossier (remplace project.html)
    ├── code-projects.html     ← liste projets Module Code (bouton Nouvelle Mission par projet)
    ├── mission.html           ← page unique Mission : Zone 1 Réflexion + Zone 2 Livrable + Zone 3 Pipeline
    ├── chat.html              ← conversation IA (markdown, folder_path, web search, sélecteur modèle)
    ├── atelier.html           ← Atelier Connecté (kanban 6 colonnes + vue pipeline prospect)
    └── settings.html          ← config clés API 3 providers + sélecteurs modèles par type
    └── assets/
        ├── style.css          ← thème sombre, variables CSS, layout 3 panneaux, composants
        └── js/
            ├── api.js         ← toutes les routes API (BASE_URL = window.location.origin)
            ├── shared.js      ← renderMarkdown, formatDate, statusBadge, costBadge, escapeHtml
            ├── sidebar.js     ← sidebar collapsible, modals nouveau chat/module/projet/reflexion
            ├── ui.js          ← showModal, closeModal, showToast
            ├── dashboard.js   ← timeline, sessions actives/bloquées, stats semaine
            ├── project.js     ← hub projet, instructions éditables, liste unifiée sessions+chats
            ├── code-projects.js  ← liste projets Module Code (bouton Nouvelle Mission)
            ├── mission.js     ← orchestrateur unique Mission (réflexion + figement + pipeline en une page)
            ├── chat.js        ← messages, optimistic UI, sélecteur modèle, suppression
            ├── explorer.js    ← arborescence fichiers locaux, preview, collapse
            ├── atelier.js     ← kanban prospects, vue pipeline atelier, zones saisie/checkpoint/export
            └── settings.js    ← clés API (états visuels), test connexion, dropdowns modèles

**Services backend actifs :** 7 / 20 maximum
**Pages frontend :** 8 / illimité

---

## 4. FONCTIONNALITÉS

**✅ Stables**
- Gestion projets CRUD (enregistrement, liste, suppression, instructions, local_path)
- Pipeline engine complet (6 workflows Module Code, state machine, persistance SQLite)
- Routing modèles par type de tâche (routing/structuring/code/analysis)
- Configuration modèles : routing=Gemini Flash, code=Claude Haiku 4.5, analysis=Claude Sonnet 4.5
- Clés API dans SQLite (table app_config), migration auto depuis config.json au démarrage
- Rollback atomique apply_files (3 phases), parsing diff 3 fallbacks
- Clôture auto PROJET_CONTEXTE.md section 8 + CHANGELOG.md
- Logs applicatifs : jarvis.log + GET /pipelines/logs
- **Frontend V2 complet** : layout 3 panneaux (sidebar collapsible, main, explorer), 8 pages, 11 modules JS
- **Page Mission unique** : zone conversation + livrable + pipeline dans une seule page, 3 zones progressives, polling 5s, validation diff/generic
- **Module Code** : pipeline exécuté depuis mission.html Zone 3, retry step, breadcrumb projet
- **Module Réflexion** : session conversationnelle → figement → livrable (mission_code / decision_figee / plan_multi_missions)
- **Module Chat** : lecture dossier local (GRAPH_REPORT prioritaire), web search Brave API, sélecteur modèle
- **Module Projet** : hub conteneur (instructions, local_path, liste unifiée sessions+chats)
- **Atelier Connecté** : kanban 6 colonnes, pipeline 13 steps pour prospects restauration, export ZIP démo HTML
- **Atelier pipeline** : 3 moments humains (form saisie terrain → checkpoint validation → export ZIP)
- Startup recovery : sessions RUNNING → FAILED au démarrage (crash server)
- Seed automatique clés API : .env → SQLite au démarrage
- Toast system, modales confirmation, états vides, dashboard pipelines actifs/bloqués

**🚧 En cours**
- Audit complet (6 phases) terminé 2026-05-03 — corrections Sprint 1 à planifier

**❌ Bugs connus — Audit 2026-05-03**

| ID | Sévérité | Module | Description | Fichiers | Statut |
|---|---|---|---|---|---|
| BUG-01 | ✅ RÉSOLU | Sidebar | Valeur par défaut `reflexion_simple` viole la contrainte CHECK SQLite → réflexion jamais créée | `sidebar.js:handleNewMission()` | Vérifié 2026-05-03 : aucun code n'envoie cette valeur, flux fonctionne correctement |
| BUG-02 | ✅ RÉSOLU | Sidebar→Mission | URL `?livrable_type=X` générée mais ignorée par `mission.js init()` → page mission blanche | `mission.js:init()` | Vérifié 2026-05-03 : mission.js lit correctement le paramètre 'new' |
| BUG-03 | ✅ RÉSOLU | Dossier | Renommage dossier silencieusement ignoré : PATCH ne traite pas le champ `name` | `routers/projects.py:update_project()` | Corrigé 2026-05-03 : requête UPDATE ligne 350-352 incluait déjà name, commentaire ajouté |
| BUG-04 | ✅ RÉSOLU | Sidebar | `btn-new-reflexion` redirige vers `code-projects.html` au lieu de créer une réflexion | `sidebar.js:~btn-new-reflexion` | Vérifié 2026-05-03 : redirige vers mission.html correctement |
| BUG-05 | ✅ RÉSOLU | Chat | `update_conversation_summary` : kwarg `model_preferences` inexistant + `result["content"]` (string, pas dict) → TypeError | `routers/chat.py:update_conversation_summary()` | Corrigé 2026-05-03 : vrai bug était AttributeError sur db_conn.cursor(), condition ajoutée model_router.py ligne 63 |
| BUG-06 | 🟠 | Dashboard | Sessions Réflexion absentes de la timeline et des stats | `dashboard.js:buildTimeline()` | À corriger |
| BUG-07 | 🟠 | Chat | `PATCH /conversations/{id}/folder` : frontend envoie JSON, backend attend query param | `routers/chat.py` / `api.js` | À corriger |
| BUG-08 | ✅ RÉSOLU | Chat | Crash serveur TypeError au déclenchement de `update_conversation_summary` (même cause que BUG-05) | `routers/chat.py` | Corrigé 2026-05-03 : même correction que BUG-05 (db_conn optionnel) |

**⚠️ Fragilités structurelles — Audit 2026-05-03**

| ID | Module | Description | Risque |
|---|---|---|---|
| FRAG-01 | Backend | `load_config()` dupliquée verbatim dans `chat.py` et `pipelines.py` | Divergence silencieuse |
| FRAG-02 | Backend | `print("DEBUG ...")` en production dans `pipelines.py` et `pipeline_engine.py` | Pollution logs |
| FRAG-03 | Pipeline | Reject d'une étape → ABORTED définitif, aucune possibilité de relancer avec feedback | Perte de session |
| FRAG-04 | Pipeline | Step `sante_cadrage` marquée COMPLETED avec `output_data=null` (rapport jamais peuplé) | Données incohérentes |
| FRAG-05 | Contexte | 3 sources non synchronisées : SQLite / `contexts/*.md` / `backend/data/methodo/` | Injection silencieuse d'un mauvais contexte |
| FRAG-06 | Réflexion | Modèle `claude-sonnet-4.5` hardcodé dans `reflexion_service.py` — non configurable | Impossible à changer depuis Paramètres |
| FRAG-07 | Réflexion | `VALID_MODEL_SLUGS` utilise tirets (`claude-sonnet-4-5`) vs points ailleurs (`claude-sonnet-4.5`) | Validation bloque des slugs valides |

**🎨 Problèmes UX — Audit 2026-05-03**

| ID | Sévérité | Description | Fichier | Statut |
|---|---|---|---|---|
| UX-01 | 🔴 | Statut `FAILED` affiché en texte brut anglais sans badge | `ui.js:statusBadge()` | ✅ RÉSOLU 2026-05-03 : badge rouge ajouté dans sidebar.js |
| UX-02 | 🟠 | `ABORTED` visuellement identique à `PENDING` (même couleur grise) | `ui.js:statusBadge()` | ✅ RÉSOLU 2026-05-03 : badge gris distinct ajouté dans sidebar.js |
| UX-03 | 🟠 | Auto-test clés API au chargement Paramètres → spinners + toasts d'erreur spontanés | `settings.js:testAllProviders()` |
| UX-04 | 🟠 | Aucun bouton retour visible après abandon en étape 1 ou 2 de mission.html | `mission.html:step-4-footer` |
| UX-05 | 🟡 | Étapes 3-4 affichées "En attente" pour `decision_figee` (ne s'activent jamais) | `mission.html` |
| UX-06 | 🟡 | Deux zones "contexte global" dans Paramètres sans distinction claire | `settings.html` |
| UX-07 | 🟡 | Bouton "Réinitialiser" Atelier label trompeur (supprime tout) | `atelier.html` |
| UX-08 | 🟡 | Emoji 📋 sur bouton "Sauvegarder le résumé" (devrait être 💾) | `chat.html:49` |

**🔒 Hors scope MVP**
- Authentification
- Multi-utilisateurs
- Déploiement cloud
- Analytics tokens en temps réel dans l'UI
- Éditeur de diff interactif (V2)
- Historique et replay complets (V2)

---

## 5. RÈGLES SPÉCIFIQUES AU PROJET

- `config.json` ne doit jamais être commité (clé API) — utiliser `.gitignore`
- Toute modification de `pipelines.json` doit rester cohérente avec `prompts.json`
- Les modèles OpenRouter doivent être validés avant d'être ajoutés à la liste
- Tous les chemins de fichiers passent par `pathlib.Path` (Windows compatibility)
- Un seul pipeline actif par projet à la fois — toute tentative de second démarrage est bloquée
- Aucune écriture sur fichiers projet sans que l'utilisateur ait cliqué "Appliquer"
- L'application atomique utilise des fichiers `.tmp` renommés — si une écriture échoue, tout est annulé
- `context_manager.py` est le SEUL service qui lit PROJET_CONTEXTE.md — jamais en direct depuis pipeline_engine
- Graphify est optionnel : si `graphify` n'est pas disponible dans le PATH, l'étape est SKIPPED avec avertissement

---

## 6. DÉCISIONS FIGÉES

| Date | Décision | Raison |
|---|---|---|
| 2026-04-14 | Stack : FastAPI + HTML/JS vanilla + SQLite | Standard METHODO Outil IA |
| 2026-04-14 | Provider principal : OpenRouter | Une clé, tous les modèles |
| 2026-04-14 | Chemins via pathlib.Path | Compatibilité Windows backslash |
| 2026-04-14 | Application fichiers : all-or-nothing | Éviter état partiel corrompant le projet |
| 2026-04-14 | Validation humaine : 2 checkpoints max par workflow | Éviter friction excessive |
| 2026-04-14 | Un pipeline actif par projet | Simplifier la state machine |
| 2026-04-14 | context_manager seul lit PROJET_CONTEXTE | Éviter chevauchement services |
| 2026-04-14 | Graphify : subprocess optionnel | Dépendance externe, ne pas bloquer si absent |
| 2026-04-14 | Diff apply : tout ou rien | Rollback fiable sur multi-fichiers |
| 2026-04-15 | Graphify initialisé | Réduction tokens — carte code générée |
| 2026-04-15 | Modèles par défaut | routing=Gemini Flash, structuring=Gemini Flash, code=Claude Haiku 4.5, analysis=Claude Sonnet 4.5 |
| 2026-04-15 | Architecture pipeline | SQLite sans ORM, sqlite3.Row (pas dict) — ne pas changer |
| 2026-04-15 | Configuration modèles définitive | routing=Gemini Flash 001, structuring=Gemini Flash 001, code=Claude Haiku 4.5, analysis=Claude Sonnet 4.5 |
| 2026-04-15 | Tests automatisés | 120 tests unitaires + intégration, live séparés (-m live), pytest-asyncio mode=auto |
| 2026-04-15 | Plans formalisés | Plan METHODO (6 fichiers) + Plan JARVIS (4 phases) exécutés via 5 prompts Cascade |
| 2026-04-16 | Module code validé | 5 P1 résolus — module code structurellement solide avant module chat |
| 2026-04-16 | Logs applicatifs | jarvis.log (RotatingFileHandler 1Mo/3 fichiers) + GET /pipelines/logs — standard pour tous les modules suivants |
| 2026-04-16 | Module chat : périmètre élargi | Lecture dossier local + accès internet inclus dans le module chat (pas reporté au module projet) |
| 2026-04-16 | project_id nullable sur conversations | Toute conversation chat aura un project_id nullable dès maintenant — évite migration future |
| 2026-04-16 | Architecture module projet | Un projet est un conteneur : il regroupe missions code + conversations chat + contexte partagé + lien dossier local |
| 2026-04-16 | start.bat : corrigé | python -m uvicorn + start /min + pause — lancement double-clic fonctionnel |
| 2026-04-17 | Frontend V2 : architecture JS modulaire | 13 fichiers JS séparés (api.js, shared.js, sidebar.js, ui.js, dashboard.js, project.js, code-projects.js, code-project-detail.js, module-code.js, chat.js, explorer.js, atelier.js, settings.js) — pas de bundler, pas de framework |
| 2026-04-17 | Clés API migrées dans SQLite | config.json ne contient plus que model_preferences — clés API dans table app_config (migration auto au démarrage) |
| 2026-04-17 | Atelier Connecté : un pipeline par prospect | Un prospect = une seule session atelier. startAtelierPipeline bloqué si session existante. Recycle n'est pas prévu : démo générée → prospect marqué contacté → fin de cycle |
| 2026-04-17 | Atelier vs Module Code : paradigmes différents | Module Code = session-centré (session visible dans sidebar sous le projet). Atelier = prospect-centré (kanban, prospect est l'entité principale). Les deux utilisent le même pipeline_engine |
| 2026-04-18 | UX Refactoring : 6 missions frontend | Décision : corriger les trous UX identifiés par audit (pages mortes, compteurs trompeurs, friction lancement). Aucun changement backend sauf FRONT-03 (ajout session_status dans GET /atelier/prospects) |
| 2026-05-01 | Pipeline scindé en deux modules : Réflexion + Code | Reproduire dans JARVIS le découpage mental qui fonctionne en méthode actuelle Claude+Cascade — penser puis faire, jamais les deux dans le même workflow |
| 2026-05-01 | Module Chat ≠ Module Réflexion : deux modules distincts | Périmètres et livrables différents (Chat = libre / Réflexion = produit livrables structurés) — pages, services et tables séparés, aucun partage de code au-delà du rendu markdown |
| 2026-05-01 | Pont Réflexion → Code = copier-coller manuel | Garder la main utilisateur sur la transition, pas de pont automatique en base entre les deux modules |
| 2026-05-01 | Module Réflexion peut écrire les .md du projet | Suppression du copier-coller documentaire, hygiène automatisée — édition validée par diff comme dans le Module Code |
| 2026-05-01 | Step « Santé du cadrage » au démarrage des deux modules | Aligner conversation IA et état réel projet (PROJET_CONTEXTE + graphify + .md méthode) — voyant vert/orange/rouge non-bloquant |
| 2026-05-01 | Module Code : découpage automatique selon limites du modèle | Éviter les échecs monolithiques observés sur le pipeline actuel — découpage par fichier ou bloc fonctionnel quand le prompt + contexte + sortie dépassent la fenêtre |
| 2026-05-01 | Routage modèles : Réflexion=Claude Sonnet 4.5, Code=Gemini/Haiku selon tâche | Optimiser coût/qualité par type d'usage — Claude pour le dialogue/analyse, Gemini pour gros volume code, Haiku pour code court rapide |
| 2026-05-01 | JARVIS remplace à terme Claude Projects + Cascade | Vision long terme : un seul outil intégré localhost — la méthode actuelle Claude+Cascade reste l'échafaudage de construction tant que JARVIS n'est pas auto-suffisant |
| 2026-05-01 | Migration Gemini 2.0 Flash → 2.5 Flash AVANT la refonte | Gemini 2.0 Flash retiré le 2026-06-01 par OpenRouter — éviter un double chantier de migration en plein refactoring |
| 2026-05-01 | Pas de migration des sessions pipeline historiques | Ménage des sessions inactives en BDD à la place — la dette est faible, valeur utilisateur nulle, risque de migration évité |
| 2026-05-01 | Migration Gemini 2.0 Flash → 2.5 Flash effectuée | OpenRouter retire Gemini 2.0 Flash le 2026-06-01 — migration faite AVANT refonte pipeline pour éviter double chantier |

---

## 7. FICHIERS AUTORISÉS

| Fichier | Rôle |
|---|---|
| PROJET_CONTEXTE.md | Source de vérité |
| CHANGELOG.md | Historique missions |
| README.md | Présentation |
| STACK_CODE.md | Stack référence Module Code |

---

## 8. SESSION EN COURS

**Graphify :** ☑ Mis à jour — 2085 nodes, 3339 edges, 222 communities (2026-05-16)
**Objectif :** UX-FIX-01-02 — Badges FAILED et ABORTED manquants dans sidebar
**Mission terminée :** 2026-05-03 — Correction affichage statuts FAILED et ABORTED
**Fichiers modifiés :** sidebar.js (ajout FAILED et ABORTED dans getStatusBadge() ligne 632-633)
**Fichiers vérifiés :** ui.js (window.statusBadge ligne 76-87), style.css (classes badge--error ligne 421-424, badge--aborted ligne 442-445)
**Résultat :** UX-01 et UX-02 marqués RÉSOLU dans PROJET_CONTEXTE.md section 4. Cause racine : sidebar.js utilisait sa propre fonction getStatusBadge() locale qui ne contenait que 5 statuts et manquait FAILED et ABORTED. ui.js avait déjà window.statusBadge() avec tous les statuts, mais sidebar.js ne l'utilisait pas. Correction : Ajout de FAILED (badge rouge 💀 avec classe badge--error) et ABORTED (badge gris distinct ⛔ avec classe badge--aborted) dans getStatusBadge(). Les classes CSS existaient déjà dans style.css. Test manuel : (1) Créer session → abandonner → voir badge "⛔" gris distinct dans sidebar → (2) Provoquer échec → voir badge "�" rouge dans sidebar → (3) Vérifier dans dashboard et page projet.
**Prochain objectif :** Sprint 1+2 terminés (6 bugs + 2 UX résolus) — Sprint 3 : BUG-06+07 + FRAG-01 à FRAG-05

---

## 9. BACKLOG

### Sprint 1 — Bugs bloquants (à corriger avant tout usage réel) ~1h15

| Item | Bugs couverts | Fichiers | Effort |
|---|---|---|---|
| **S1-A** Corriger la création de réflexion depuis la sidebar | BUG-01, BUG-02, BUG-04 | `sidebar.js` + `mission.js` | ~30 min |
| **S1-B** Corriger le renommage de dossier | BUG-03 | `routers/projects.py` | ~20 min |
| **S1-C** Corriger le crash régénération résumé chat | BUG-05, BUG-08 | `routers/chat.py` | ~15 min |
| **S1-D** Ajouter badges FAILED et ABORTED distincts | UX-01, UX-02 | `ui.js` + `style.css` | ~10 min |

### Sprint 2 — UX dégradée ~1h20

| Item | Bugs couverts | Fichiers | Effort |
|---|---|---|---|
| **S2-A** Réflexion dans timeline dashboard | BUG-06 | `dashboard.js` | ~45 min |
| **S2-B** Supprimer auto-test au chargement Paramètres | UX-03 | `settings.js` | ~10 min |
| **S2-C** Bouton retour après abandon mission | UX-04 | `mission.js` | ~15 min |
| **S2-D** Corrections visuelles mineures | UX-05, UX-07, UX-08 | `mission.html`, `atelier.html`, `chat.html` | ~10 min |

### Sprint 3 — Fragilités structurelles ~3h30

| Item | Fragilités | Effort |
|---|---|---|
| **S3-A** Supprimer DEBUG prints production | FRAG-02 | ~10 min |
| **S3-B** Harmoniser VALID_MODEL_SLUGS | FRAG-07 | ~10 min |
| **S3-C** Reject → statut REJECTED (pas ABORTED) + relance possible | FRAG-03 | ~1h |
| **S3-D** Consolider sources de contexte (SQLite seul) | FRAG-05 | ~1h |
| **S3-E** Rendre le modèle Réflexion configurable | FRAG-06 | ~20 min |
| **S3-F** Clarifier distinction Contexte Global vs Profil/Règles dans Paramètres | UX-06 | ~30 min |

### Fonctionnalités futures

- **Notifications push** — Browser notification API quand session passe en WAITING_VALIDATION (effort : 3h)
- **Dashboard : Sessions Atelier RUNNING** — Afficher dans section "En cours" avec lien vers kanban (effort : 1h)
- **Atelier : Relancer pipeline FAILED** — Ajouter bouton "Relancer ce pipeline" (effort : 1h)
- **Phase 4 UI avancée** — éditeur diff interactif, historique replay
- **Atelier V2** — multi-catégories, relance cycle sur même prospect
- **Dashboard — analytics avancés** — coût cumulatif par projet, courbe semaine/mois