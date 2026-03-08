# KEAMDER_DEV_RULES.md
Règles d’orchestration pour les IA — Keamder / JARVIS

---

# 1. OBJECTIF

Garantir que toutes les IA travaillent de manière cohérente avec Keamder et le workflow établi.

**CONTEXTE CRITIQUE** : Keamder est un **pilote de projet assisté par IA à 100%**, PAS un développeur.
- **0% de production de code autonome** : Ne code JAMAIS sans IA
- **100% de dépendance à l'IA** pour toute génération de code
- **Forte capacité de conception produit** mais compréhension technique limitée

**Conséquence** : L'IA doit adapter sa communication et ses explications en conséquence.

---

# 2. PRINCIPES GÉNÉRAUX (CONFIRMÉS MULTI-PROJETS)

## Règles Absolues
- **Ne jamais inventer des informations** (basé sur preuves uniquement)
- **Ne générer que ce qui est demandé** ou validé par l'architecture
- **Toujours structurer les réponses et logs** (clairs, centralisés)
- **Respecter les phases** : réflexion / implémentation / test / documentation
- **Maintenir mémoire et historique complet** des projets

## Principes Techniques (JARVIS 2.0)

### Règle 1 : Storage JSON
Une classe Storage doit TOUJOURS avoir :
1. Constructeur `__init__(self, filepath: str)`
2. Méthode `save(self, data)` pour écrire
3. Méthode `load(self) -> data` pour lire

### Règle 2 : Pydantic v2
Utiliser TOUJOURS l'API Pydantic v2 :
- `.model_dump()` au lieu de `.dict()`
- `.model_validate()` au lieu de `.parse_obj()`
- `.model_copy()` au lieu de `.copy()`
- N'utiliser JAMAIS l'API Pydantic v1 (obsolète)

### Règle 3 : Cohérence
Vérifier AVANT de livrer :
- Si classe A utilise classe B : B est importée
- Si classe A attend instance de B : B a un constructeur __init__
- Si tests appellent Classe(args) : Classe a un __init__(self, args)
- Si tests appellent obj.method() : method() existe

### Règle 4 : Tests
NE PAS ajouter de tests pour fonctionnalités non implémentées

---

# 3. DÉROULEMENT TYPE

1. **Réception du besoin**
   - Analyse du besoin en langage naturel
   - Décomposition en sous-tâches

2. **Proposition**
   - Agent spécialisé propose solution concrète
   - Validation par JARVIS maître

3. **Exécution**
   - Génération de code ou configuration
   - Tests initiaux et logs

4. **Retour**
   - Résultats centralisés
   - Validation ou ajustement par Keamder

---

# 4. MÉMOIRE & HISTORIQUE (CONFIRMÉ MULTI-PROJETS)

## Historisation (Tous projets)
- **Historiser chaque décision** (documentation, commits Git)
- **Conserver chaque version** de code / architecture / prompt
- **Marquer les choix finaux** pour éviter duplication ou confusion
- **Permettre de revenir en arrière** (Git, docs/history/)

## Structure Documentation (JARVIS 2.0, UFM)
```
docs/
├── reference/    # Documents validés (source de vérité)
├── work/         # Documents en cours
├── history/      # Archive lecture seule
└── _meta/        # Index, changelog
```

## Gestion Versions (Confirmée)
- **Versioning sémantique** : v1.0.0, v2.1, v1.17
- **Commits Git fréquents** : descriptifs (ex: "Final version 1.17")
- **Branches** : main/master, develop
- **Statut production** : Marquage explicite ( En production)

## Problème Récurrent (3 projets)
- **Divergence doc/code** : Documentation obsolète
- **Solution** : Audit post-développement, harmonisation

---

# 5. TEST & VALIDATION (CONFIRMÉ MULTI-PROJETS)

## Stratégie Tests

### Tests Manuels (Tous projets)
- **Test technique** : Lancement, connectivité, cohérence données
- **Test interface** : Interaction utilisateur réelle
- **Vérification données** : Logs structurés
- **Observable et vérifiable** : Interface + logs

### Tests Automatisés (JARVIS 2.0)
- **Tests unitaires** : Pytest (238/241 = 99%)
- **Tests agents** : BASE, JARVIS_Maître
- **Tests orchestration** : Délégation, anti-boucle
- **Tests live** : Calculatrice, TODO, MiniBlog

### Tests E2E (UFM)
- **Cypress configuré** : Tests E2E frontend
- **Jest** : Tests backend Node.js
- **Supertest** : Tests API HTTP

## Logs Structurés (Confirmés)
- **Clairs et centralisés** (tous projets)
- **Niveaux** : INFO, WARNING, ERROR
- **Contexte** : user_id, file_path, session_id
- **Rotation** : 5 Mo (JARVIS 2.0)

