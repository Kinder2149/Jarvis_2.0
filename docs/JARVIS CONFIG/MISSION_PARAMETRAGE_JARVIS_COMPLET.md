# MISSION : PARAMÉTRAGE COMPLET DE JARVIS 2.0

**Date** : 6 mars 2026  
**Objectif** : Paramétrer JARVIS 2.0 (agents, workflow, library) pour remplacer Windsurf comme assistant principal de Keamder

---

# 📋 CONTEXTE

## Qui est Keamder ?

**Valentin Coutry (Keamder)** est un **pilote de projet assisté par IA à 100%**, PAS un développeur autonome.

**Caractéristiques** :
- ✅ **0% de production de code autonome** : Ne code JAMAIS sans IA
- ✅ **100% de dépendance à l'IA** pour toute génération de code
- ✅ **Forte capacité de conception produit** : Vision claire du besoin utilisateur
- ✅ **Bonne compréhension conceptuelle** de l'architecture logicielle
- ✅ **Capacité à piloter un projet technique** via IA (workflow structuré)

**Difficultés principales** :
1. **Pilotage IA** (prioritaire) : Communication avec IA, compréhension code généré, maintien cohérence, choix technologiques
2. **Techniques** (secondaire, gérées par IA) : Configuration .env, migrations BDD, auth complexe, déploiement

**Forces réelles** :
- Vision produit claire (9 projets dont 3 en production)
- Workflow structuré et rigoureux (documentation systématique)
- Persévérance et itérations (ne lâche pas avant que ça marche)
- Tests manuels rigoureux (interface réelle + logs)
- Capacité d'apprentissage (2 ans, 9 projets variés)

---

## Qu'est-ce que JARVIS 2.0 ?

**JARVIS 2.0** est un assistant IA multi-agent pour génération de code, conçu pour remplacer Windsurf.

**Architecture actuelle** :
- **JARVIS_Maître** (gemini-2.0-flash) : Orchestrateur, interface avec Keamder
- **CODEUR** (gemini-2.5-pro) : Génération code uniquement
- **BASE** (gemini-2.0-flash-lite) : Validation, vérification complétude
- **VALIDATEUR** (gemini-3.1-pro-preview) : 📋 Prévu, non implémenté

**Statut actuel** : 🔄 EN COURS DE PARAMÉTRAGE
- ✅ Backend fonctionnel (99% tests)
- ✅ Orchestration JARVIS_Maître → CODEUR/BASE
- ✅ Génération code sur disque
- 🔄 Intégration documents CONFIG dans Library
- 📋 Agent VALIDATEUR non implémenté
- 📋 Documentation utilisateur manquante

**Objectif** : Remplacer Windsurf comme assistant principal de Keamder

---

# 🎯 MISSION COMPLÈTE

## Objectif Principal

Paramétrer JARVIS 2.0 pour qu'il soit **utilisable quotidiennement** par Keamder en tant qu'assistant principal, en remplacement de Windsurf.

## Sous-Objectifs

### 1. Paramétrer les Agents
- Définir prompts système pour JARVIS_Maître, CODEUR, BASE
- Adapter communication pour un pilote IA (pas développeur)
- Intégrer règles absolues (Pydantic v2, Storage JSON, etc.)

### 2. Configurer la Library
- Intégrer les 5 documents CONFIG dans `backend/db/library_seed.json`
- Catégorie "personal"
- Vérifier accessibilité via function `get_library_document`

### 3. Définir le Workflow
- Workflow standard en 6 phases (Analyse → Validation → Génération → Config → Tests → Debugging)
- Gestion mémoire et contexte (rappel automatique)
- Documentation automatique (README, plan.md, .env.example)

### 4. Créer Documentation Utilisateur
- Guide démarrage rapide
- Exemples concrets (TODO list, site avec auth)
- Troubleshooting

### 5. Tester et Valider
- Test création projet simple (TODO list)
- Vérification génération code + documentation
- Validation workflow complet

---

# 📚 RÉFÉRENCES DOCUMENTAIRES

## Documents CONFIG (Base de Travail)

Ces 5 documents sont la **source de vérité** pour paramétrer JARVIS :

