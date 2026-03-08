# KEAMDER_PROFILE.md

Profil développeur — Base de connaissance personnelle

---

# 1. IDENTITÉ & CONTEXTE

**Nom utilisé par l'assistant** : Keamder
**Pays** : France
**Fuseau horaire** : Europe (France)

## Langues

Français

* langue native
* utilisée pour tous les contextes

Anglais

* niveau très basique
* lecture partielle de documentation technique

Langage technique informatique

* niveau débutant
* dépendance à l’IA pour traduire les besoins fonctionnels en architecture technique

## Mode de communication technique

Keamder exprime ses besoins en **langage naturel français**.

Le rôle de l’IA est de :

1. comprendre le besoin fonctionnel
2. traduire en architecture technique
3. proposer la stack adaptée
4. générer le code
5. permettre un test réel via interface

Exemple de traduction attendue :

Besoin exprimé :

> "Je veux un site avec des comptes utilisateurs et des données"

Traduction technique attendue :

* frontend dynamique
* backend API
* base de données
* authentification
* logique métier

---

# 2. SITUATION PROFESSIONNELLE

Statut actuel :

* salarié
* micro-entrepreneur

## Micro-entreprise

Activité :

* prestation de service
* développement d’outils numériques simples
* accompagnement des petites structures

Projet en développement :

**L’Atelier Connecté**

Objectif :

* proposer des solutions numériques simples
* aider les petites organisations locales
* résoudre des problèmes d’organisation ou d’informatique
* créer des outils sur mesure

---

# 3. PARCOURS

Historique professionnel principal :

* secteur social
* profil polyvalent / "couteau suisse"

Parcours technique :

* autodidacte
* apprentissage par projets
* apprentissage via IA

Durée de pratique :

≈ 2 ans de développement **no-code assisté par IA**

---

# 4. POSITIONNEMENT TECHNIQUE

Niveau global :

**Pilote de projet assisté par IA à 100%**

Caractéristiques :

* **0% de production de code autonome** : Ne code JAMAIS sans IA
* **100% de dépendance à l'IA** pour toute génération de code
* **Forte capacité de conception produit** : Vision claire du besoin utilisateur
* **Bonne compréhension conceptuelle** de l'architecture logicielle
* **Capacité à piloter un projet technique** via IA (workflow structuré)

**Rôle réel** :
- Chef de projet technique (définit besoin, valide architecture)
- Testeur (interface réelle + logs)
- PAS développeur (ne produit pas de code)

---

# 5. COMPÉTENCES TECHNIQUES

## Frontend

**Technologies de projets pilotés via IA** (multi-projets) :

* **HTML5/CSS3/JavaScript vanilla** : Portfolio, Atelier Connecté, 9 sites Wix
* **Angular 17-19** : Ultimate Frisbee Manager (production)
* **Angular Material** : UFM (composants UI)
* **RxJS** : UFM (gestion état réactive)
* **TypeScript** : UFM, JARVIS 2.0
* **Flutter/Dart** : TerraNova, PaperClip2 (publié Play Store)
* **Streamlit** : frisbee-teams (interface Python)

**Niveau réel** :

* **Compréhension conceptuelle** : Architecture frontend, patterns, composants
* **Production** : 100% générée par IA, 0% autonome
* **Validation** : Tests via interface réelle, logs
* **Choix technologiques** : Souvent proposés par IA, validés sans expertise technique approfondie

---

## Backend

**Technologies de projets pilotés via IA** (multi-projets) :

* **Python 3.11+** : JARVIS 2.0, RAG, frisbee-teams
* **FastAPI** : JARVIS 2.0 (framework principal)
* **Flask** : RAG
* **Express.js** : UFM, PaperClip2 (choix IA, non réfléchi)
* **Node.js 20** : UFM, PaperClip2 (choix IA, non réfléchi)
* **Firebase Functions v2** : PaperClip2 (production)

**Niveau** :

* **Compréhension conceptuelle** : Architecture API REST, patterns
* **Production** : 100% générée par IA, 0% autonome
* **Validation** : Tests manuels via interface + logs
* **Choix stack** : Souvent proposés par IA sans réflexion technique approfondie (ex: UFM en Node.js au lieu de Python)

---

## Bases de données

**Technologies confirmées** (multi-projets) :

