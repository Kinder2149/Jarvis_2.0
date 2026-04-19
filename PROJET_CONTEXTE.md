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
│   │   ├── pipelines.py       ← start, status, validate step, retry step, abort, logs
│   │   ├── models.py          ← config clés API (SQLite), test connexion, modèles disponibles
│   │   ├── files.py           ← read, write, diff, apply, archive docs, local-list
│   │   ├── chat.py            ← conversations, messages, titrage auto
│   │   └── atelier.py         ← CRUD prospects, start pipeline atelier, export ZIP
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
    ├── project.html           ← hub projet (instructions, local_path, sessions+conversations unifiées)
    ├── module-code.html       ← suivi temps réel workflow IA (steps, validation, diff, polling 2s)
    ├── chat.html              ← conversation IA (markdown, folder_path, web search, sélecteur modèle)
    ├── atelier.html           ← Atelier Connecté (kanban 6 colonnes + vue pipeline prospect)
    └── settings.html          ← config clés API 3 providers + sélecteurs modèles par type
    └── assets/
        ├── style.css          ← thème sombre, variables CSS, layout 3 panneaux, composants
        └── js/
            ├── api.js         ← toutes les routes API (BASE_URL = window.location.origin)
            ├── shared.js      ← renderMarkdown, formatDate, statusBadge, costBadge, escapeHtml
            ├── sidebar.js     ← sidebar collapsible, modals nouveau chat/module/projet
            ├── ui.js          ← showModal, closeModal, showToast
            ├── dashboard.js   ← timeline, sessions actives/bloquées, stats semaine
            ├── project.js     ← hub projet, instructions éditables, liste unifiée sessions+chats
            ├── module-code.js ← polling pipeline, steps, zone validation (diff/generic), retry step
            ├── chat.js        ← messages, optimistic UI, sélecteur modèle, suppression
            ├── explorer.js    ← arborescence fichiers locaux, preview, collapse
            ├── atelier.js     ← kanban prospects, vue pipeline atelier, zones saisie/checkpoint/export
            └── settings.js    ← clés API (états visuels), test connexion, dropdowns modèles

**Services backend actifs :** 6 / 20 maximum
**Pages frontend :** 6 / illimité

---

## 4. FONCTIONNALITÉS

**✅ Stables**
- Gestion projets CRUD (enregistrement, liste, suppression, instructions, local_path)
- Pipeline engine complet (6 workflows Module Code, state machine, persistance SQLite)
- Routing modèles par type de tâche (routing/structuring/code/analysis)
- Suite de tests : 162/162 backend + 41 E2E Playwright V2 + tests UX Refactoring (test_front_ux.py)
- Configuration modèles : routing=Gemini Flash, code=Claude Haiku 4.5, analysis=Claude Sonnet 4.5
- Clés API dans SQLite (table app_config), migration auto depuis config.json au démarrage
- Tous les workflows testés live
- Rollback atomique apply_files (3 phases), parsing diff 3 fallbacks
- Clôture auto PROJET_CONTEXTE.md section 8 + CHANGELOG.md
- Logs applicatifs : jarvis.log + GET /pipelines/logs
- **Frontend V2 complet** : layout 3 panneaux (sidebar collapsible, main, explorer), 6 pages, 11 modules JS
- **Module Code** : polling 2s, steps visuels, zone validation diff/generic, retry step, breadcrumb projet
- **Module Chat** : lecture dossier local (GRAPH_REPORT prioritaire), web search Brave API, sélecteur modèle
- **Module Projet** : hub conteneur (instructions, local_path, liste unifiée sessions+chats)
- **Atelier Connecté** : kanban 6 colonnes, pipeline 9 steps pour prospects restauration, export ZIP démo HTML
- **Atelier pipeline** : 3 moments humains (form saisie terrain → checkpoint validation → export ZIP)
- **Build portable** : JARVIS.exe via PyInstaller (launcher tkinter)
- **UX Refactoring (FRONT-01 à 06)** : CTA post-session, badges kanban, sidebar counter, dashboard waiting, lancement inline

**🚧 En cours**
- Tests E2E UX Refactoring : écriture tests/test_front_ux.py (TEST-02) + run complet (TEST-03)

