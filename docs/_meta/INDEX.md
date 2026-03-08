# Index de la Documentation - JARVIS 2.0

**Statut** : REFERENCE  
**Version** : 2.4  
**Date** : 2026-03-07

## Point d'Entrée Unique

Ce document sert de point d'entrée centralisé pour toute la documentation du projet JARVIS 2.0.

---

## 📁 Structure Documentaire

### Racine du repo
Documents fondateurs.

- **JARVIS_Base_Document_Complet.md** - Vision long terme du projet JARVIS (document fondateur, non implémenté en totalité)

### `docs/reference/`
Documents contractuels validés (source de vérité). Toute modification = nouvelle version.

- **ARCHITECTURE.md** (v3.0) - Architecture technique du système
- **API_SPECIFICATION_V2.md** (v2.1) - Spécification des endpoints API
- **AGENT_SYSTEM.md** (v4.0) - Système d'agents (factory, config, 3 Agent IDs, orchestration, file_writer)
- **AGENTS_CONFIGURATION_COMPLETE.md** (v2.0) - Configuration complète des 3 agents (prompts + functions + paramètres Mistral)
- **INSTRUCTIONS_MISTRAL_STUDIO.md** - Instructions copier-coller pour configuration functions sur Mistral AI Studio

### `config_agents/`
Prompts agents JARVIS 2.0. Source de vérité pour les instructions (chargés localement via SDK Gemini).

- **README.md** - Guide d'utilisation du dossier
- **CODEUR.md** (v3.3) - Prompt agent CODEUR (spécialiste code, max_tokens=8192)
- **JARVIS_MAITRE.md** (v5.2) - Prompt agent JARVIS_Maître (orchestrateur)
- **BASE.md** (v3.1) - Prompt agent BASE (worker générique)
- **VALIDATEUR.md** (v2.0) - Prompt agent VALIDATEUR (contrôle qualité)

### `docs/work/`
Documents en cours (audits, analyses, brouillons). Durée de vie limitée, revue périodique.

- **ETAT_LIBRARY.md** - État complet library (40 documents)
- **GUIDE_TESTS_LIVE.md** - Guide validation paramétrage JARVIS 2.0

### `docs/history/`
Archive lecture seule (traçabilité). Documents obsolètes/remplacés/terminés. 60+ documents archivés.

**Documents clés** :
- **20260212_MIGRATION_ARCHITECTURE_2_AGENTS.md** - Plan de migration vers 2 agents distincts (exécuté et validé)
- **20260216_RESOLUTION_DELEGATION_COMPLETE.md** - Résolution délégation JARVIS_Maître → CODEUR
- **20260218_RAPPORT_SESSION_CORRECTION_PHASE.md** - Correction phase EXECUTION (écriture disque)

### `docs/_meta/`
Index, règles, templates, changelog.

- **INDEX.md** - Ce document
- **ETAT_ACTUEL_JARVIS_20260307.md** - État actuel JARVIS 2.0 (REFERENCE)
- **CHANGELOG.md** - Historique des modifications documentaires
- **IA_CONTEXT.md** - Document de contexte complet pour IA externe
- **AUDIT_DOCUMENTATION_20260218.md** - Audit documentation

---

## 🎯 Documents Clés par Thématique

### Pour Démarrer
1. `_meta/ETAT_ACTUEL_JARVIS_20260307.md` - État actuel système (LIRE EN PREMIER)
2. `work/GUIDE_TESTS_LIVE.md` - Guide validation
3. `../.env.example` - Configuration requise

### Pour Développer
1. `../config_agents/` - Prompts agents (CODEUR v3.3, JARVIS_MAITRE v5.2)
2. `../backend/agents/agent_config.py` - Configuration centralisée agents
3. `work/ETAT_LIBRARY.md` - Library 40 documents

### Pour Onboarder une IA
- `_meta/IA_CONTEXT.md` - Document de contexte complet pour IA externe

---

## 📋 Dernières Mises à Jour