* **SQLite** : JARVIS 2.0 (aiosqlite)
* **PostgreSQL** : UFM (via Supabase)
* **Prisma ORM** : UFM (migrations, schéma)
* **Cloud Firestore** : PaperClip2
* **ChromaDB + FAISS** : RAG (bases vectorielles)

**Capacités** :

* Compréhension schémas relationnels et NoSQL
* Création de modèles de données
* Migrations (avec scripts correctifs)
* Manipulation guidée par IA

---

## Authentification

**Systèmes de projets pilotés** (multi-projets) :

* **Supabase Auth** : UFM (JWT RS256)
* **Firebase Auth** : PaperClip2 (ID Token)
* **Google OAuth** : PaperClip2, UFM
* **JWT** : UFM, PaperClip2
* **Session management** : Tous projets

**Rôle réel** :

* **Recherche d'informations** : Tu cherches clés API, URLs, documentation services
* **Configuration par IA** : L'IA génère le code d'authentification
* **Validation par tests** : Tu testes via interface réelle (connexion, déconnexion)
* **Debugging assisté** : L'IA t'aide à interpréter erreurs 401, 403, etc.

---

## IA & Machine Learning

**Projets pilotés utilisant ces technologies** (2 projets) :

* **Google Gemini API** : JARVIS 2.0 (Tier 1 : gemini-2.0-flash, gemini-2.5-pro, gemini-3.1-pro)
* **Transformers (Hugging Face)** : RAG
* **Sentence Transformers** : RAG (embeddings)
* **PyTorch 2.2.0** : RAG (avec ROCm 5.7 pour GPU AMD)
* **LangChain** : RAG
* **ChromaDB + FAISS** : RAG (recherche vectorielle)

**Rôle réel** :

* **Conception architecture** : Vision claire du système multi-agents ou RAG
* **Configuration via IA** : L'IA génère intégrations APIs, embeddings, etc.
* **Tests fonctionnels** : Validation via interface et logs
* **Optimisation guidée** : L'IA propose optimisations quotas, tu valides

---

# 6. APPLICATIONS RÉALISÉES

## Projets Confirmés (9 projets analysés)

### 1. JARVIS 2.0 OPÉRATIONNEL
- **Type** : Assistant IA multi-agent pour génération de code
- **Technologies** : Python 3.11, FastAPI, Google Gemini API, SQLite
- **Statut** : v2.1 (22 février 2026)
- **Tests** : 238/241 (99%)
- **Caractéristiques** : 4 agents spécialisés, génération code sur disque, protections anti-boucle

### 2. Ultimate Frisbee Manager PRODUCTION
- **Type** : Application web SaaS full-stack
- **Technologies** : Angular 17-19, Express.js, Prisma, PostgreSQL, Supabase, Cloudinary
- **Statut** : Production sur Vercel
- **URL** : https://ultimate-frisbee-manager.vercel.app
- **Caractéristiques** : Auth complète, workspaces, upload images, tests E2E

### 3. PaperClip2 (ClipFactory Empire) PUBLIÉ
- **Type** : Jeu mobile idle/clicker
- **Technologies** : Flutter, Firebase Functions v2, Cloud Firestore, Firebase Auth
- **Statut** : Publié sur Google Play Store
- **Package** : com.kinder2149.paperclip2
- **Fonctionnalités** : Offline, Google login, sync cloud, 10 mondes/utilisateur

### 4. TerraNova EN DÉVELOPPEMENT
- **Type** : Jeu mobile city-builder
- **Technologies** : Flutter/Dart pur (multi-plateforme)
- **Statut** : v1.1 en développement
- **Caractéristiques** : 15 bâtiments, 10 ressources, système XP, architecture en couches

### 5. Frisbee Teams Manager FONCTIONNEL
- **Type** : Application data science
- **Technologies** : Python, Streamlit, Pandas, Matplotlib
- **Objectif** : Répartition équilibrée joueurs en équipes
- **Caractéristiques** : Algorithme serpentin, export Excel, visualisations

### 6. L'Atelier Connecté PRÊT DÉPLOIEMENT
- **Type** : Site vitrine professionnel (micro-entreprise)
- **Technologies** : HTML5, CSS3, JavaScript vanilla, EmailJS
- **Statut** : Prêt pour GitHub Pages
- **Objectif** : Accompagnement numérique PME/associations

### 7. Portfolio Personnel DÉPLOYÉ
- **Type** : Site portfolio
- **Technologies** : HTML5, CSS3, JavaScript vanilla
- **Statut** : Déployé (20+ versions Git)
- **Caractéristiques** : Carrousel dynamique, glassmorphism, responsive

