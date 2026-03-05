# Proposition de Réorganisation Documentation — JARVIS 2.0

**Statut** : WORK  
**Date** : 2026-03-02  
**Objectif** : Organiser la documentation pour distinguer clairement données personnelles, méthodologies et aspects techniques

---

## 📊 Analyse de l'Existant

### Structure Actuelle
```
docs/
├── reference/        # 11 documents techniques (architecture, API, agents)
├── work/            # 6 documents en cours (audits, rapports)
├── history/         # 54 documents archivés (sessions passées)
├── knowledge_base/  # 4 documents (patterns Python/JS, règles)
├── architecture/    # 4 documents (orchestration, safety)
└── _meta/           # 6 documents (index, règles, changelog)

config_agents/       # 4 prompts agents (BASE, CODEUR, JARVIS_MAITRE, VALIDATEUR)
backend/db/library_seed.json  # 13 documents Library (librairies, méthodologies, personnel)
```

### Problèmes Identifiés

1. **Dispersion des données personnelles**
   - Préférences Val C. éparpillées dans plusieurs docs
   - Méthodologies personnelles mélangées avec docs techniques
   - Pas de centralisation des conventions de travail

2. **Confusion méthodologies vs techniques**
   - `knowledge_base/` contient des règles techniques (pas des méthodologies)
   - Méthodologies dans `library_seed.json` (pas accessibles facilement)
   - Pas de distinction claire entre "comment Val C. travaille" et "comment le code doit être écrit"

3. **Redondance et obsolescence**
   - `JARVIS_Base_Document_Complet.md` en history mais encore référencé
   - Informations personnelles dupliquées dans plusieurs fichiers
   - Pas de document unique "Profil Val C."

---

## 🎯 Proposition de Nouvelle Structure

### Principe Directeur
**3 piliers distincts** : Personnel / Méthodologie / Technique

```
docs/
├── personal/                    # 🆕 NOUVEAU — Données personnelles Val C.
│   ├── PROFIL.md               # Qui est Val C., préférences, contexte
│   ├── STACK_TECHNIQUE.md      # Technologies maîtrisées, préférées
│   ├── CONVENTIONS.md          # Conventions de code personnelles
│   ├── WORKFLOWS.md            # Workflows de travail quotidiens
│   └── HISTORIQUE_PROJETS.md  # Projets passés, expériences
│
├── methodologies/               # 🆕 NOUVEAU — Méthodes de travail
│   ├── AUDIT_PLAN_EXECUTION.md # Méthodologie universelle
│   ├── TDD_APPROACH.md         # Approche TDD de Val C.
│   ├── CODE_REVIEW.md          # Process de revue de code
│   ├── DOCUMENTATION.md        # Comment documenter (style Val C.)
│   └── DECISION_MAKING.md      # Processus de décision technique
│
├── technical/                   # 🔄 RENOMMÉ (ex-knowledge_base + reference)
│   ├── libraries/              # Références techniques librairies
│   │   ├── FASTAPI.md
│   │   ├── PYTEST.md
│   │   ├── PYDANTIC.md
│   │   ├── FLUTTER.md
│   │   └── ...
│   ├── patterns/               # Patterns de code
│   │   ├── PYTHON.md
│   │   ├── JAVASCRIPT.md
│   │   └── STORAGE_JSON.md
│   ├── architecture/           # Architecture JARVIS
│   │   ├── OVERVIEW.md
│   │   ├── AGENTS.md
│   │   ├── API.md
│   │   └── DATABASE.md
│   └── guides/                 # Guides techniques
│       ├── RAG_UTILISATION.md
│       └── MIGRATION_TIER1.md
│
├── reference/                   # Documents contractuels validés (inchangé)
├── work/                        # Documents en cours (inchangé)
├── history/                     # Archive (inchangé)
└── _meta/                       # Méta-documentation (inchangé)
```

---

## 📝 Contenu Détaillé des Nouveaux Documents

### 1. `personal/PROFIL.md`

**Objectif** : Centraliser toutes les informations sur Val C. pour personnaliser l'assistant

**Contenu** :
- Nom, rôle, contexte professionnel
- Objectifs avec JARVIS
- Style de communication préféré
- Niveau technique (langages, frameworks)
- Préférences de travail (horaires, rythme, pauses)
- Contraintes personnelles (temps limité, projets parallèles)

