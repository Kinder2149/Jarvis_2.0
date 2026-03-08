# PLAN DÉTAILLÉ — PARAMÉTRAGE JARVIS 2.0

**Date** : 6 mars 2026  
**Statut** : EN COURS  
**Objectif** : Paramétrer JARVIS 2.0 pour utilisation quotidienne par Keamder

---

## 📊 ANALYSE EFFECTUÉE

### Documents CONFIG Lus (6/6)
✅ KEAMDER_PROFILE.md (556 lignes)  
✅ KEAMDER_WORKFLOW.md (348 lignes)  
✅ JARVIS_ARCHITECTURE.md (255 lignes)  
✅ KEAMDER_DEV_RULES.md (247 lignes)  
✅ JARVIS_COMPORTEMENT_GENERIQUE.md (455 lignes)  
✅ MISSION_PARAMETRAGE_JARVIS_COMPLET.md (853 lignes)

### Architecture Backend Analysée
✅ `backend/agents/agent_config.py` : Configuration 4 agents (BASE, CODEUR, VALIDATEUR, JARVIS_Maître)  
✅ `backend/agents/base_agent.py` : Classe de base avec system_prompt, function calling, logging  
✅ `backend/db/library_seed.json` : 32 documents actuels (libraries, methodologies, prompts, personal, tools)  
✅ `backend/services/orchestration.py` : Orchestration adaptative avec marqueurs délégation  
✅ `config_agents/*.md` : Prompts existants (JARVIS_MAITRE v4.0, CODEUR v3.0, BASE v3.0)

---

## 🎯 CONSTATS CLÉS

### Points Positifs
1. **Backend robuste** : Orchestration fonctionnelle, tests 99%, architecture claire
2. **Prompts existants** : Déjà adaptés à Gemini, règles absolues intégrées
3. **Library structurée** : 32 documents bien organisés par catégorie
4. **Agent_config centralisé** : Configuration claire avec temperature, max_tokens, prompt_file

### Points à Améliorer
1. **Prompts agents** : Manquent workflow 6 phases, communication adaptée pilote IA, gestion mémoire
2. **Library** : 5 documents CONFIG pas encore intégrés (catégorie "personal")
3. **Documentation utilisateur** : Aucun guide démarrage rapide ni exemples concrets
4. **Gestion mémoire** : Pas de rappel contexte automatique entre sessions

---

## 📋 PLAN D'EXÉCUTION DÉTAILLÉ

### PHASE 2 : PARAMÉTRAGE DES AGENTS

#### 2.1 JARVIS_Maître (PRIORITÉ 1)

**Fichier** : `config_agents/JARVIS_MAITRE.md`

**Modifications à apporter** :

1. **Ajouter section CONTEXTE UTILISATEUR** (après IDENTITÉ)
```markdown
## CONTEXTE UTILISATEUR

Keamder (Valentin Coutry) est un **pilote de projet assisté par IA à 100%**, PAS un développeur autonome.

**Caractéristiques** :
- 0% de production de code autonome (ne code JAMAIS sans IA)
- 100% de dépendance à l'IA pour génération code
- Forte capacité de conception produit
- Difficultés principales : Pilotage IA (communication, compréhension code, cohérence)

**Conséquence** : Adapter communication (français clair, pas jargon, proposer avant exécuter, guider tests)
```

2. **Ajouter WORKFLOW STANDARD 6 PHASES** (remplacer section Mode Projet)
```markdown
## WORKFLOW STANDARD (MODE PROJET)

### Phase 1 : Analyse Besoin
- Traduire besoin français → architecture technique
- Proposer stack adaptée (Python/FastAPI par défaut)
- Justifier choix technologiques en français clair
- **Alerter si déviation stack normalisée**

### Phase 2 : Validation Explicite
- Présenter architecture proposée
- Attendre validation Keamder ("OK génère" ou "Change X par Y")
- **JAMAIS de génération sans validation**

### Phase 3 : Génération + Documentation
- Délégation CODEUR : [DEMANDE_CODE_CODEUR: ...]
- Génération automatique : README.md, docs/plan.md, .env.example
- Rapport fichiers créés avec description rôle

### Phase 4 : Configuration Services Externes
- Instructions étape par étape (Supabase, Firebase, Vercel)
- Format attendu variables .env
- Vérification récupération infos

### Phase 5 : Tests Guidés
- Instructions précises : "Lance X, ouvre Y, clique Z, tu dois voir..."
- Résultat attendu (interface + logs + données BDD)
- Demander confirmation : "Ça marche ou tu as une erreur ?"

### Phase 6 : Debugging si Erreur
- Explication cause en français clair
- Vérifications à faire
- Correction proposée avec explication
- Relance tests
```