### 8. Système RAG EN DÉVELOPPEMENT
- **Type** : Backend IA recherche sémantique
- **Technologies** : Python, Flask, PyTorch, ChromaDB, FAISS, LangChain
- **Objectif** : Indexation et recherche documentaire pour agents IA

### 9. Projets Wix (9 sites)
- L'atelier connecté, La légende du Graoully, Make it better, Enquête Multivers, Escape Mythology, Formation BAFA, Jeux Olympique
- **E-commerce Shopify** : OPPI, Subteal (missions professionnelles)

---

# 7. STACKS RÉCURRENTES

## Stack Python Backend
**Utilisée dans** : JARVIS 2.0, RAG, frisbee-teams
- Python 3.11+
- FastAPI ou Flask
- Pytest pour tests
- python-dotenv pour configuration
- Logging structuré

## Stack Node.js Full-Stack
**Utilisée dans** : Ultimate Frisbee Manager
- Node.js 20
- Express.js
- Prisma ORM
- PostgreSQL
- Angular (frontend)
- TypeScript
- Déploiement Vercel

## Stack Flutter Mobile
**Utilisée dans** : TerraNova, PaperClip2
- Flutter/Dart
- Firebase (Functions, Auth, Firestore) ou architecture pure
- Multi-plateforme (Android, iOS, Web, Desktop)

## Stack IA/LLM
**Utilisée dans** : JARVIS 2.0, RAG
- Google Gemini API
- Transformers / LangChain
- Embeddings vectoriels
- ChromaDB / FAISS

## Services Cloud Confirmés

**Fréquemment utilisés** :
* **Vercel** : Déploiement production (UFM)
* **Supabase** : Auth + PostgreSQL (UFM)
* **Firebase** : Functions + Auth + Firestore (PaperClip2)
* **Cloudinary** : Stockage images (UFM)
* **Google Play Store** : Publication mobile (PaperClip2)
* **GitHub Pages** : Sites statiques (Portfolio, Atelier)

**Objectif constant** : Solutions **gratuites ou low-cost**

---

# 18. DIFFICULTÉS RÉCURRENTES (RÉALITÉ D'UN PILOTE DE PROJET IA)

## A. Difficultés Pilotage IA (PRINCIPALES)

### 1. Communication avec l'IA
- **Expliquer clairement le besoin** en langage naturel
- **Traduire vision produit** en spécifications techniques compréhensibles
- **Itérer sur les prompts** jusqu'à obtenir le résultat voulu
- **Détecter quand l'IA n'a pas compris** le besoin réel

### 2. Compréhension du Code Généré
- **Lire et comprendre** le code produit par l'IA
- **Identifier si le code est bon** ou contient des erreurs
- **Savoir quoi tester** pour valider le code
- **Comprendre les messages d'erreur** techniques

### 3. Maintien de la Cohérence
- **Perte de contexte** entre sessions IA (mémoire limitée)
- **Incohérences** entre code généré à différents moments
- **Divergence documentation/code** (doc obsolète)
- **Nomenclature incohérente** (Monde/World/Partie)

### 4. Choix Technologiques
- **Accepter propositions IA** sans réflexion technique (ex: UFM en Node.js)
- **Choisir technologies adaptées** au besoin réel
- **Normaliser la stack** pour éviter dispersion
- **Justifier techniquement** les choix

### 5. Gestion Complexité Projet
- **Over-engineering** : IA propose trop complexe (9 agents prévus)
- **Scope creep** : Fonctionnalités ajoutées sans plan
- **Structuration projet** : Maintenir organisation claire

## B. Difficultés Techniques (SECONDAIRES, car IA code)

Ces difficultés existent mais sont **gérées par l'IA** :

### 1. Configuration Environnement
- Multiples `.env` (local, production, preview)
- Variables complexes (auth, CORS, API keys)
- **Résolution** : IA génère scripts de vérification

### 2. Migrations Base de Données
- Scripts correctifs (`safe-migrate-vercel.js`)
- Perte données production (UFM - incident 2026-02-20)
- **Résolution** : IA génère scripts, je teste

### 3. Authentification
- JWT RS256 complexe (Supabase, Firebase)
- **Résolution** : IA configure, je valide via tests interface

### 4. Déploiement Production
- Vercel, CORS, scripts post-déploiement
- **Résolution** : IA génère config, je déploie et teste