**❌ Bugs connus**
- Aucun

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
| 2026-04-17 | Frontend V2 : architecture JS modulaire | 11 fichiers JS séparés (api.js, shared.js, sidebar.js, ui.js, dashboard.js, project.js, module-code.js, chat.js, explorer.js, atelier.js, settings.js) — pas de bundler, pas de framework |
| 2026-04-17 | Clés API migrées dans SQLite | config.json ne contient plus que model_preferences — clés API dans table app_config (migration auto au démarrage) |
| 2026-04-17 | Atelier Connecté : un pipeline par prospect | Un prospect = une seule session atelier. startAtelierPipeline bloqué si session existante. Recycle n'est pas prévu : démo générée → prospect marqué contacté → fin de cycle |
| 2026-04-17 | Atelier vs Module Code : paradigmes différents | Module Code = session-centré (session visible dans sidebar sous le projet). Atelier = prospect-centré (kanban, prospect est l'entité principale). Les deux utilisent le même pipeline_engine |
| 2026-04-18 | UX Refactoring : 6 missions frontend | Décision : corriger les trous UX identifiés par audit (pages mortes, compteurs trompeurs, friction lancement). Aucun changement backend sauf FRONT-03 (ajout session_status dans GET /atelier/prospects) |

---

## 7. FICHIERS AUTORISÉS

| Fichier | Rôle |
|---|---|
| PROJET_CONTEXTE.md | Source de vérité |
| CHANGELOG.md | Historique missions |
| README.md | Présentation |
| STACK_STANDARD.md | Stack référence |

---

## 8. SESSION EN COURS

**Graphify :** ☑ Mis à jour — 904 nodes, 1044 edges, 81 communities (2026-04-18)
**Objectif :** ✅ TERMINÉ — INFRA-04 : Couche contexte globale dans le Module Code. Injection des règles méthode (REGLES_GLOBALES.md + PROFIL_UTILISATEUR.md) dans les pipelines Module Code via flag inject_global_rules. Nouvelle fonction build_global_rules_context() dans context_manager.py charge les règles depuis METHODO. Flag ajouté aux steps clés : orientation, cloture_docs, cadrage, document_mission, analyse_besoin, draft_projet_contexte, scan_projet, audit_code, analyse_bug (9 steps). Templates prompts enrichis avec {{global_rules}}. Les pipelines connaissent maintenant les règles de la méthode (3 couches max, 20 services max, zéro abstraction non demandée).
**Résultat :** 
  - backend/services/context_manager.py : fonction build_global_rules_context() + gestion inject_global_rules + substitution {{global_rules}}
  - backend/data/pipelines.json : inject_global_rules: true sur 9 steps concernés
  - backend/data/prompts.json : {{global_rules}} ajouté en début des templates
  - CHANGELOG.md mis à jour
  - PROJET_CONTEXTE.md section 8 mis à jour
**Prochaine session :** Graphify update recommandé

---

## 9. BACKLOG

### Améliorations UX Refactoring (priorité haute)

1. **FRONT-01 : Bouton "Retour au projet" en secondaire** — Inverser avec "Nouvelle session" pour mettre l'accent sur le retour (effort : 5 min)
2. **FRONT-05 : Banner encombrant si 10+ sessions** — Ajouter limite affichage (ex: "⏸️ 12 sessions attendent ta validation" + collapse "Voir tout") (effort : 30 min)

### Améliorations UX Refactoring (priorité moyenne)

3. **Atelier : Relancer pipeline FAILED** — Ajouter bouton "Relancer ce pipeline" sur zone CTA Atelier (effort : 1h)
4. **Dashboard : Optimiser appels API** — Cache partagé entre sidebar et dashboard pour éviter doublons (effort : 2h)
5. **FRONT-04 : Animation pulse plus prononcée** — Réduire opacity min de 0.4 à 0.2 pour ⚙️ RUNNING (effort : 2 min)

### Améliorations UX Refactoring (priorité basse)

6. **Notifications push** — Browser notification API quand session passe en WAITING_VALIDATION (effort : 3h)
7. **Dashboard : Sessions Atelier RUNNING** — Afficher dans section "En cours" avec lien vers kanban (effort : 1h)
8. **Atelier : Duplication prospect** — Bouton "Dupliquer" sur card kanban pour relancer cycle (effort : 2h)

### Fonctionnalités futures

9. **Phase 4 UI avancée** — éditeur diff interactif (sélection chunks, annotations), historique replay (rejouer une session passée)
10. **Atelier V2** — multi-catégories (pas uniquement restauration), relance cycle sur même prospect
11. **Dashboard — analytics avancés** — coût cumulatif par projet, courbe d'activité semaine/mois