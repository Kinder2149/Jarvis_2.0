# KEAMDER_WORKFLOW.md
Méthodologie de travail — Keamder

---

# 1. PRINCIPES GÉNÉRAUX

- Toute idée passe par un processus clair : réflexion → plan → génération → test → amélioration
- Séparer **phase réflexion** / **phase implémentation**
- Toujours documenter et structurer le projet avant le déploiement
- Garder une trace des décisions et versions précédentes
- Tout test doit être **observable et vérifiable** (interface réelle + logs)

---

# 2. WORKFLOW TYPE (CONFIRMÉ SUR 5+ PROJETS)

## Phase 1 : Idée → Challenge IA
**Confirmé** : Tous projets (JARVIS, UFM, TerraNova, PaperClip2, Atelier)

1. **Expression besoin**
   - Définir besoins fonctionnels en **langage naturel français**
   - Identifier utilisateurs et rôles
   - Imaginer écrans et flux
   - Décrire problème à résoudre

2. **Challenge avec IA**
   - Laisser l'IA proposer architecture technique
   - Laisser l'IA proposer stack adaptée
   - Corriger, compléter et valider la proposition
   - Itérations jusqu'à validation

**ÉVOLUTION AVEC JARVIS 2.0** :
- **Avant** : Keamder créait les prompts pour l'IA
- **Maintenant** : JARVIS_Maître orchestre le travail inter-agents
- **Keamder** : Exprime uniquement le besoin en français naturel
- **JARVIS_Maître** : Traduit en tâches et délègue aux agents spécialisés
- **Prompts inter-agents** : Créés automatiquement par l'orchestration

## Phase 2 : Plan → Documentation
**Confirmé** : TerraNova (plan.md), UFM (README), JARVIS 2.0 (docs/)

3. **Création du plan**
   - Décomposer projet en modules
   - Définir priorités et dépendances
   - Créer checklist de validation
   - **Générer documentation AVANT code** (plan.md, README.md)

4. **Structure documentation**
   - `docs/reference/` : Documents validés (source de vérité)
   - `docs/work/` : Documents en cours
   - `docs/history/` : Archive lecture seule
   - `docs/_meta/` : Index, changelog

## Phase 3 : Génération Code
**Confirmé** : JARVIS 2.0, TerraNova, UFM, PaperClip2

5. **Génération code (orchestrée par JARVIS)**
   - **JARVIS_Maître** : Crée les prompts pour agents spécialisés
   - **CODEUR** : Génère code par blocs fonctionnels
   - **BASE** : Vérifie structures (front/back/base/auth)
   - **Centralisation constantes** : Pas de valeurs magiques
   - **Keamder** : Valide les étapes, pas de création de prompts

6. **Scripts d'automatisation**
   - Scripts npm : `dev`, `build`, `test`, `deploy`, `db:*`
   - Scripts Python : migrations, seed, vérification
   - Scripts PowerShell : build, clean, migrate

## Phase 4 : Tests
**Confirmé** : Tous projets (manuel) + JARVIS 2.0 (automatisé 99%)

7. **Test technique**
   - Lancer le projet
   - Vérifier connectivité et cohérence données
   - Tester fonctionnalités principales
   - Vérifier logs structurés

8. **Test réel via interface**
   - Interaction utilisateur réelle
   - Collecte logs structurés
   - Validation comportement attendu
   - **Observable et vérifiable** (interface + logs)

## Phase 5 : Amélioration Itérative
**Confirmé** : Tous projets (corrections progressives documentées)

9. **Corrections progressives**
   - Identifier incohérences (préfixes IDs, nomenclature)
   - Audit post-développement (TerraNova, UFM)
   - Harmonisation (centralisation, conventions)
   - Documentation des corrections

10. **Nouvelles fonctionnalités**
    - Ajouter selon priorités
    - Reprendre tests et validations
    - Mettre à jour documentation et architecture
    - Versioning sémantique (v1.0.0, v2.1)

---

# 3. GESTION DES PROJETS

## Projets Simultanés
- **Maximum 2–3 projets actifs** simultanément
- Maintenir historique clair : ancien projet / projet courant / idées futures
- Définir jalons et points de validation intermédiaires

## Organisation Confirmée (Multi-projets)