### 5. Tests Incomplets
- Coverage inégale (99% JARVIS vs 0% autres)
- Tests E2E configurés mais non utilisés
- **Résolution** : Tests manuels via interface réelle

## C. Difficultés Organisationnelles

### 1. Workflow
- **Appliquer workflow structuré** systématiquement
- **Maintenir documentation** à jour (plan.md, README)
- **Versioning sémantique** et commits descriptifs

### 2. Gestion Projets
- **Maximum 2-3 projets actifs** : Respecter la limite
- **Historique clair** : Ancien / courant / idées futures
- **Jalons et validation** : Points de contrôle définis

---

# 19. FORCES RÉELLES (CONFIRMÉES MULTI-PROJETS)

## Points Forts Avérés

### 1. Vision Produit Claire
- **9 projets réalisés** dont 3 en production
- **Capacité à imaginer** écrans, flux utilisateur, fonctionnalités
- **Compréhension besoins** utilisateurs finaux

### 2. Workflow Structuré et Rigoureux
- **Documentation systématique** : plan.md, README.md (5+ projets)
- **Organisation claire** : docs/reference/work/history/_meta
- **Versioning sémantique** : v1.0.0, v2.1, commits descriptifs

### 3. Persévérance et Itérations
- **Corrections progressives** documentées (tous projets)
- **Audits post-développement** (TerraNova, UFM)
- **Itérations jusqu'à succès** : Ne lâche pas avant que ça marche

### 4. Tests Manuels Rigoureux
- **Interface réelle** : Teste toujours via navigateur/app
- **Logs structurés** : Vérifie logs backend systématiquement
- **Observable et vérifiable** : "Je dois VOIR que ça marche"

### 5. Capacité d'Apprentissage
- **2 ans d'expérience** : Autodidacte complet
- **9 projets variés** : Web, mobile, IA, data science
- **Adaptation rapide** : Nouvelles technos selon besoins

## Points Faibles Assumés

### 1. Production Code Autonome
- **0% autonomie** : Ne code jamais sans IA
- **Dépendance totale** à l'IA pour génération

### 2. Compréhension Technique Approfondie
- **Concepts complexes** : JWT, CORS, migrations BDD (difficultés)
- **Choix technologiques** : Parfois non réfléchis (UFM en Node.js)

### 3. Tests Automatisés
- **0% tests auto** sauf JARVIS (99%)
- **Pas de TDD** : Tests manuels uniquement

### 4. Bonnes Pratiques Code
- **Linting/Formatting** : Configuré par IA, pas appliqué consciemment
- **Type safety** : Code généré par IA, pas choix conscient

---

# 20. OBJECTIF PRINCIPAL

Construire des outils numériques utiles pour :

* soi-même
* petites structures
* organisations locales

---

# 20. PROJET CENTRAL : JARVIS

JARVIS est un assistant personnel multi-agents.

## Architecture conceptuelle

Agent maître :

JARVIS

Équipe d’agents spécialisés :

* agents techniques
* agents d’analyse
* agents d’exécution

---

## Rôle de JARVIS

1. assistant développement
2. orchestrateur d’IA
3. mémoire des projets
4. assistant personnel
5. copilote stratégique

---

## Objectif principal

Remplacer l'utilisation actuelle de Windsurf et devenir :

un **assistant personnel complet** inspiré de l'assistant de Tony Stark.

---

# 21. INFRASTRUCTURE FUTURE

Projet :

mettre en place un **serveur personnel** sur un second ordinateur.

Objectif :

* héberger des services
* expérimenter des architectures
* gagner en autonomie technique.

---

# 22. MODE D’INTERACTION IDÉAL AVEC UNE IA

Une IA efficace pour Keamder doit :

1. traduire les besoins fonctionnels
2. proposer une architecture claire
3. générer du code propre
4. fournir les commandes exactes
5. structurer les logs
6. maintenir la mémoire des décisions techniques
7. séparer clairement :

* phase réflexion
* phase implémentation

---

# 23. PROFIL SYNTHÉTIQUE

Type de profil :

**Product builder assisté par IA**

Forces :

* créativité produit
* vision d’usage
* capacité d’apprentissage rapide
* expérimentation

Faiblesses techniques :

* syntaxe code
* architecture avancée
* organisation technique long terme

Positionnement :

**Concepteur d’outils numériques pilotant le développement via IA.**
