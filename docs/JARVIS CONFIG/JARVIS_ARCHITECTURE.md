# JARVIS_ARCHITECTURE.md
Architecture et organisation des agents — JARVIS 2.0

---

# 1. AGENT MAÎTRE

Nom : **JARVIS_Maître**  
Modèle : **gemini-2.0-flash** (Tier 1 Gemini)  
Configuration : Temperature 0.3, Max tokens 4096, **0 functions**

Rôle :

- **Orchestrateur des agents** (délégation via marqueurs textuels)
- **Mémoire centrale des projets** (historique, décisions)
- **Interface principale avec Keamder** (langage naturel français)
- **Superviseur de génération et tests** (validation étapes)
- **Décideur sur priorités et flux de travail** (audit → plan → exécution)

**IMPORTANT** : 0 functions (les functions empêchent la délégation)

Délégation via marqueurs :
- `[DEMANDE_CODE_CODEUR: ...]` : Délégation génération code
- `[DEMANDE_VALIDATION_BASE: ...]` : Délégation validation complétude

---

# 2. ÉQUIPE D'AGENTS SPÉCIALISÉS (4 AGENTS IMPLÉMENTÉS)

## 1. CODEUR
**Modèle** : gemini-2.5-pro (Tier 1 Gemini)  
**Configuration** : Temperature 0.3, Max tokens 4096, 2 functions  
**Rôle** : Génération de code uniquement

**Responsabilités** :
- Génération code frontend (Angular, Flutter, HTML/CSS/JS)
- Génération code backend (Python FastAPI, Express.js)
- Fichiers complets et autonomes
- Imports absolus simples
- Pas de commentaires sauf si demandé

**Règles absolues** :
- Pydantic v2 API (model_dump, model_validate, model_copy)
- Storage JSON avec __init__, save(), load()
- Cohérence imports et dépendances
- Pas de tests pour fonctionnalités non implémentées

## 2. BASE (Worker polyvalent)
**Modèle** : gemini-2.0-flash-lite (Tier 1 Gemini)  
**Configuration** : Temperature 0.7, Max tokens 4096, 4 functions  
**Rôle** : Validation, vérification complétude, rapports

**Functions disponibles** :
- `get_project_file` : Lire fichiers projet
- `get_project_structure` : Structure arborescence
- `get_library_document` : Accès documents library
- `get_library_list` : Liste documents disponibles

**Responsabilités** :
- Vérification complétude code généré
- Validation présence fichiers attendus
- Rapports d'état (COMPLET / INCOMPLET)
- Analyse erreurs et logs

## 3. VALIDATEUR (Contrôle qualité) - 📋 PRÉVU, NON IMPLÉMENTÉ
**Modèle prévu** : gemini-3.1-pro-preview (Tier 1 Gemini)  
**Configuration prévue** : Temperature 0.5, Max tokens 4096, 0 functions  
**Rôle prévu** : Détection bugs, tests, qualité

**Responsabilités prévues** :
- Détection bugs et erreurs
- Vérification qualité code
- Suggérer améliorations
- Validation tests

**Statut** : 📋 Planifié, pas encore développé

## 4. Agents Futurs (Planifiés, non implémentés)
- **Agent Tests** : Tests automatisés E2E
- **Agent Documentation** : Génération markdown/schémas
- **Agent Mémoire** : Archivage projets
- **Agent Frontend** : Spécialisé UI
- **Agent Backend** : Spécialisé API

---

# 3. STACK & SERVICES (CONFIRMÉS MULTI-PROJETS)

## Stack Backend Python
**Utilisée par** : JARVIS 2.0, RAG, frisbee-teams
- Python 3.11+
- FastAPI (framework principal JARVIS)
- Flask (RAG)
- SQLite + aiosqlite (JARVIS)
- Pytest (tests 99%)
- Uvicorn (serveur ASGI)

## Stack Backend Node.js
**Utilisée par** : Ultimate Frisbee Manager, PaperClip2
- Node.js 20
- Express.js
- Prisma ORM (migrations, schéma)
- PostgreSQL (via Supabase)
- Firebase Functions v2 (PaperClip2)

## Stack Frontend
**Utilisée par** : UFM, Portfolio, Atelier, TerraNova, PaperClip2
- Angular 17-19 (UFM)
- Flutter/Dart (TerraNova, PaperClip2)
- HTML5/CSS3/JavaScript vanilla (Portfolio, Atelier, Wix)
- TypeScript (UFM, JARVIS)

## Stack IA/ML
**Utilisée par** : JARVIS 2.0, RAG
- **Google Gemini API** (Tier 1 gratuit)
  - gemini-2.0-flash (JARVIS_Maître)
  - gemini-2.5-pro (CODEUR)
  - gemini-2.0-flash-lite (BASE)
  - gemini-3.1-pro-preview (VALIDATEUR)
- Transformers / LangChain (RAG)
- ChromaDB + FAISS (RAG)
- PyTorch 2.2.0 avec ROCm 5.7 (RAG)

