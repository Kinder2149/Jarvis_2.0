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
**Workflows :** `backend/data/pipelines.json` (1 workflow code_mission + 1 workflow atelier_restauration)
**Prompts :** `backend/data/prompts.json` (templates par étape, variables `{{var}}`)
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
│   │   ├── pipelines.py       ← start, status, validate step, retry step, abort, logs, parse-mission
│   │   ├── reflexions.py      ← CRUD réflexions, messages, figement, livrable, propose/apply edit
│   │   ├── files.py           ← read, write, diff, apply, archive docs, local-list
│   │   ├── chat.py            ← conversations, messages, titrage auto, résumé, folder_path
│   │   ├── atelier.py         ← CRUD prospects, start pipeline atelier, export ZIP
│   │   └── config.py          ← clés API (SQLite), test connexion, modèles, profil utilisateur
│   ├── services/
│   │   ├── pipeline_engine.py ← state machine, orchestration, chunking, persistance
│   │   ├── model_router.py    ← sélection modèle, appel API, log décisions
│   │   ├── context_manager.py ← construction context envelopes par étape
│   │   ├── file_service.py    ← pathlib, diff, rollback all-or-nothing
│   │   ├── chat_service.py    ← historique messages, titrage auto, lecture dossier local, web search
│   │   ├── atelier_service.py ← logique pipeline atelier, export ZIP fichiers démo
│   │   ├── reflexion_service.py ← session réflexion, messages IA, figement, livrables, propose/apply edit
│   │   ├── cadrage.py         ← 7 checks santé cadrage (PROJET_CONTEXTE, graphify, section 8…)
│   │   ├── chunking.py        ← découpage automatique missions par fichier (single_call / chunk_by_file)
│   │   └── mission_parser.py  ← parsing prompt mission → titre, fichiers, modèle recommandé
│   ├── schemas/
│   │   ├── project.py
│   │   ├── pipeline.py
│   │   ├── reflexion.py
│   │   └── config.py
│   └── data/
│       ├── jarvis.db          ← SQLite (tables: projects, sessions, pipeline_steps, conversations, messages, app_config, prospects, reflexion_sessions, reflexion_messages, mission_prompts)
│       ├── config.json        ← model_preferences + methodo_path (clés API dans jarvis.db)
│       ├── pipelines.json     ← workflow code_mission (4 steps) + atelier_restauration (13 steps)
│       └── prompts.json       ← templates prompts par step (execution, verification, cloture, atelier_*, reflexion_*)
└── frontend/
    ├── index.html             ← dashboard (timeline activité, sessions actives/bloquées, stats)
    ├── dossier.html           ← hub projet/dossier (remplace project.html)
    ├── code-projects.html     ← liste projets Module Code (bouton Nouvelle Mission par projet)
    ├── mission.html           ← page unique Mission : Zone 1 Réflexion + Zone 2 Livrable + Zone 3 Pipeline
    ├── chat.html              ← conversation IA (markdown, folder_path, web search, sélecteur modèle)
    ├── conversations.html     ← liste de toutes les conversations (hub d'accès depuis sidebar btn 💬)
    ├── atelier.html           ← Atelier Connecté (kanban 6 colonnes + vue pipeline prospect)
    ├── sentinelle.html        ← Module Sentinelle (cycle investissement PHASE_1 à PHASE_6, portefeuille, watchlist)
    └── settings.html          ← config clés API 3 providers + sélecteurs modèles par type
    └── assets/
        ├── style.css          ← thème sombre, variables CSS, layout 3 panneaux, composants
        └── js/
            ├── api.js            ← toutes les routes API (BASE_URL = window.location.origin)
            ├── shared.js         ← renderMarkdown, formatDate, statusBadge, costBadge, initLayout
            ├── sidebar.js        ← sidebar collapsible, modals nouveau chat/module/projet/reflexion
            ├── ui.js             ← showModal, closeModal, showToast
            ├── dashboard.js      ← timeline, sessions actives/bloquées, stats semaine
            ├── project.js        ← hub projet, instructions éditables, liste unifiée sessions+chats
            ├── code-projects.js  ← liste projets Module Code (bouton Nouvelle Mission)
            ├── mission.js        ← orchestrateur unique Mission (réflexion + figement + pipeline en une page)
            ├── chat.js           ← messages, optimistic UI, sélecteur modèle, suppression
            ├── conversations.js  ← liste conversations, suppression, redirection chat.html
            ├── explorer.js       ← arborescence fichiers locaux, preview, collapse
            ├── atelier.js        ← kanban prospects, vue pipeline atelier, zones saisie/checkpoint/export
            ├── sentinelle.js     ← Module Sentinelle — cycle investissement, portefeuille, watchlist
            └── settings.js       ← clés API (états visuels), test connexion, dropdowns modèles

**Services backend actifs :** 11 / 20 maximum
**Pages frontend :** 9 / illimité (mission.html a remplacé reflexion.html + module-code.html + code-project-detail.html — conversations.html et sentinelle.html ajoutées)

---

## 4. FONCTIONNALITÉS

**✅ Stables**
- Gestion projets CRUD (enregistrement, liste, suppression, instructions, local_path)
- Pipeline engine complet (workflow code_mission + atelier_restauration, state machine, persistance SQLite)
- Chunking automatique par fichier pour les missions code (single_call / chunk_by_file selon budget tokens)
- Routing modèles par type de tâche (routing/structuring/code/analysis) — configurable depuis Paramètres
- `load_config()` centralisé dans database.py — source unique pour tous les routers
- Clés API dans SQLite (table app_config), seed auto depuis .env au démarrage
- Rollback atomique apply_files (3 phases), parsing diff 3 fallbacks
- Clôture auto PROJET_CONTEXTE.md section 8 + CHANGELOG.md à chaque mission
- Logs applicatifs : jarvis.log + GET /pipelines/logs
- **Frontend V2 complet** : layout 3 panneaux (sidebar collapsible, main, explorer), 7 pages, 12 modules JS
- **Page Mission unique** (mission.html) : flow 4 étapes progressives (Réflexion → Validation → Exécution → Suivi), polling 5s, validation diff/generic, complétion decision_figee avec retour projet
- **Module Réflexion** : session conversationnelle Claude Sonnet 4.5 → figement → 3 types de livrables (mission_code / decision_figee / plan_multi_missions). Modèle configurable depuis app_config.
- **Module Code** : pipeline code_mission depuis mission.html Zone 3, preview parsing, chunking auto, retry step
- **Module Chat** : lecture dossier local (GRAPH_REPORT prioritaire), web search Brave API, sélecteur modèle, résumé contextuel
- **Module Projet** : hub conteneur (instructions, local_path, liste unifiée sessions+chats)
- **Atelier Connecté** : kanban 6 colonnes, pipeline 13 steps pour prospects restauration, export ZIP démo HTML
- **Atelier pipeline** : 3 moments humains (form saisie terrain → checkpoint validation → export ZIP)
- Cadrage health check : 7 points de contrôle (PROJET_CONTEXTE, graphify, section 8, décisions figées, fichiers méthode, backlog, fraîcheur)
- Sources METHODO unifiées : reflexion_service et cadrage lisent depuis methodo_path (config.json), fallback interne avec warning
- Startup recovery : sessions RUNNING → FAILED au démarrage (crash server)
- Toast system, modales confirmation, états vides, dashboard timeline réflexions + pipelines
- Badges statut complets : PENDING / RUNNING / WAITING_VALIDATION / COMPLETED / FAILED 💀 / ABORTED ⛔
- Paramètres : distinction claire Contexte Global (tous modules) vs Profil utilisateur (Chat uniquement)
- health_check.py : vérification rapide 3 modules en < 60s

**🚧 En cours**
- Aucun — audit 2026-05-03 soldé (Sprint 1 + 2 + 3 terminés). JARVIS prêt pour usage.

**❌ Bugs connus — Audit 2026-05-03**

| ID | Sévérité | Module | Description | Fichiers | Statut |
|---|---|---|---|---|---|
| BUG-01 | ✅ RÉSOLU | Sidebar | Valeur par défaut `reflexion_simple` viole la contrainte CHECK SQLite → réflexion jamais créée | `sidebar.js:handleNewMission()` | Vérifié 2026-05-03 : aucun code n'envoie cette valeur, flux fonctionne correctement |
| BUG-02 | ✅ RÉSOLU | Sidebar→Mission | URL `?livrable_type=X` générée mais ignorée par `mission.js init()` → page mission blanche | `mission.js:init()` | Vérifié 2026-05-03 : mission.js lit correctement le paramètre 'new' |
| BUG-03 | ✅ RÉSOLU | Dossier | Renommage dossier silencieusement ignoré : PATCH ne traite pas le champ `name` | `routers/projects.py:update_project()` | Corrigé 2026-05-03 : requête UPDATE ligne 350-352 incluait déjà name, commentaire ajouté |
| BUG-04 | ✅ RÉSOLU | Sidebar | `btn-new-reflexion` redirige vers `code-projects.html` au lieu de créer une réflexion | `sidebar.js:~btn-new-reflexion` | Vérifié 2026-05-03 : redirige vers mission.html correctement |
| BUG-05 | ✅ RÉSOLU | Chat | `update_conversation_summary` : kwarg `model_preferences` inexistant + `result["content"]` (string, pas dict) → TypeError | `routers/chat.py:update_conversation_summary()` | Corrigé 2026-05-03 : vrai bug était AttributeError sur db_conn.cursor(), condition ajoutée model_router.py ligne 63 |
| BUG-06 | ✅ RÉSOLU | Dashboard | Sessions Réflexion absentes de la timeline et des stats | `dashboard.js:buildTimeline()` | Résolu lors de R01-R03 — dashboard.js charge et affiche les réflexions (timeline + stats semaine) |
| BUG-07 | ✅ RÉSOLU | Chat | `PATCH /conversations/{id}/folder` : frontend envoie JSON, backend attend query param | `routers/chat.py` / `api.js` | Vérifié : api.js et backend utilisent tous deux un JSON body (Pydantic FolderUpdate) |
| BUG-08 | ✅ RÉSOLU | Chat | Crash serveur TypeError au déclenchement de `update_conversation_summary` (même cause que BUG-05) | `routers/chat.py` | Corrigé 2026-05-03 : même correction que BUG-05 (db_conn optionnel) |

**⚠️ Fragilités structurelles — Audit 2026-05-03**

| ID | Module | Description | Risque |
|---|---|---|---|
| FRAG-01 | ✅ RÉSOLU | Backend | `load_config()` dupliquée verbatim dans `chat.py` et `pipelines.py` | Centralisée dans `database.py` — Sprint 3 2026-05-03 |
| FRAG-02 | ✅ RÉSOLU | Backend | `print("DEBUG ...")` en production dans `pipelines.py` et `pipeline_engine.py` | Vérifié : aucun print() en production, tous remplacés par logger |
| FRAG-03 | ✅ RÉSOLU | Pipeline | Reject d'une étape → ABORTED définitif, aucune possibilité de relancer avec feedback | `validate_step()` laisse la session en WAITING_VALIDATION — retry possible |
| FRAG-04 | ✅ RÉSOLU | Pipeline | Step `sante_cadrage` marquée COMPLETED avec `output_data=null` (rapport jamais peuplé) | `check_cadrage_health()` appelé et résultat JSON stocké dans output_data |
| FRAG-05 | ✅ RÉSOLU | Contexte | 3 sources non synchronisées : SQLite / `contexts/*.md` / `backend/data/methodo/` | `_get_methodo_path()` dans reflexion_service + cadrage — lit methodo_path config, fallback interne avec warning |
| FRAG-06 | ✅ RÉSOLU | Réflexion | Modèle `claude-sonnet-4.5` hardcodé dans `reflexion_service.py` — non configurable | `_get_reflexion_model()` lit analysis_model depuis app_config (SQLite) — Sprint 3 2026-05-03 |
| FRAG-07 | ✅ RÉSOLU | Réflexion | `VALID_MODEL_SLUGS` utilise tirets (`claude-sonnet-4-5`) vs points ailleurs (`claude-sonnet-4.5`) | VALID_MODEL_SLUGS utilise les points (4.5) — cohérent avec le reste |

**🎨 Problèmes UX — Audit 2026-05-03**

| ID | Sévérité | Description | Fichier | Statut |
|---|---|---|---|---|
| UX-01 | 🔴 | Statut `FAILED` affiché en texte brut anglais sans badge | `ui.js:statusBadge()` | ✅ RÉSOLU 2026-05-03 : badge rouge ajouté dans sidebar.js |
| UX-02 | 🟠 | `ABORTED` visuellement identique à `PENDING` (même couleur grise) | `ui.js:statusBadge()` | ✅ RÉSOLU 2026-05-03 : badge gris distinct ajouté dans sidebar.js |
| UX-03 | ✅ RÉSOLU | Auto-test clés API au chargement Paramètres → spinners + toasts d'erreur spontanés | `settings.js:testAllProviders()` | `initializeTestBadges()` au chargement (badges "Non testé"), test déclenché uniquement sur clic |
| UX-04 | ✅ RÉSOLU | Aucun bouton retour visible après abandon en étape 1 ou 2 de mission.html | `mission.html:step-4-footer` | step-4-footer + btn-back-project affichés quand statut=ABANDONNEE |
| UX-05 | ✅ RÉSOLU | Étapes 3-4 affichées "En attente" pour `decision_figee` (ne s'activent jamais) | `mission.html` | Sprint 2 : setActiveStep(4) + message "Décision appliquée ✅" après applyEdit() |
| UX-06 | ✅ RÉSOLU | Deux zones "contexte global" dans Paramètres sans distinction claire | `settings.html` | Sprint 2 : textes explicatifs `.settings-section-hint` sur chaque zone |
| UX-07 | ✅ RÉSOLU | Bouton "Réinitialiser" Atelier label trompeur (supprime tout) | `atelier.html` | Renommé "🗑️ Tout supprimer" |
| UX-08 | ✅ RÉSOLU | Emoji 📋 sur bouton "Sauvegarder le résumé" (devrait être 💾) | `chat.html:49` | Bouton Save utilise 💾, 📋 reste sur le toggle d'affichage (logique) |

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
| 2026-05-01 | Gemini 2.0 Flash → 2.5 Flash | Retrait Gemini 2.0 par OpenRouter (deadline 2026-06-01) — migration transparente |
| 2026-05-01 | Workflow code_mission (4 steps) remplace 6 workflows obsolètes | session_start/end/bug_simple/mission_complexe/nouveau_projet/projet_existant supprimés — un seul workflow universel |
| 2026-05-02 | mission.html : page unique Mission | Fusion reflexion.html + module-code.html + code-project-detail.html — 4 étapes progressives dans une seule page. Fichiers archivés dans temp/_archive/ |
| 2026-05-02 | Module Réflexion : modèle configurable | Modèle lu depuis analysis_model dans app_config (SQLite) — pas hardcodé. Fallback : anthropic/claude-sonnet-4.5 |
| 2026-05-03 | load_config() centralisé dans database.py | Source unique pour tous les routers — pas de duplication possible |
| 2026-05-03 | Reject pipeline → WAITING_VALIDATION | Un reject laisse la session ouverte pour retry avec feedback — ABORTED réservé à l'abandon explicite |
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
| 2026-05-15 | SENTINELLE via JARVIS : thèses hors scope conversation | Thèses = interface dédiée sentinelle.html. Depuis JARVIS : consultation et watchlist uniquement. Agir (transactions) : jamais. |

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

**Graphify :** ✅ Mis à jour (hook post-commit)
**Objectif :** 5 corrections timeout + UX + performance
**Mission terminée :** 2026-05-24 — PERF-ROBUSTESSE
**Fichiers modifiés :**
- backend/services/model_router.py : timeout 60s appels LLM
- backend/services/atelier_handler.py : vérification prospect supprimé + message site inaccessible
- frontend/assets/js/atelier.js : event delegation kanban
- frontend/assets/js/sidebar.js : parallélisation sessions+réflexions
- CHANGELOG.md : ajout ligne mission PERF-ROBUSTESSE
- PROJET_CONTEXTE.md : mise à jour section 8

**Corrections appliquées :**

**C-1 : Timeout 60s appels LLM**
- Wrapper `asyncio.wait_for(timeout=60.0)` sur tous appels OpenRouter + Anthropic dans `model_router.py`
- `raise RuntimeError("Timeout LLM après 60s")` si dépassé
- Exception catchée par handlers et renvoyée comme message d'erreur normal

**C-2 : Vérification prospect supprimé pipeline ATELIER**
- Au début `_run_phase1_bg()` + `_run_phase2_bg()` : `SELECT id FROM prospects WHERE id=?`
- Si absent : `logger.warning` + `_inject_message_conversation("prospect supprimé, pipeline annulé")` + `return`
- Même vérification session ABORTED

**C-3 : Event delegation kanban ATELIER**
- Suppression `addEventListener` directs sur `.prospect-card` + `.btn-prospect-delete` dans `renderKanban()`
- Ajout event delegation sur `#kanban-board` dans `DOMContentLoaded` (une seule fois, flag `_delegated`)
- `e.target.closest('.prospect-card')` pour clic card, `e.target.closest('.btn-prospect-delete')` pour suppression
- Évite N listeners après N cycles polling

**M-1 : Parallélisation sidebar sessions+réflexions**
- Remplacement `for...of` séquentiel (`await getProjectSessions` + `await getReflexions`) par `Promise.allSettled` sur `projects.map` avec `Promise.allSettled` interne `[sessions, reflexions]`
- Gain temps chargement sidebar proportionnel au nombre de projets

**M-3 : Message explicite site inaccessible ATELIER**
- Détection `fetch_ok` dans `_handle_new_prospect` + `_finalize_collecting_with_url`
- Si false : ajout `site_note` "⚠️ Le site {url} est inaccessible ou a retourné une erreur. Je vais analyser le prospect avec les informations disponibles (nom, URL, notes) sans accéder au site."
- Inclus dans `content` retourné à l'utilisateur, évite hallucinations sur contenu site inexistant

**Graphify post-commit :**
- 2947 nodes, 4717 edges, 465 communities
- GRAPH_REPORT.md mis à jour automatiquement

**Backlog technique (audit) :**
- INCOMPLET-01 : sentinelle_theses sans interface (table active, service la lit, aucun CRUD UI)

**Prochain objectif :** Tests manuels — (C-1) Appel LLM > 60s → message "Timeout LLM après 60s". (C-2) Supprimer prospect pendant pipeline → message "prospect supprimé, pipeline annulé". (C-3) Recharger kanban 5 fois + cliquer card → 1 seule requête. (M-1) DevTools Network sidebar → requêtes sessions+réflexions en parallèle. (M-3) URL invalide ATELIER → message "inaccessible"

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