| Date | Document | Action |
|------|----------|--------|
| 2026-02-10 | Tous | Création initiale de la documentation |
| 2026-02-12 | ARCHITECTURE.md | v3.0 — Migration architecture 2 agents |
| 2026-02-12 | AGENT_SYSTEM.md | v3.0 — Factory + config, suppression agent_registry |
| 2026-02-12 | API_SPECIFICATION_V2.md | Correction CHECK role (retrait 'system') |
| 2026-02-12 | IA_CONTEXT.md | v2.0 — Reflet architecture actuelle |
| 2026-02-12 | INDEX.md | v2.0 — Références mises à jour |
| 2026-02-12 | CHANGELOG.md | Entrées migration ajoutées |
| 2026-02-12 | 20260212_MIGRATION... | Archivé dans docs/history/ |
| 2026-02-12 | JARVIS_Base_Document_Complet.md | v2.0 — Réécriture vision consolidée |
| 2026-02-12 | 20260212_CHANTIER_PERSONNALISATION_V1.md | Création document de travail (9 missions) |
| 2026-02-12 | AGENT_SYSTEM.md | v3.1 — Personnalisation agents (params, cloud-only) |
| 2026-02-12 | 20260212_CHANTIER_PERSONNALISATION_V1.md | Archivé dans docs/history/ (missions terminées) |
| 2026-02-12 | 9 fichiers frontend obsolètes | Supprimés (nettoyage) |
| 2026-02-13 | JARVIS_Base_Document_Complet.md | v2.1 — Ajout CODEUR, réécriture §6 Orchestration |
| 2026-02-13 | AGENT_SYSTEM.md | v4.0 — 3 agents, orchestration, boucle vérification, file_writer |
| 2026-02-13 | CHANGELOG.md | Entrées orchestration v1.1 ajoutées |
| 2026-02-13 | file_writer.py | Fix artefacts markdown (_clean_content) |
| 2026-02-13 | orchestration.py | Boucle vérification CODEUR→BASE→relance |
| 2026-02-13 | AGENTS_CONFIGURATION_COMPLETE.md | v2.0 — Document unique configuration agents + functions |
| 2026-02-13 | INSTRUCTIONS_MISTRAL_STUDIO.md | Instructions copier-coller functions Mistral AI Studio |
| 2026-02-13 | Knowledge Base | Implémentation complète (backend + function calling + 13 documents) |
| 2026-02-13 | 20260213_MISTRAL_FUNCTION_CALLING_CONFIG.md | Archivé dans docs/history/ |
| 2026-02-13 | 20260213_PROMPT_PLAN_LIBRAIRIE.md | Archivé dans docs/history/ |
| 2026-02-16 | config_mistral/agents/*.md | Simplification prompts (1330→482 lignes, -64%) |
| 2026-02-16 | orchestration.py | Extraction fichiers (4 stratégies), vérification renforcée, VALIDATEUR intégré |
| 2026-02-16 | file_writer.py | Logging détaillé parsing markdown |
| 2026-02-16 | mistral_client.py | Timeout adaptatif (120-300s), compression historique, max iterations 15 |
| 2026-02-16 | project_context.py | Compression contexte (max 3 niveaux, 50 fichiers, 1000 chars) |
| 2026-02-16 | language_detector.py | Détection auto langage/framework (nouveau) |
| 2026-02-16 | docs/knowledge_base/ | 4 documents créés (REGLES_STORAGE_JSON, REGLES_FRONTEND_HTML_JS, PATTERNS_PYTHON, PATTERNS_JAVASCRIPT) |
| 2026-02-16 | docs/work/20260216_PLAN_CORRECTION_COMPLET_AUDIT.md | Plan de correction détaillé (5 phases) |
| 2026-02-16 | docs/work/20260216_MODIFICATIONS_PLAN_CORRECTION.md | Récapitulatif modifications appliquées |
| 2026-02-16 | backend/ia/mistral_client.py | Protections anti-boucle (max 3 iterations, timeout 30s, détection) |
| 2026-02-16 | backend/services/orchestration.py | Ajout function_executor pour agents délégués |
| 2026-02-16 | backend/api.py | Passage function_executor à l'orchestration |
| 2026-02-16 | config_mistral/agents/JARVIS_MAITRE.md | Nettoyage complet (suppression functions, workflow simplifié) |
| 2026-02-16 | docs/history/20260216_RESOLUTION_DELEGATION_COMPLETE.md | ✅ Résolution délégation JARVIS_Maître → CODEUR validée |
| 2026-02-16 | Fichiers temporaires | Nettoyage (diagnostics, scripts de test temporaires) |
| 2026-02-18 | backend/services/orchestration.py | Correction phase EXECUTION : transition_to_execution() avant délégation CODEUR |
| 2026-02-18 | config_mistral/agents/*.md | Ajout spécification Tools (code_interpreter pour CODEUR) |
| 2026-02-18 | config_mistral/agents/CODEUR.md | Changement modèle : devstral-2 → mistral-large-3 |
| 2026-02-18 | Documentation racine | Nettoyage : 3 fichiers supprimés, 2 archivés |
| 2026-02-18 | docs/archive/ | Fusion complète dans docs/history/ (13 fichiers) |
| 2026-02-18 | docs/ racine | Archivage 6 fichiers dans docs/history/ |
| 2026-02-18 | docs/history/20260218_RAPPORT_SESSION_CORRECTION_PHASE.md | Rapport complet correction phase EXECUTION |
| 2026-02-18 | README.md | Mise à jour état actuel (v2.0 - 18/02) |
| 2026-02-18 | docs/_meta/INDEX.md | v2.3 - Structure finale après nettoyage |
| 2026-02-18 | docs/work/ | Archivage 10 fichiers dans docs/history/ (PHASE_*_RAPPORT_FINAL.md, etc.) |
| 2026-02-18 | tests/ | Réorganisation : création sous-dossiers unit/, live/, manual/ |
| 2026-02-18 | tests/live/ | Déplacement 2 tests live (test_live_projects.py, test_live_notekeeper.py) |
| 2026-02-18 | tests/manual/ | Déplacement 9 tests manuels + 1 test minimal_delegation |
| 2026-02-18 | scripts/ | Création dossier + déplacement 2 scripts utilitaires |
| 2026-02-18 | tests/README.md | Documentation structure tests + usage |
| 2026-02-18 | scripts/README.md | Documentation scripts utilitaires |
| 2026-02-18 | pyproject.toml | Exclusion tests/manual et tests/live de pytest |
| 2026-03-07 | config_agents/CODEUR.md | v3.2 → v3.3 — max_tokens=8192, format strict, cohérence noms |
| 2026-03-07 | config_agents/JARVIS_MAITRE.md | v5.1 → v5.2 — Exception projets TEST en priorité |
| 2026-03-07 | backend/agents/agent_config.py | CODEUR max_tokens 4096 → 8192 |
| 2026-03-07 | Tests live | 3/3 (100%) — Calculatrice, TODO, MiniBlog ✅ |
| 2026-03-07 | docs/work/ | Archivage 7 documents terminés vers docs/history/ |
| 2026-03-07 | docs/_meta/ETAT_ACTUEL_JARVIS_20260307.md | Création document état actuel (REFERENCE) |
| 2026-03-07 | docs/_meta/INDEX.md | v2.4 — Mise à jour structure après nettoyage |
| 2026-03-08 | backend/ia/providers/provider_factory.py | Implémentation clés API multiples (GEMINI_API_KEY_{AGENT}) |
| 2026-03-08 | backend/ia/providers/gemini_provider.py | Dictionnaire _last_request_times pour rate limiting par clé |
| 2026-03-08 | .env | Ajout 5 clés API Gemini distinctes (quota total 75 req/min) |
| 2026-03-08 | scripts/test_cles_api_multiples.py | Script test manuel clés API (5/5 clés spécifiques détectées) |
| 2026-03-08 | tests/live/ | Restructuration complète : unit/, integration/, e2e/ |
| 2026-03-08 | tests/live_archive_20260308/ | Archivage tests actuels (test_live_api.py, test_live_calculatrice.py) |
| 2026-03-08 | tests/live/README.md | Guide complet tests live (règles, exemples, plan) |
| 2026-03-08 | docs/work/SYNTHESE_MISSION_TESTS_LIVE_20260308.md | Document synthèse mission (corrections + clés API + restructuration) |
| 2026-03-08 | docs/history/ | Archivage ANALYSE_ERREURS_TESTS_LIVE.md, CORRECTIONS_TESTS_LIVE_20260308.md |
| 2026-03-08 | docs/_meta/INDEX.md | v2.5 — Mise à jour après mission tests live |

---

## 🔄 Revue Documentaire

**Dernière revue** : 2026-03-08 (Mission tests live + clés API multiples)  
**Prochaine revue prévue** : 2026-04-08  
**Responsable** : Keamder / Cascade