### 1. `KEAMDER_PROFILE.md`
**Contenu** : Profil complet de Keamder
- Positionnement : Pilote de projet IA 100%
- Compétences : Technologies pilotées via IA
- Difficultés : Pilotage IA (prioritaire) + Techniques (secondaire)
- Forces réelles : Vision produit, workflow structuré, persévérance
- 9 projets réalisés dont 3 en production

**Utilité pour paramétrage** :
- Adapter communication agents (langage clair, pas jargon)
- Définir niveau d'explication requis
- Identifier difficultés à anticiper

### 2. `KEAMDER_WORKFLOW.md`
**Contenu** : Méthodologie de travail de Keamder
- Workflow en 5 phases (Idée → Challenge → Plan → Génération → Tests → Amélioration)
- Pratiques réelles (documentation systématique, tests manuels, versioning)
- Gestion échecs et debugging (critères abandon, sources aide externe)
- Stack normalisée préférée (Python/FastAPI, HTML/CSS/JS vanilla, SQLite/Supabase)

**Utilité pour paramétrage** :
- Définir workflow standard JARVIS
- Configurer génération documentation automatique
- Paramétrer stack par défaut

### 3. `JARVIS_ARCHITECTURE.md`
**Contenu** : Architecture JARVIS 2.0
- 4 agents (JARVIS_Maître, CODEUR, BASE, VALIDATEUR)
- Stack et services (Python/FastAPI, Gemini API Tier 1, Supabase, Vercel)
- Flux de travail (orchestration, délégation, protections anti-boucle)
- Statut actuel et roadmap

**Utilité pour paramétrage** :
- Comprendre architecture existante
- Identifier ce qui fonctionne vs ce qui manque
- Définir prochaines étapes

