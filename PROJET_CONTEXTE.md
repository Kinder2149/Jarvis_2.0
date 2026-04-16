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
**Config :** `backend/data/config.json` (clés API + préférences modèles)
**Workflows :** `backend/data/pipelines.json` (6 workflows définis comme données)
**Prompts :** `backend/data/prompts.json` (templates par étape, variables `{{var}}`)
**Diff :** `difflib` Python stdlib (unified diff) — rendu CSS côté frontend
**Démarrage :** `start.bat` à la racine (lance uvicorn + ouvre navigateur)

---

## 3. ARCHITECTURE


JARVIS/
├── start.bat ← démarrage Windows (double-clic)
├── requirements.txt
├── PROJET_CONTEXTE.md
├── STACK_STANDARD.md
├── CHANGELOG.md
├── backend/
│ ├── main.py ← FastAPI app, CORS, routes, static files
│ ├── routers/
│ │ ├── projects.py ← CRUD projets + import depuis PROJET_CONTEXTE.md
│ │ ├── pipelines.py ← start, status, validate step, retry step
│ │ ├── models.py ← appel OpenRouter/direct + test connexion
│ │ └── files.py ← read, write, diff, apply, archive docs
│ ├── services/
│ │ ├── pipeline_engine.py ← state machine, orchestration, persistance
│ │ ├── model_router.py ← sélection modèle, appel API, log décisions
│ │ ├── context_manager.py ← construction context envelopes par étape
│ │ └── file_service.py ← pathlib, diff, rollback all-or-nothing
│ ├── schemas/
│ │ ├── project.py
│ │ ├── pipeline.py
│ │ └── config.py
│ └── data/
│ ├── jarvis.db ← SQLite
│ ├── config.json ← clés API + mapping modèles
│ ├── pipelines.json ← 6 workflows définis
│ └── prompts.json ← templates prompts par step
└── frontend/
├── index.html ← dashboard projets
├── pipeline.html ← pipeline actif (page principale)
├── project.html ← vue projet (PROJET_CONTEXTE, logs, backlog)
├── settings.html ← clés API + modèles par défaut
└── assets/
├── style.css ← thème sombre, variables CSS, composants
└── app.js ← fetch API, rendu markdown/diff, gestion état UI


**Services actifs :** 8 / 20 maximum
**Fichiers frontend :** 6 / illimité (pas de contrainte ici)

---

## 4. FONCTIONNALITÉS

**✅ Stables**
- Gestion projets CRUD (enregistrement, liste, suppression)
- Pipeline engine complet (6 workflows, state machine, persistance SQLite)
- Routing modèles par type de tâche (routing/structuring/code/analysis)
- Suite de tests 142/142 (unitaires + intégration)
- Configuration modèles équilibrée (routing=Gemini Flash, code=Haiku, analysis=Sonnet)
- Roadmap OpenRouter validée (6 slugs testés live)
- Tous les workflows testés live (session_start, session_end, bug_simple, mission_complexe, nouveau_projet, projet_existant)
- Fermeture de boucle complète : apply_files connecté, parsing diff robuste (3 fallbacks), flux validation amélioré
- Cloture automatique : PROJET_CONTEXTE.md section 8 et CHANGELOG.md mis à jour automatiquement
- Sécurité : config.json et jarvis.db gitignorés
- Auto-avance sur étapes sans validation
- Checkpoints de validation fonctionnels
- Clés API masquées dans l'interface
- Frontend V1 complet (4 pages : index, pipeline, project, settings)
- Erreurs API lisibles utilisateur (401, 429, 404, timeout → messages FR)
- Logs applicatifs : backend/data/jarvis.log + endpoint GET /pipelines/logs
- Rollback atomique apply_files : 3 phases (vérif / tmp / rename+backup)
- Architecture respectée : context_manager seul lecteur/écrivain de PROJET_CONTEXTE.md
- Prompts (25) : format corrigé, JSON pur, chemin inside bloc code
- **Module code complet** : 6 workflows, 142 tests, rollback atomique, clôture automatique

**🚧 En cours**
- Module chat : backend livré, routes 200 OK, chat simple fonctionnel (prompt système modifiable, message envoyable) — À compléter : lecture dossier local, accès internet, project_id nullable

**❌ Bugs connus**
- start.bat ne se lance pas — serveur démarré manuellement (non bloquant)

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
| 2026-04-16 | start.bat : bug identifié | Le serveur se lance manuellement en attendant le fix — non bloquant |

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

**Graphify :** ☑ Mis à jour
**Objectif :** Clôture module chat + cadrage module chat enrichi
**Contexte :** Module chat livré (142/142 tests). Deux bugs critiques corrigés (clé API masquée écrasée + ChatConfig manquant dans schema). Session cadrage : décisions prises sur périmètre élargi (lecture dossier + internet), architecture module projet, project_id nullable.
**Blocage :** start.bat ne fonctionne pas (lancement manuel). Test live chat non encore réalisé post-corrections.
**Résultat attendu :** Prompt A (clôture : fix start.bat + project_id nullable + git commit) + Prompt B (module chat enrichi : dossier local + internet) produits et validés.

---

## 9. BACKLOG

1. **Clôture module chat de base** — fix start.bat + ajout project_id nullable sur conversations + git commit
2. **Module chat enrichi** — lecture dossier local (chat sans projet = dossier temp ; chat avec projet = dossier projet hérité) + accès internet via web search
3. **Module projet** — conteneur regroupant missions code + conversations chat + contexte partagé + lien dossier local
4. **Phase 4 UI avancée** — éditeur diff interactif, historique replay