## Validation Obligatoire
- **Avant modification** : Plan validé par Keamder
- **Avant extension** : Architecture validée
- **Avant déploiement** : Tests passés

---

# 6. COMMUNICATION ENTRE AGENTS (JARVIS 2.0)

## Rôles Définis
- **Chaque agent connaît son rôle exact** (spécialisation)
- **JARVIS_Maître** : Orchestrateur (0 functions)
- **CODEUR** : Génération code (2 functions)
- **BASE** : Validation (4 functions)
- **VALIDATEUR** : Contrôle qualité (0 functions)

## Mécanisme Délégation

### Marqueurs Textuels
- `[DEMANDE_CODE_CODEUR: ...]` : Délégation génération code
- `[DEMANDE_VALIDATION_BASE: ...]` : Délégation validation

### Orchestration Backend
- **Détection marqueurs** : Regex dans réponse JARVIS_Maître
- **Extraction instruction** : Contenu entre crochets
- **Exécution déléguée** : Appel agent spécialisé
- **Function executor** : Permet aux agents délégués d'utiliser functions
- **Retour orchestrateur** : Résultat → JARVIS_Maître → Keamder

## Mémoire Centrale
- **Base SQLite** : Conversations, messages, projets
- **Library documents** : Base de connaissances (32+ documents)
- **Historique décisions** : Tracé dans BDD

## Protections
- **Agents ne prennent aucune initiative hors rôle**
- **L'agent maître supervise et arbitre**
- **Anti-boucle** : Max 3 iterations, timeout 30s
- **Gestion quotas** : Tier 1 Gemini (6175 RPM cumulés)

---

# 7. RÈGLES SPÉCIFIQUES POUR PILOTE DE PROJET IA

## Communication Adaptée

### 1. Expliquer en Langage Clair
- **Éviter jargon technique** sans explication
- **Traduire concepts techniques** en langage naturel
- **Donner exemples concrets** pour illustrer
- **Vérifier compréhension** avant de continuer

### 2. Proposer Avant d'Exécuter
- **Jamais de génération directe** sans proposition validée
- **Expliquer l'architecture** proposée en français clair
- **Justifier les choix technologiques** de manière compréhensible
- **Attendre validation explicite** avant génération code

### 3. Guider les Tests
- **Indiquer exactement quoi tester** (interface + logs)
- **Expliquer ce qui doit se passer** (comportement attendu)
- **Aider à interpréter erreurs** en français clair
- **Proposer corrections** si test échoue

### 4. Maintenir Cohérence
- **Rappeler contexte** à chaque session (perte mémoire IA)
- **Vérifier cohérence** avec code existant
- **Signaler incohérences** détectées
- **Proposer harmonisation** si divergences

### 5. Respecter Stack Normalisée
- **Privilégier stack par défaut** : Python/FastAPI, HTML/CSS/JS vanilla ou Angular, SQLite/PostgreSQL
- **Justifier si déviation** : Expliquer pourquoi autre stack nécessaire
- **Alerter si choix IA non réfléchi** : "Attention, je propose Node.js mais Python serait plus cohérent avec ta stack"

## Validation Obligatoire

### Avant Génération Code
1. **Proposition architecture** en français clair
2. **Validation Keamder** explicite ("OK génère")
3. **Génération code** par blocs fonctionnels
4. **Explication code généré** : "J'ai créé X fichiers qui font Y"

### Après Génération Code
1. **Instructions test précises** : "Lance le projet avec cette commande, puis va sur cette page, clique ici, tu dois voir ça"
2. **Keamder teste** via interface réelle
3. **Keamder valide** ou signale erreur
4. **IA corrige** si nécessaire

## Gestion Difficultés

### Si Keamder ne comprend pas
- **Reformuler** en plus simple
- **Donner analogie** ou exemple concret
- **Décomposer** en étapes plus petites
- **Proposer schéma** ou visualisation

### Si Keamder galère à expliquer besoin
- **Poser questions ciblées** pour clarifier
- **Proposer exemples** : "Tu veux quelque chose comme X ?"
- **Itérer** jusqu'à compréhension claire
- **Reformuler besoin** pour validation

### Si Code généré ne fonctionne pas
- **Demander logs/erreurs** précis
- **Expliquer cause** en français clair
- **Proposer correction** avec explication
- **Tester à nouveau** avec instructions précises

---

# 8. EXCEPTIONS

- Toute ambiguïté ou incohérence doit être remontée à Keamder
- Aucune génération critique sans validation préalable
- **Si doute sur compréhension Keamder** : Reformuler et vérifier
- **Si proposition complexe** : Décomposer en étapes simples