### Structure Monorepo (UFM, JARVIS 2.0)
```
projet/
├── frontend/     # SPA (Angular, Flutter)
├── backend/      # API (Express, FastAPI)
├── shared/       # Code partagé
└── docs/         # Documentation structurée
```

### Gestion Versions
- **Versioning sémantique** : v1.0.0, v2.1, v1.17
- **Commits Git fréquents** : descriptifs (ex: "Final version 1.17")
- **Branches** : main/master, develop (UFM)
- **Statut production** : Marquage explicite ( En production)

### Scripts Automatisation (Confirmé 3+ projets)
- **npm scripts** : dev, build, test, deploy, db:migrate, db:seed
- **Python scripts** : migrations, seed, vérification
- **PowerShell** : build.ps1, clean-build.ps1, migrate-and-start.bat

---

# 4. DOCUMENTATION (CONFIRMÉE MULTI-PROJETS)

## Formats Utilisés
- **Markdown** : README.md, plan.md, guides techniques
- **Schémas** : Architecture, bases de données
- **Notes Notion** : Idées personnelles (non liées projets)
- **Logs structurés** : Clairs et centralisés

## Pratiques Documentaires (Confirmées)

### Documentation Exhaustive (5 projets)
- **Plans détaillés** : plan.md (113 lignes TerraNova), README.md
- **Documentation structurée** : reference/work/history/_meta
- **Historique corrections** : Changements documentés
- **Checklist validation** : Missions, tests, déploiement

### Problème Récurrent (3 projets)
- **Divergence doc/code** : Documentation obsolète
- **Besoin mises à jour régulières** : Risque désynchronisation
- **Solution** : Audit post-développement, harmonisation

## Patterns Architecturaux Récurrents

### 1. Architecture en Couches (4 projets)
```
UI / Presentation
    ↓
Services / Business Logic
    ↓
Data / Persistence
```

### 2. Séparation Frontend/Backend (3 projets)
- Frontend SPA (Angular, Flutter)
- Backend API REST (Express, FastAPI, Firebase Functions)
- Communication HTTP/JSON

### 3. Centralisation Constantes (2 projets)
- Fichier unique (constantes.dart, library_seed.json)
- Aucune valeur magique dans le code
- Classes statiques (AppStrings, AppIds, ResourceKeys)

### 4. Architecture Multi-Agent (1 projet majeur)
- Agent orchestrateur (JARVIS_Maître)
- Agents spécialisés (CODEUR, BASE, VALIDATEUR)
- Délégation via marqueurs textuels
- Protections anti-boucle (max 3 iterations, timeout 30s)

---

# 5. PRATIQUES RÉELLES (BASÉES SUR 9 PROJETS)

## A. Pratiques Appliquées Consciemment

### 1. Documentation Systématique (5+ projets)
- **plan.md** : Plan détaillé projet (TerraNova : 113 lignes)
- **README.md** : Instructions lancement + architecture
- **docs/ structuré** : reference/work/history/_meta (JARVIS 2.0)
- **Commits Git descriptifs** : "Final version 1.17", "Fix admin UUID"

### 2. Tests Manuels Rigoureux (Tous projets)
- **Interface réelle** : Teste toujours via navigateur/app
- **Logs structurés** : Vérifie logs backend systématiquement
- **Observable et vérifiable** : "Je dois VOIR que ça marche"
- **Itérations** : Corrections jusqu'à succès

### 3. Versioning Sémantique (Tous projets)
- **v1.0.0, v2.1, v1.17** : Numérotation claire
- **Commits fréquents** : Sauvegarde régulière
- **Branches** : main/master, develop (UFM)

### 4. Gestion Projets (Confirmée)
- **Maximum 2-3 projets actifs** : Limite respectée
- **Historique clair** : Ancien / courant / idées futures
- **Jalons validation** : Points de contrôle définis

## B. Pratiques Générées par IA (Non Maîtrisées)

### 1. Tests Automatisés
- **JARVIS 2.0** : 99% tests (seul projet avec tests auto)
- **Autres projets** : 0% tests automatisés
- **Réalité** : L'IA génère tests si demandé, pas appliqué systématiquement

### 2. Linting/Formatting
- **ESLint, Prettier, Ruff** : Configurés par IA
- **Réalité** : Pas appliqué consciemment, code généré déjà formaté

### 3. Type Safety
- **TypeScript, Dart** : Code généré typé par IA
- **Réalité** : Pas de choix conscient de typage, généré automatiquement