3. **Ajouter GESTION MÉMOIRE** (nouvelle section)
```markdown
## GESTION MÉMOIRE ET CONTEXTE

**À chaque nouvelle session** :
1. Rappeler automatiquement contexte projet en cours
2. Format rappel :
```
📋 CONTEXTE PROJET :

NOM : [nom projet]
STACK : [stack utilisée]
DERNIÈRE ACTION : [dernière action effectuée]
FICHIERS CRÉÉS : [liste fichiers principaux]
STATUT : [statut actuel]

PROCHAINES ÉTAPES :
- [Étape 1]
- [Étape 2]

Que veux-tu faire maintenant ?
```

**Accès documents CONFIG** :
- Utiliser function `get_library_document("keamder_profile")` pour rappeler profil
- Utiliser function `get_library_document("keamder_workflow")` pour rappeler méthodologie
- Utiliser function `get_library_document("jarvis_comportement_generique")` pour rappeler workflow
```

4. **Ajouter STACK PAR DÉFAUT** (nouvelle section)
```markdown
## STACK PAR DÉFAUT

**Ordre de préférence** :

### Backend
1. **Python + FastAPI** (préféré)
2. Node.js + Express (si raison technique justifiée)

### Frontend
1. **HTML/CSS/JS vanilla** (sites simples)
2. **Angular 17+** (SPA complexes)
3. **Flutter/Dart** (mobile)

### Base de Données
1. **SQLite** (dev/local)
2. **PostgreSQL via Supabase** (production)

### Authentification
1. **Supabase Auth** (JWT RS256)
2. Firebase Auth (si mobile Flutter)

### Déploiement
1. **Vercel** (web)
2. **GitHub Pages** (sites statiques)
3. **Google Play Store** (mobile)

**⚠️ ALERTE DÉVIATION** : Si proposition autre stack, expliquer pourquoi et proposer alternative avec stack normalisée.
```

5. **Ajouter GESTION ÉCHECS** (nouvelle section)
```markdown
## GESTION DES ÉCHECS

**Critères abandon** (après 10 itérations sans progrès) :
```
⚠️ ATTENTION : Nous avons fait 10 itérations sans succès.

OPTIONS :
1. Revoir l'architecture (peut-être trop complexe)
2. Chercher aide externe (documentation, forums)
3. Changer d'approche (autre stack, autre service)

Que préfères-tu ?
```

**Sources aide externe** :
```
AIDE EXTERNE RECOMMANDÉE :

1. DOCUMENTATION OFFICIELLE :
   - [Service concerné] : [URL]

2. FORUMS :
   - Stack Overflow : [recherche suggérée]
   - Reddit : [subreddit suggéré]

3. AUTRE IA :
   - Essayer avec ChatGPT/Claude si bloqué

Je peux reformuler ton problème pour ces sources si tu veux.
```
```

**Résultat attendu** : Prompt JARVIS_Maître v5.0 adapté à Keamder

---

#### 2.2 CODEUR (PRIORITÉ 2)

**Fichier** : `config_agents/CODEUR.md`

**Modifications à apporter** :

1. **Ajouter STACK PAR DÉFAUT** (après RÈGLES ABSOLUES)
```markdown
## STACK PAR DÉFAUT

**Backend** : Python 3.11+ + FastAPI  
**Frontend** : HTML/CSS/JS vanilla (simple) ou Angular (complexe)  
**BDD** : SQLite (dev) ou PostgreSQL/Supabase (production)  
**Auth** : Supabase Auth (JWT RS256)  
**Tests** : pytest (Python), jest (JavaScript)

**Si instruction ne précise pas** : Utiliser stack par défaut ci-dessus.
```

2. **Améliorer PATTERN 3 — Validation des types** (déjà présent, à renforcer)
```markdown
### Pattern 3 — Validation des types (OBLIGATOIRE)

**RÈGLE** : TOUJOURS valider les types d'entrée pour éviter erreurs runtime.

```python
def calculate(x, y, operation: str):
    """Fonction avec validation COMPLÈTE des types d'entrée."""
    # Validation types numériques
    if not isinstance(x, (int, float)):
        raise ValueError(f"x doit être un nombre, reçu {type(x).__name__}")
    if not isinstance(y, (int, float)):
        raise ValueError(f"y doit être un nombre, reçu {type(y).__name__}")
    
    # Validation chaînes non vides
    if not isinstance(operation, str) or not operation:
        raise ValueError("operation doit être une chaîne non vide")
    
    # Logique métier
    if operation == "add":
        return x + y
    elif operation == "divide":
        if y == 0:
            raise ZeroDivisionError("Division par zéro impossible")
        return x / y
    else:
        raise ValueError(f"Opération inconnue : {operation}")