**Sources à consolider** :
- `JARVIS_Base_Document_Complet.md` (sections personnelles)
- `library_seed.json` (catégorie "personal")
- Mémoires Cascade actuelles

---

### 2. `personal/STACK_TECHNIQUE.md`

**Objectif** : Documenter les technologies maîtrisées et préférées

**Contenu** :
- **Langages** : Python (expert), JavaScript (avancé), Dart/Flutter (intermédiaire)
- **Frameworks** : FastAPI (préféré), React (connu), Flutter (en cours)
- **Outils** : Git, VSCode, Windsurf, pytest
- **Bases de données** : SQLite (préféré pour projets perso), PostgreSQL (connu)
- **IA/ML** : Mistral AI, Gemini, OpenRouter, RAG
- **Préférences** :
  - Backend : FastAPI > Flask
  - Frontend : Vanilla JS > React (pour projets simples)
  - Tests : pytest + TDD obligatoire
  - Base de données : SQLite pour prototypes, PostgreSQL pour production

---

### 3. `personal/CONVENTIONS.md`

**Objectif** : Conventions de code personnelles de Val C.

**Contenu** :
- **Nommage** :
  - Variables : `snake_case`
  - Classes : `PascalCase`
  - Constantes : `UPPER_SNAKE_CASE`
  - Fichiers : `snake_case.py`
- **Structure de projet** :
  - Backend : `backend/` avec `agents/`, `db/`, `services/`, `models.py`, `api.py`, `app.py`
  - Frontend : `frontend/` avec `css/`, `js/`, `index.html`
  - Tests : `tests/` avec structure miroir du code
- **Documentation** :
  - Docstrings obligatoires pour fonctions publiques
  - README.md à jour
  - Changelog pour versions
- **Git** :
  - Commits en français
  - Messages descriptifs (pas de "fix", "update")
  - Branches : `feature/`, `fix/`, `refactor/`

---

### 4. `personal/WORKFLOWS.md`

**Objectif** : Documenter les workflows de travail quotidiens

**Contenu** :
- **Démarrage de session** :
  1. Lire `jarvis_audit.log` (dernières actions)
  2. Vérifier état projet (tests, erreurs)
  3. Définir objectif de session
- **Développement d'une feature** :
  1. Audit de l'existant
  2. Plan d'exécution validé
  3. Implémentation TDD
  4. Tests + validation
  5. Documentation
- **Résolution de bug** :
  1. Reproduction du bug
  2. Diagnostic (logs, tests)
  3. Fix minimal
  4. Test de non-régression
  5. Documentation
- **Fin de session** :
  1. Commit des changements
  2. Mise à jour CHANGELOG
  3. Rapport de session (si pertinent)

---

### 5. `personal/HISTORIQUE_PROJETS.md`

**Objectif** : Tracer les projets passés pour contexte et apprentissage

**Contenu** :
- **JARVIS 1.0** : Première version (architecture, leçons apprises)
- **JARVIS 2.0** : Version actuelle (évolutions, décisions clés)
- **Projets annexes** : Autres projets Python/Flutter
- **Expériences marquantes** :
  - Migration Mistral → Gemini (quotas, performances)
  - Implémentation RAG (ChromaDB, embeddings)
  - Orchestration multi-agents (délégation, validation)

---

### 6. `methodologies/AUDIT_PLAN_EXECUTION.md`

**Objectif** : Méthodologie universelle de Val C.

**Contenu** :
```
1. AUDIT
   - Analyser l'existant (code, architecture, dette)
   - Identifier les risques
   - Lister les contraintes

2. PLAN
   - Définir les étapes
   - Séquencer les actions
   - Identifier les points de validation

3. VALIDATION
   - Présenter le plan à Val C.
   - Attendre validation explicite
   - Ajuster si nécessaire

4. EXÉCUTION
   - Implémenter selon le plan
   - Tests à chaque étape
   - Journalisation des actions

5. DOCUMENTATION
   - Mettre à jour README
   - Documenter les décisions
   - Archiver les rapports
```

---

### 7. `methodologies/TDD_APPROACH.md`

**Objectif** : Approche TDD de Val C.