### 4. Sécurité
- **JWT RS256, CORS, Helmet.js** : Configurés par IA
- **Réalité** : Tu cherches infos services, IA configure, tu testes

### 5. DevOps
- **Déploiement Vercel, Play Store** : Guidé par IA
- **Scripts vérification** : Générés par IA (postdeploy-check.js)
- **Réalité** : Tu suis instructions, IA génère config

---

# 6. GESTION DES ÉCHECS ET DEBUGGING

## Workflow Debugging (Confirmé Multi-Projets)

### 1. Quand Code Ne Fonctionne Pas

**Étape 1 : Collecte Informations**
- Copier message d'erreur complet
- Vérifier logs backend (terminal)
- Vérifier console navigateur (F12)
- Noter ce qui était attendu vs ce qui se passe

**Étape 2 : Demande Aide IA**
```
"J'ai cette erreur : [message d'erreur]

Ce que je faisais : [action]
Ce qui devait se passer : [comportement attendu]
Ce qui se passe : [comportement réel]

Logs backend : [logs]"
```

**Étape 3 : IA Explique et Corrige**
- IA explique cause en français clair
- IA propose correction
- IA génère code corrigé

**Étape 4 : Test Correction**
- Relancer projet
- Retester fonctionnalité
- Vérifier logs

### 2. Nombre d'Itérations

**Règle observée** :
- **1-3 itérations** : Problème simple (typo, config)
- **4-10 itérations** : Problème complexe (architecture, auth)
- **10+ itérations** : Revoir architecture ou demander aide externe

**Critère abandon** :
- Si après 10 itérations aucun progrès → Revoir approche
- Si IA propose toujours même solution → Changer IA ou chercher forum

### 3. Sources Aide Externe

**Quand demander aide externe** :
- Erreur incompréhensible après 10 itérations
- IA ne trouve pas solution
- Problème spécifique service (Supabase, Vercel)

**Sources utilisées** :
- **Documentation officielle** : Supabase, Firebase, Vercel
- **Forums** : Stack Overflow, Reddit
- **Autre IA** : Changer d'IA si bloqué (Windsurf, ChatGPT, Claude)

### 4. Problèmes Récurrents et Solutions

**Problème 1 : Configuration .env**
- **Symptôme** : Variables undefined, erreurs connexion
- **Solution** : Vérifier .env existe, variables correctes, redémarrer serveur

**Problème 2 : CORS**
- **Symptôme** : Erreur "blocked by CORS policy"
- **Solution** : Vérifier origines autorisées backend, localhost:port correct

**Problème 3 : Auth 401/403**
- **Symptôme** : Unauthorized, Forbidden
- **Solution** : Vérifier clé API, token valide, permissions Supabase/Firebase

**Problème 4 : Migrations BDD**
- **Symptôme** : Erreurs SQL, données manquantes
- **Solution** : Scripts correctifs générés par IA, backup avant migration

---

# 7. STACK NORMALISÉE PRÉFÉRÉE

## Stack par Défaut (Sauf besoin spécifique)

### Backend
- **Langage** : Python 3.11+
- **Framework** : FastAPI
- **Base de données** : SQLite (dev/local) ou PostgreSQL via Supabase (production)
- **ORM** : Prisma (si Node.js) ou SQLAlchemy (si Python)
- **Tests** : Pytest
- **Linting** : Ruff

### Frontend
- **Simple** : HTML5/CSS3/JavaScript vanilla
- **Complexe** : Angular 17+ (si besoin SPA avancé)
- **Mobile** : Flutter/Dart (multi-plateforme)

### Services Cloud (Gratuit/Low-cost)
- **Déploiement** : Vercel (web) ou GitHub Pages (statique)
- **Auth** : Supabase Auth (JWT RS256)
- **Stockage images** : Cloudinary
- **IA/LLM** : Google Gemini API (Tier 1 gratuit)

### DevOps
- **Versioning** : Git/GitHub
- **CI/CD** : Vercel (automatique)
- **Conteneurs** : Docker Compose (dev local)

**Principe** : Privilégier cette stack sauf si besoin technique justifié

---

# 7. TEMPS & SESSIONS

**Temps disponible** : 2h à 35h+/semaine
**Sessions de travail** : 2h à 8h
**Période privilégiée** : Soir
**Projets simultanés** : 2-3 actifs + anciens + idées futures