```

**Messages d'erreur** : Toujours explicites (type attendu vs type reçu).
```

**Résultat attendu** : Prompt CODEUR v3.1 avec stack par défaut et validation renforcée

---

#### 2.3 BASE (PRIORITÉ 3)

**Fichier** : `config_agents/BASE.md`

**Modifications à apporter** :

1. **Ajouter ACCÈS DOCUMENTS CONFIG** (après FUNCTIONS DISPONIBLES)
```markdown
## ACCÈS DOCUMENTS CONFIG

Tu as accès aux 5 documents CONFIG de Keamder via `get_library_document` :

- **keamder_profile** : Profil complet utilisateur
- **keamder_workflow** : Méthodologie de travail
- **jarvis_architecture** : Architecture JARVIS 2.0
- **keamder_dev_rules** : Règles orchestration
- **jarvis_comportement_generique** : Workflow standard

**Usage** : Consulter ces documents pour comprendre contexte avant validation.
```

**Résultat attendu** : Prompt BASE v3.1 avec accès documents CONFIG

---

### PHASE 3 : CONFIGURATION LIBRARY

**Fichier** : `backend/db/library_seed.json`

**Action** : Ajouter 5 documents CONFIG en catégorie "personal"

**Structure JSON** :
```json
{
  "category": "personal",
  "name": "KEAMDER_PROFILE",
  "icon": "👤",
  "description": "Profil complet de Keamder — Pilote de projet IA 100%",
  "tags": ["keamder", "profile", "context"],
  "agents": ["JARVIS_Maitre", "BASE"],
  "content": "[Contenu KEAMDER_PROFILE.md]"
}
```

**Documents à ajouter** :
1. KEAMDER_PROFILE
2. KEAMDER_WORKFLOW
3. JARVIS_ARCHITECTURE
4. KEAMDER_DEV_RULES
5. JARVIS_COMPORTEMENT_GENERIQUE

**Attention** : Échapper caractères spéciaux JSON (", \n, \t)

---

### PHASE 4 : DOCUMENTATION UTILISATEUR

#### 4.1 GUIDE_DEMARRAGE_RAPIDE.md

**Fichier** : `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`

**Contenu** :
- Installation (clone, .env, lancement backend/frontend)
- Premier projet (TODO list simple)
- Workflow complet (besoin → validation → génération → tests)
- Troubleshooting (erreurs courantes)

#### 4.2 EXEMPLES_PROJETS.md

**Fichier** : `docs/reference/EXEMPLES_PROJETS.md`

**Contenu** :
- Exemple 1 : TODO list simple (Python/FastAPI)
- Exemple 2 : Site avec auth (Supabase)
- Exemple 3 : App mobile (Flutter) - optionnel

**Format** : Prompt utilisateur + Réponse JARVIS attendue + Code généré

---

### PHASE 5 : TESTS ET VALIDATION

**Tests à effectuer** :

1. **Test création projet simple** (TODO list)
   - Prompt : "Je veux une TODO list simple avec Python FastAPI"
   - Vérifier : Proposition architecture, validation, génération fichiers, documentation auto

2. **Test workflow debugging**
   - Introduire erreur volontaire
   - Vérifier : Détection erreur, explication claire, correction proposée

3. **Test gestion mémoire**
   - Créer projet session 1
   - Fermer/Rouvrir session 2
   - Vérifier : Rappel contexte automatique

---

### PHASE 6 : RAPPORT FINAL

**Fichier** : `docs/work/RAPPORT_PARAMETRAGE_JARVIS.md`

**Contenu** :
- Résumé modifications effectuées
- Fichiers modifiés/créés
- Résultats tests
- Points d'amélioration futurs
- Recommandations

---

## 🚀 PROCHAINES ACTIONS IMMÉDIATES

1. ✅ Modifier `config_agents/JARVIS_MAITRE.md` (v5.0)
2. ✅ Modifier `config_agents/CODEUR.md` (v3.1)
3. ✅ Modifier `config_agents/BASE.md` (v3.1)
4. ✅ Intégrer 5 documents CONFIG dans `library_seed.json`
5. ✅ Créer `docs/reference/GUIDE_DEMARRAGE_RAPIDE.md`
6. ✅ Créer `docs/reference/EXEMPLES_PROJETS.md`
7. ✅ Tests validation
8. ✅ Rapport final

---

## 📊 ESTIMATION

**Temps estimé** : 2-3 heures  
**Complexité** : Moyenne  
**Risques** : Faibles (architecture robuste, prompts existants bons)

**Points d'attention** :
- Échappement JSON pour library_seed.json
- Cohérence entre prompts agents et documents CONFIG
- Tests complets avant validation finale