**Contenu** :
- **Principe** : Red → Green → Refactor
- **Règles** :
  - Écrire le test AVANT le code
  - 1 test = 1 comportement
  - Tests unitaires + tests d'intégration
  - Couverture > 80% obligatoire
- **Structure de test** :
  - Arrange (setup)
  - Act (action)
  - Assert (vérification)
- **Outils** : pytest, fixtures, parametrize, tmp_path

---

## 🔄 Migration Proposée

### Étape 1 : Créer la nouvelle structure
```bash
mkdir -p docs/personal
mkdir -p docs/methodologies
mkdir -p docs/technical/libraries
mkdir -p docs/technical/patterns
mkdir -p docs/technical/architecture
mkdir -p docs/technical/guides
```

### Étape 2 : Créer les documents personnels
- Extraire infos de `JARVIS_Base_Document_Complet.md`
- Extraire infos de `library_seed.json` (catégorie "personal")
- Consolider mémoires Cascade
- Créer `PROFIL.md`, `STACK_TECHNIQUE.md`, `CONVENTIONS.md`, `WORKFLOWS.md`, `HISTORIQUE_PROJETS.md`

### Étape 3 : Créer les documents méthodologies
- Extraire de `library_seed.json` (catégorie "methodologies")
- Créer `AUDIT_PLAN_EXECUTION.md`, `TDD_APPROACH.md`, `CODE_REVIEW.md`, `DOCUMENTATION.md`, `DECISION_MAKING.md`

### Étape 4 : Réorganiser documents techniques
- Migrer `knowledge_base/` → `technical/patterns/`
- Migrer `reference/` (docs techniques) → `technical/architecture/` et `technical/guides/`
- Extraire de `library_seed.json` (catégorie "libraries") → `technical/libraries/`

### Étape 5 : Mettre à jour `library_seed.json`
- Pointer vers les nouveaux fichiers
- Ajouter références aux documents personnels
- Ajouter références aux méthodologies

### Étape 6 : Mettre à jour `_meta/INDEX.md`
- Documenter la nouvelle structure
- Créer des liens vers les 3 piliers
- Expliquer la logique d'organisation

---

## 🎯 Bénéfices Attendus

### Pour Val C.
✅ **Centralisation** : Toutes les infos personnelles au même endroit  
✅ **Clarté** : Distinction nette personnel / méthodologie / technique  
✅ **Accessibilité** : Retrouver rapidement une info  
✅ **Évolutivité** : Facile d'ajouter de nouvelles conventions  

### Pour l'Assistant IA
✅ **Personnalisation** : Accès direct au profil et préférences  
✅ **Cohérence** : Respecter les méthodologies documentées  
✅ **Contexte** : Comprendre l'historique et les décisions passées  
✅ **Autonomie** : Moins de questions, plus d'actions alignées  

### Pour le Projet
✅ **Documentation structurée** : Logique claire et maintenable  
✅ **Onboarding facilité** : Nouvelle IA comprend rapidement le contexte  
✅ **Traçabilité** : Décisions et évolutions documentées  
✅ **Scalabilité** : Structure prête pour croissance du projet  

---

## ❓ Questions pour Validation

1. **Structure** : Les 3 piliers (personal / methodologies / technical) sont-ils pertinents ?
2. **Contenu personnel** : Quelles informations ajouter dans `PROFIL.md` ?
3. **Méthodologies** : Y a-t-il d'autres workflows à documenter ?
4. **Priorités** : Quel document créer en premier ?
5. **Migration** : Faut-il archiver les anciens documents ou les supprimer ?

---

## 📋 Plan d'Exécution (après validation)

1. ✅ Créer l'arborescence `personal/`, `methodologies/`, `technical/`
2. ✅ Créer `personal/PROFIL.md` (document prioritaire)
3. ✅ Créer `personal/STACK_TECHNIQUE.md`
4. ✅ Créer `personal/CONVENTIONS.md`
5. ✅ Créer `methodologies/AUDIT_PLAN_EXECUTION.md`
6. ✅ Migrer documents techniques vers `technical/`
7. ✅ Mettre à jour `library_seed.json`
8. ✅ Mettre à jour `_meta/INDEX.md`
9. ✅ Archiver anciens documents dans `history/`
10. ✅ Tester accessibilité depuis frontend Library

---

**Prochaine étape** : Validation de la proposition par Val C.