## Services Cloud Confirmés
**Fréquemment utilisés** :
- **Vercel** : Déploiement production (UFM)
- **Supabase** : Auth JWT RS256 + PostgreSQL (UFM)
- **Firebase** : Functions v2 + Auth + Firestore (PaperClip2)
- **Cloudinary** : Stockage images (UFM)
- **Google Play Store** : Publication mobile (PaperClip2)
- **GitHub Pages** : Sites statiques (Portfolio, Atelier)

**Objectif** : Solutions **gratuites ou low-cost**

## Communication Entre Agents
- **Mémoire centrale** : Base de données SQLite (JARVIS 2.0)
- **Prompts orchestrés** : JARVIS_Maître délègue via marqueurs
- **Function executor** : Permet aux agents délégués d'utiliser functions
- **Protections anti-boucle** : Max 3 iterations, timeout 30s

---

# 4. PRINCIPES

- Chaque agent a un rôle unique et clairement défini
- Les agents ne prennent aucune décision en dehors du workflow
- Toutes les modifications sont tracées
- L’agent maître supervise et valide toutes les actions

---

# 5. FLUX DE TRAVAIL (CONFIRMÉ JARVIS 2.0)

## Workflow Standard

1. **Keamder exprime besoin** en langage naturel français
2. **JARVIS_Maître analyse** et décompose en tâches
3. **JARVIS_Maître crée plan** (audit → plan → validation)
4. **Keamder valide plan** (validation explicite requise)
5. **JARVIS_Maître délègue** via marqueurs :
   - `[DEMANDE_CODE_CODEUR: ...]` → Génération code
   - `[DEMANDE_VALIDATION_BASE: ...]` → Vérification
6. **Agent délégué exécute** (CODEUR ou BASE)
7. **Orchestration backend** traite réponse agent
8. **Génération code sur disque** (fichiers créés)
9. **Retour à Keamder** avec résultat et documentation

## Protections Implémentées

**Anti-boucle** :
- Max 3 iterations function calling
- Timeout 30s par function call
- Compteur par function (max 2 appels)

**Gestion quotas API** :
- Configuration Tier 1 Gemini validée
- Quotas séparés par agent (6175 RPM cumulés)
- RPD illimité pour JARVIS_Maître et BASE

## Tests Confirmés
- **238/241 tests passent** (99%) - Tests backend uniquement
- Tests unitaires agents (BASE, JARVIS_Maître)
- Tests orchestration
- Tests live (calculatrice, TODO, MiniBlog)

**Note** : Tests fonctionnels mais JARVIS pas encore utilisé quotidiennement (en paramétrage)

---

# 6. CONFIGURATION TECHNIQUE

## Gemini Tier 1 (Gratuit)

| Agent | Modèle | RPM | TPM | RPD |
|-------|---------|-----|-----|-----|
| JARVIS_Maître | gemini-2.0-flash | 2K | 4M | Illimité |
| CODEUR | gemini-2.5-pro | 150 | 2M | 1K |
| BASE | gemini-2.0-flash-lite | 4K | 4M | Illimité |
| VALIDATEUR | gemini-3.1-pro-preview | 25 | 5M | 255 |

**Avantages** :
- ✅ Quotas séparés (6175 RPM cumulés)
- ✅ RPD illimité pour orchestrateur et worker
- ✅ Qualité maximale pour CODEUR (Pro)
- ✅ 100% gratuit

## Backend### 1. JARVIS 2.0 🔄 EN COURS DE PARAMÉTRAGE
- **Type** : Assistant IA multi-agent pour génération de code
- **Technologies** : Python 3.11, FastAPI, Google Gemini API, SQLite
- **Statut** : v2.1 (22 février 2026) - **EN PARAMÉTRAGE, PAS ENCORE UTILISABLE QUOTIDIENNEMENT**
- **Tests** : 238/241 (99%) - Tests backend fonctionnels
- **Objectif** : Remplacer Windsurf comme assistant principal
- **Caractéristiques** : 3 agents implémentés (JARVIS_Maître, CODEUR, BASE), génération code sur disque, protections anti-boucle

---

# 7. STATUT ACTUEL ET ROADMAP

## Statut : 🔄 EN COURS DE PARAMÉTRAGE

**Version** : v2.1 (22 février 2026)
**Objectif** : Remplacer Windsurf comme assistant principal

### ✅ Ce Qui Fonctionne

**Backend (99% tests)** :
- ✅ Orchestration JARVIS_Maître → CODEUR/BASE
- ✅ Délégation via marqueurs textuels
- ✅ Génération code sur disque
- ✅ Protections anti-boucle
- ✅ Base SQLite + Library documents

### 🔄 En Cours

- 🔄 Intégration 5 documents CONFIG dans Library
- 🔄 Tests interface complète

### 📋 Ce Qui Manque

- 📋 Agent VALIDATEUR
- 📋 Tests live avancés (auth, frontend, mobile)
- 📋 Documentation utilisateur

## Ce Qui Bloque l'Utilisation Quotidienne

1. **Personnalisation incomplète** : JARVIS ne connaît pas encore ton profil
2. **Tests interface incomplets** : Frontend web pas complètement testé
3. **Documentation manquante** : Pas de guide "Comment utiliser JARVIS"

## Prochaines Étapes

1. Intégrer 5 documents CONFIG dans Library
2. Tester interface web complète
3. Créer premier projet réel avec JARVIS
4. Remplacer Windsurf par JARVIS