### 4. `KEAMDER_DEV_RULES.md`
**Contenu** : Règles d'orchestration pour IA
- Principes fondamentaux (pas d'invention, structuration, validation)
- Workflow (phases, traçabilité, validation obligatoire)
- Règles spécifiques pour pilote IA (communication adaptée, proposer avant exécuter, guider tests)
- Règles absolues CODEUR (Pydantic v2, Storage JSON, cohérence)

**Utilité pour paramétrage** :
- Définir règles comportementales agents
- Configurer validation obligatoire
- Intégrer règles techniques CODEUR

### 5. `JARVIS_COMPORTEMENT_GENERIQUE.md`
**Contenu** : Comportement générique JARVIS
- Workflow standard en 6 phases détaillées
- Stack par défaut (ordre de préférence)
- Gestion mémoire et contexte (rappel automatique)
- Documentation automatique (README, plan.md, .env.example)
- Gestion échecs (critères abandon, aide externe)
- Exemples concrets (site avec auth, app mobile)

**Utilité pour paramétrage** :
- Template workflow standard
- Exemples de communication avec Keamder
- Gestion cas d'usage réels

---

# 🔧 MÉTHODE DE TRAVAIL

## Phase 1 : Analyse et Compréhension

### 1.1 Lire les 5 Documents CONFIG
- Lire intégralement chaque document
- Identifier informations clés pour paramétrage
- Noter incohérences ou manques éventuels

### 1.2 Analyser Architecture Actuelle
- Lire fichiers backend existants :
  - `backend/agents/jarvis_maitre.py`
  - `backend/agents/codeur.py`
  - `backend/agents/base_agent.py`
  - `backend/services/orchestration.py`
  - `backend/db/library_seed.json`
- Comprendre fonctionnement actuel
- Identifier points à modifier

### 1.3 Définir Plan de Paramétrage
- Lister toutes les modifications nécessaires
- Prioriser (critique → important → nice-to-have)
- Estimer complexité

---

## Phase 2 : Paramétrage des Agents

### 2.1 JARVIS_Maître

**Fichier** : `config_gemini/agents/JARVIS_MAITRE.md` (ou équivalent)

**Contenu à définir** :
```markdown
# JARVIS_MAÎTRE - Prompt Système

## Identité
Tu es JARVIS_Maître, assistant personnel de Valentin Coutry (Keamder).

## Contexte Utilisateur
Keamder est un **pilote de projet assisté par IA à 100%**, PAS un développeur autonome.
- 0% de production de code autonome
- 100% de dépendance à l'IA pour génération code
- Forte capacité de conception produit
- Difficultés : Pilotage IA (communication, compréhension code, cohérence)

## Ton Rôle
1. **Orchestrateur** : Déléguer aux agents spécialisés (CODEUR, BASE)
2. **Traducteur** : Besoin français → Architecture technique
3. **Guide** : Expliquer en français clair, guider tests manuels
4. **Mémoire** : Rappeler contexte à chaque session

## Règles Absolues
1. **Proposer AVANT de générer** : Jamais de génération directe sans validation
2. **Expliquer en français clair** : Pas de jargon sans explication
3. **Guider tests manuels** : Instructions précises (Lance X, clique Y, tu dois voir Z)
4. **Rappeler contexte** : À chaque session, rappeler projet, stack, dernière action
5. **Respecter stack normalisée** : Python/FastAPI par défaut, alerter si déviation

## Workflow Standard
[Détailler les 6 phases du workflow]

## Délégation
- `[DEMANDE_CODE_CODEUR: ...]` : Génération code
- `[DEMANDE_VALIDATION_BASE: ...]` : Vérification complétude

## Documents de Référence
- KEAMDER_PROFILE.md : Profil utilisateur
- KEAMDER_WORKFLOW.md : Méthodologie
- KEAMDER_DEV_RULES.md : Règles orchestration
- JARVIS_COMPORTEMENT_GENERIQUE.md : Workflow standard
```

**Actions** :
1. Créer/Modifier fichier prompt JARVIS_Maître
2. Intégrer workflow standard complet
3. Ajouter exemples de communication
4. Tester avec prompt simple

### 2.2 CODEUR

**Fichier** : `config_gemini/agents/CODEUR.md` (ou équivalent)

**Contenu à définir** :
```markdown
# CODEUR - Prompt Système

## Identité
Tu es CODEUR, agent spécialisé dans la génération de code pour JARVIS 2.0.

## Ton Rôle
Générer du code de qualité selon les spécifications de JARVIS_Maître.

## Règles Absolues (NON NÉGOCIABLES)

### Règle 1 : Storage JSON
Une classe Storage doit TOUJOURS avoir :
1. `__init__(self, filepath: str)`
2. `save(self, data)`
3. `load(self) -> data`

### Règle 2 : Pydantic v2
- `.model_dump()` au lieu de `.dict()`
- `.model_validate()` au lieu de `.parse_obj()`
- `.model_copy()` au lieu de `.copy()`

### Règle 3 : Cohérence
Vérifier AVANT de livrer :
- Si classe A utilise classe B : B est importée
- Si classe A attend instance de B : B a un constructeur
- Si tests appellent Classe(args) : Classe a un __init__

### Règle 4 : Tests
NE PAS ajouter tests pour fonctionnalités non implémentées

## Stack par Défaut
- Backend : Python 3.11+ + FastAPI
- Frontend : HTML/CSS/JS vanilla (simple) ou Angular (complexe)
- BDD : SQLite (dev) ou PostgreSQL/Supabase (production)
- Auth : Supabase Auth (JWT RS256)

## Génération Code
- Fichiers complets et autonomes
- Imports absolus simples
- Pas de commentaires sauf si demandé
- Code immédiatement exécutable
```

**Actions** :
1. Créer/Modifier fichier prompt CODEUR
2. Intégrer règles absolues
3. Ajouter stack par défaut
4. Tester génération code simple

### 2.3 BASE

**Fichier** : `config_gemini/agents/BASE.md` (ou équivalent)

**Contenu à définir** :
```markdown
# BASE - Prompt Système

## Identité
Tu es BASE, agent polyvalent de validation et vérification pour JARVIS 2.0.

## Ton Rôle
Valider la complétude du code généré et produire des rapports.

## Functions Disponibles
- `get_project_file` : Lire fichiers projet
- `get_project_structure` : Structure arborescence
- `get_library_document` : Accès documents library
- `get_library_list` : Liste documents disponibles

## Responsabilités
1. Vérifier complétude code généré
2. Valider présence fichiers attendus
3. Rapports d'état (COMPLET / INCOMPLET)
4. Analyse erreurs et logs

## Format Rapport
```
RAPPORT VALIDATION

FICHIERS ATTENDUS :
- [fichier 1] : ✅ Présent / ❌ Manquant
- [fichier 2] : ✅ Présent / ❌ Manquant

VÉRIFICATIONS :
- [vérification 1] : ✅ OK / ❌ KO
- [vérification 2] : ✅ OK / ❌ KO

STATUT GLOBAL : COMPLET / INCOMPLET

RECOMMANDATIONS :
- [recommandation 1]
- [recommandation 2]
```
```

**Actions** :
1. Créer/Modifier fichier prompt BASE
2. Définir format rapport standard
3. Tester validation fichiers

---

## Phase 3 : Configuration Library

### 3.1 Intégrer Documents CONFIG

**Fichier** : `backend/db/library_seed.json`

**Modifications** :
```json
{
  "documents": [
    {
      "id": "keamder_profile",
      "title": "KEAMDER_PROFILE",
      "category": "personal",
      "content": "[Contenu KEAMDER_PROFILE.md]",
      "metadata": {
        "type": "profile",
        "version": "1.0",
        "last_updated": "2026-03-06"
      }
    },
    {
      "id": "keamder_workflow",
      "title": "KEAMDER_WORKFLOW",
      "category": "personal",
      "content": "[Contenu KEAMDER_WORKFLOW.md]",
      "metadata": {
        "type": "workflow",
        "version": "1.0",
        "last_updated": "2026-03-06"
      }
    },
    {
      "id": "jarvis_architecture",
      "title": "JARVIS_ARCHITECTURE",
      "category": "personal",
      "content": "[Contenu JARVIS_ARCHITECTURE.md]",
      "metadata": {
        "type": "architecture",
        "version": "1.0",
        "last_updated": "2026-03-06"
      }
    },
    {
      "id": "keamder_dev_rules",
      "title": "KEAMDER_DEV_RULES",
      "category": "personal",
      "content": "[Contenu KEAMDER_DEV_RULES.md]",
      "metadata": {
        "type": "rules",
        "version": "1.0",
        "last_updated": "2026-03-06"
      }
    },
    {
      "id": "jarvis_comportement_generique",
      "title": "JARVIS_COMPORTEMENT_GENERIQUE",
      "category": "personal",
      "content": "[Contenu JARVIS_COMPORTEMENT_GENERIQUE.md]",
      "metadata": {
        "type": "behavior",
        "version": "1.0",
        "last_updated": "2026-03-06"
      }
    }
  ]
}
```

**Actions** :
1. Lire contenu des 5 fichiers .md
2. Ajouter à library_seed.json
3. Vérifier format JSON valide
4. Redémarrer backend pour charger

### 3.2 Tester Accès Library

**Test** :
```python
# Via function get_library_document
result = get_library_document("keamder_profile")
# Doit retourner contenu KEAMDER_PROFILE.md
```

**Actions** :
1. Tester accès chaque document
2. Vérifier contenu complet
3. Valider métadonnées

---

## Phase 4 : Documentation Utilisateur

### 4.1 Guide Démarrage Rapide

**Fichier** : `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`

**Contenu** :
```markdown
# Guide Démarrage Rapide - JARVIS 2.0

## Installation

1. Clone le projet
2. Configure .env
3. Lance backend : `uvicorn backend.app:app --reload`
4. Lance frontend : Ouvre `frontend/index.html`

## Premier Projet

### Exemple : TODO List Simple

1. **Exprime ton besoin** :
   "Je veux une TODO list simple avec Python FastAPI"

2. **JARVIS propose architecture** :
   - Backend : Python + FastAPI
   - Frontend : HTML/CSS/JS vanilla
   - BDD : SQLite

3. **Tu valides** :
   "OK génère"

4. **JARVIS génère code** :
   - backend/main.py
   - backend/models.py
   - frontend/index.html
   - frontend/app.js

5. **JARVIS guide tests** :
   "Lance backend : uvicorn main:app --reload
   Ouvre frontend/index.html
   Ajoute une tâche, tu dois voir..."

6. **Tu testes et valides** :
   "Ça marche !"

## Troubleshooting

[Problèmes courants et solutions]
```

**Actions** :
1. Créer guide démarrage rapide
2. Ajouter exemples concrets
3. Ajouter troubleshooting

### 4.2 Exemples Concrets

**Fichier** : `docs/reference/EXEMPLES_PROJETS.md`

**Contenu** :
- Exemple 1 : TODO list simple (Python/FastAPI)
- Exemple 2 : Site avec auth (Supabase)
- Exemple 3 : App mobile (Flutter)

**Actions** :
1. Créer 3 exemples détaillés
2. Inclure prompts utilisateur
3. Inclure réponses JARVIS attendues

---

## Phase 5 : Tests et Validation

### 5.1 Test Création Projet Simple

**Projet test** : TODO list simple

**Étapes** :
1. Lancer JARVIS
2. Prompt : "Je veux une TODO list simple avec Python FastAPI"
3. Vérifier proposition architecture
4. Valider : "OK génère"
5. Vérifier génération fichiers :
   - backend/main.py
   - backend/models.py
   - frontend/index.html
   - frontend/app.js
   - README.md
   - docs/plan.md
   - .env.example
6. Vérifier documentation auto
7. Tester code généré

**Critères succès** :
- ✅ Architecture proposée cohérente avec stack normalisée
- ✅ Tous fichiers générés
- ✅ Documentation auto créée
- ✅ Code exécutable sans erreur
- ✅ Tests manuels passent

### 5.2 Test Workflow Complet

**Scénario** : Projet avec erreur

**Étapes** :
1. Créer projet
2. Introduire erreur volontaire
3. Tester debugging JARVIS
4. Vérifier explication en français clair
5. Vérifier correction proposée
6. Valider correction

**Critères succès** :
- ✅ JARVIS détecte erreur
- ✅ Explication claire en français
- ✅ Correction proposée valide
- ✅ Workflow debugging fonctionne

### 5.3 Test Gestion Mémoire

**Scénario** : Nouvelle session

**Étapes** :
1. Créer projet session 1
2. Fermer JARVIS
3. Rouvrir JARVIS session 2
4. Vérifier rappel contexte automatique

**Critères succès** :
- ✅ JARVIS rappelle projet en cours
- ✅ JARVIS rappelle stack utilisée
- ✅ JARVIS rappelle dernière action
- ✅ JARVIS propose prochaines étapes

---

# 📝 TRAVAIL À FAIRE (CHECKLIST COMPLÈTE)

## ✅ Phase 1 : Analyse et Compréhension

- [ ] Lire KEAMDER_PROFILE.md intégralement
- [ ] Lire KEAMDER_WORKFLOW.md intégralement
- [ ] Lire JARVIS_ARCHITECTURE.md intégralement
- [ ] Lire KEAMDER_DEV_RULES.md intégralement
- [ ] Lire JARVIS_COMPORTEMENT_GENERIQUE.md intégralement
- [ ] Analyser `backend/agents/jarvis_maitre.py`
- [ ] Analyser `backend/agents/codeur.py`
- [ ] Analyser `backend/agents/base_agent.py`
- [ ] Analyser `backend/services/orchestration.py`
- [ ] Analyser `backend/db/library_seed.json`
- [ ] Créer plan de paramétrage détaillé

## ✅ Phase 2 : Paramétrage des Agents

### JARVIS_Maître
- [ ] Créer/Modifier prompt système JARVIS_Maître
- [ ] Intégrer workflow standard 6 phases
- [ ] Ajouter règles communication (français clair, pas jargon)
- [ ] Ajouter règles validation obligatoire
- [ ] Ajouter exemples de communication
- [ ] Intégrer gestion mémoire (rappel contexte)
- [ ] Tester prompt avec requête simple

### CODEUR
- [ ] Créer/Modifier prompt système CODEUR
- [ ] Intégrer règles absolues (Pydantic v2, Storage JSON, Cohérence, Tests)
- [ ] Définir stack par défaut
- [ ] Ajouter règles génération code (fichiers complets, imports absolus)
- [ ] Tester génération code simple

### BASE
- [ ] Créer/Modifier prompt système BASE
- [ ] Définir format rapport validation
- [ ] Tester validation fichiers
- [ ] Tester accès library documents

## ✅ Phase 3 : Configuration Library

- [ ] Lire contenu KEAMDER_PROFILE.md
- [ ] Lire contenu KEAMDER_WORKFLOW.md
- [ ] Lire contenu JARVIS_ARCHITECTURE.md
- [ ] Lire contenu KEAMDER_DEV_RULES.md
- [ ] Lire contenu JARVIS_COMPORTEMENT_GENERIQUE.md
- [ ] Ajouter 5 documents à library_seed.json (catégorie "personal")
- [ ] Vérifier format JSON valide
- [ ] Redémarrer backend
- [ ] Tester accès via `get_library_document("keamder_profile")`
- [ ] Tester accès aux 5 documents

## ✅ Phase 4 : Documentation Utilisateur

- [ ] Créer `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`
- [ ] Ajouter section Installation
- [ ] Ajouter section Premier Projet (exemple TODO list)
- [ ] Ajouter section Troubleshooting
- [ ] Créer `docs/reference/EXEMPLES_PROJETS.md`
- [ ] Ajouter Exemple 1 : TODO list simple
- [ ] Ajouter Exemple 2 : Site avec auth
- [ ] Ajouter Exemple 3 : App mobile (optionnel)

## ✅ Phase 5 : Tests et Validation

### Test 1 : Création Projet Simple
- [ ] Lancer JARVIS
- [ ] Prompt : "Je veux une TODO list simple avec Python FastAPI"
- [ ] Vérifier proposition architecture
- [ ] Valider : "OK génère"
- [ ] Vérifier génération fichiers (backend/main.py, frontend/index.html, etc.)
- [ ] Vérifier documentation auto (README.md, docs/plan.md, .env.example)
- [ ] Tester code généré (lancer backend + frontend)
- [ ] Valider tests manuels

### Test 2 : Workflow Debugging
- [ ] Créer projet avec erreur volontaire
- [ ] Tester debugging JARVIS
- [ ] Vérifier explication en français clair
- [ ] Vérifier correction proposée
- [ ] Valider correction

### Test 3 : Gestion Mémoire
- [ ] Créer projet session 1
- [ ] Fermer JARVIS
- [ ] Rouvrir JARVIS session 2
- [ ] Vérifier rappel contexte automatique

## ✅ Phase 6 : Finalisation

- [ ] Documenter toutes les modifications effectuées
- [ ] Créer rapport final de paramétrage
- [ ] Lister points d'amélioration futurs
- [ ] Valider avec Keamder

---

# 🎯 CRITÈRES DE SUCCÈS

## Critères Obligatoires (Must Have)

1. ✅ **Agents paramétrés** : JARVIS_Maître, CODEUR, BASE ont prompts système adaptés
2. ✅ **Library configurée** : 5 documents CONFIG accessibles via `get_library_document`
3. ✅ **Workflow fonctionnel** : Création projet simple fonctionne de bout en bout
4. ✅ **Documentation créée** : Guide démarrage rapide + exemples concrets
5. ✅ **Tests passent** : Test création projet simple réussi

## Critères Souhaitables (Should Have)

6. ✅ **Debugging fonctionne** : Workflow debugging avec explication claire
7. ✅ **Gestion mémoire** : Rappel contexte automatique entre sessions
8. ✅ **Documentation auto** : README.md, plan.md, .env.example générés automatiquement

## Critères Optionnels (Nice to Have)

9. ✅ **Agent VALIDATEUR** : Implémenté et fonctionnel
10. ✅ **Tests avancés** : Projet avec auth, frontend complexe, mobile

---

# 📂 FICHIERS À MODIFIER/CRÉER

## Fichiers à Modifier

1. `config_gemini/agents/JARVIS_MAITRE.md` (ou équivalent)
2. `config_gemini/agents/CODEUR.md` (ou équivalent)
3. `config_gemini/agents/BASE.md` (ou équivalent)
4. `backend/db/library_seed.json`

## Fichiers à Créer

1. `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`
2. `docs/reference/EXEMPLES_PROJETS.md`
3. `docs/work/RAPPORT_PARAMETRAGE_JARVIS.md` (rapport final)

## Fichiers de Référence (Ne PAS Modifier)

1. `docs/JARVIS CONFIG/KEAMDER_PROFILE.md`
2. `docs/JARVIS CONFIG/KEAMDER_WORKFLOW.md`
3. `docs/JARVIS CONFIG/JARVIS_ARCHITECTURE.md`
4. `docs/JARVIS CONFIG/KEAMDER_DEV_RULES.md`
5. `docs/JARVIS CONFIG/JARVIS_COMPORTEMENT_GENERIQUE.md`

---

# 🚀 DÉMARRAGE DE LA MISSION

## Étape 1 : Lecture et Compréhension

Commence par lire les 5 documents CONFIG dans cet ordre :

1. **KEAMDER_PROFILE.md** : Comprendre qui est Keamder
2. **KEAMDER_WORKFLOW.md** : Comprendre sa méthodologie
3. **JARVIS_ARCHITECTURE.md** : Comprendre architecture JARVIS
4. **KEAMDER_DEV_RULES.md** : Comprendre règles orchestration
5. **JARVIS_COMPORTEMENT_GENERIQUE.md** : Comprendre workflow standard

## Étape 2 : Analyse Architecture Actuelle

Lire les fichiers backend pour comprendre implémentation actuelle :
- `backend/agents/jarvis_maitre.py`
- `backend/agents/codeur.py`
- `backend/agents/base_agent.py`
- `backend/services/orchestration.py`
- `backend/db/library_seed.json`

## Étape 3 : Créer Plan Détaillé

Créer un plan de paramétrage détaillé avec :
- Liste complète des modifications nécessaires
- Priorisation (critique → important → nice-to-have)
- Estimation complexité
- Ordre d'exécution

## Étape 4 : Exécution

Suivre le plan et la checklist complète ci-dessus.

## Étape 5 : Tests et Validation

Tester chaque modification et valider avec les critères de succès.

## Étape 6 : Rapport Final

Créer rapport final documentant :
- Toutes les modifications effectuées
- Résultats des tests
- Points d'amélioration futurs
- Recommandations

---

# ⚠️ POINTS D'ATTENTION

## Règles Absolues à Respecter

1. **NE PAS modifier les 5 documents CONFIG** : Ce sont les références, pas les fichiers de travail
2. **Tester chaque modification** : Ne pas accumuler modifications sans tests
3. **Documenter toutes les modifications** : Traçabilité complète
4. **Valider avec critères de succès** : Vérifier chaque critère

## Difficultés Anticipées

1. **Intégration Library** : Format JSON, échappement caractères
2. **Prompts agents** : Trouver bon équilibre détail vs concision
3. **Tests workflow complet** : Nécessite backend + frontend fonctionnels
4. **Gestion mémoire** : Implémentation rappel contexte automatique

## Solutions Recommandées

1. **Intégration Library** : Utiliser outil validation JSON, tester accès après chaque ajout
2. **Prompts agents** : Commencer simple, itérer selon résultats tests
3. **Tests workflow** : Tester par étapes (backend seul, puis frontend, puis ensemble)
4. **Gestion mémoire** : Utiliser base SQLite existante, ajouter fonction rappel contexte

---

# 📊 LIVRABLES ATTENDUS

## Livrables Obligatoires

1. **Prompts agents paramétrés** :
   - `config_gemini/agents/JARVIS_MAITRE.md`
   - `config_gemini/agents/CODEUR.md`
   - `config_gemini/agents/BASE.md`

2. **Library configurée** :
   - `backend/db/library_seed.json` avec 5 documents CONFIG

3. **Documentation utilisateur** :
   - `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`
   - `docs/reference/EXEMPLES_PROJETS.md`

4. **Rapport final** :
   - `docs/work/RAPPORT_PARAMETRAGE_JARVIS.md`

## Livrables Optionnels

5. **Agent VALIDATEUR** :
   - `config_gemini/agents/VALIDATEUR.md`
   - `backend/agents/validateur.py`

6. **Tests avancés** :
   - Projet avec auth (Supabase)
   - Projet frontend complexe (Angular)
   - Projet mobile (Flutter)

---

# ✅ VALIDATION FINALE

Une fois la mission terminée, valider que :

1. ✅ Les 5 documents CONFIG sont intégrés dans Library
2. ✅ Les 3 agents (JARVIS_Maître, CODEUR, BASE) ont prompts système adaptés
3. ✅ Le workflow standard fonctionne (création projet simple)
4. ✅ La documentation utilisateur est créée
5. ✅ Les tests passent (création projet, debugging, gestion mémoire)
6. ✅ Le rapport final est rédigé

**Si tous ces critères sont validés, JARVIS 2.0 est prêt pour utilisation quotidienne par Keamder.** 🚀

---

# 📞 CONTACT

**Keamder (Valentin Coutry)**
- Email : valentin.coutry@gmail.com
- Localisation : Lille, France
- Disponibilité : 2h à 35h+/semaine, sessions 2h-8h, soir privilégié

**En cas de blocage** :
1. Documenter le problème précisément
2. Lister solutions tentées
3. Demander aide à Keamder avec contexte complet
