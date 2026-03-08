# JARVIS 2.0 — Explication Complète pour Valentin

**Date** : 7 mars 2026  
**Objectif** : Comprendre comment fonctionne JARVIS 2.0 sans termes techniques

---

## 🎯 TON BESOIN RÉEL

Tu veux un outil qui te permette de **créer des projets complets** alors que tu ne sais pas coder seul. Tu as besoin d'une **équipe d'IA compétente** qui comprend tes besoins et produit du code structuré, sans doublons, bien documenté.

**JARVIS 2.0 est exactement ça** : ton équipe d'IA personnelle.

---

## 🏗️ COMMENT ÇA MARCHE (VERSION SIMPLE)

Imagine une **agence de développement** avec 4 employés :

### 1. **JARVIS_Maître** — Le Chef de Projet
- **Son rôle** : Comprendre ce que tu veux, organiser le travail, déléguer aux spécialistes
- **Ce qu'il fait** :
  - Tu lui dis "Je veux une calculatrice"
  - Il réfléchit : "OK, il faut 2 fichiers : le code de la calculatrice + les tests"
  - Il donne l'ordre au CODEUR : "Crée ces 2 fichiers avec ces fonctionnalités"
  - Il vérifie que tout est bien fait
  - Il te dit "C'est prêt, voilà ce qui a été créé"

### 2. **CODEUR** — Le Développeur
- **Son rôle** : Écrire le code exactement comme demandé
- **Ce qu'il fait** :
  - Reçoit une instruction précise de JARVIS_Maître
  - Écrit le code complet (fichiers, fonctions, tests)
  - Respecte les règles de qualité (pas de doublons, code propre)
  - Livre les fichiers sur ton disque

### 3. **BASE** — L'Assistant Polyvalent
- **Son rôle** : Vérifier que tout est complet, faire des rapports
- **Ce qu'il fait** :
  - Vérifie que tous les fichiers demandés ont été créés
  - Analyse le code produit et fait un résumé
  - Répond aux questions simples

### 4. **VALIDATEUR** — Le Contrôleur Qualité
- **Son rôle** : Détecter les bugs et erreurs
- **Ce qu'il fait** :
  - Lit le code du CODEUR
  - Cherche les erreurs (bugs, incohérences, oublis)
  - Signale les problèmes à JARVIS_Maître
  - Si problème → CODEUR corrige → VALIDATEUR revérifie

---

## 🔄 LE WORKFLOW COMPLET (ÉTAPE PAR ÉTAPE)

### Exemple : Tu veux créer une calculatrice

**1. Tu dis à JARVIS_Maître** :
```
"Je veux une calculatrice Python avec addition, soustraction, multiplication, division"
```

**2. JARVIS_Maître analyse** :
- Il comprend que tu veux un projet Python
- Il sait qu'il faut : le code + les tests
- Il prépare l'instruction pour le CODEUR

**3. JARVIS_Maître délègue au CODEUR** :
```
[DEMANDE_CODE_CODEUR: Crée les fichiers suivants :
- src/calculator.py : classe Calculator avec méthodes add, subtract, multiply, divide
- tests/test_calculator.py : tests pytest pour toutes les fonctions]
```

**4. Le CODEUR travaille** :
- Il écrit `src/calculator.py` avec le code complet
- Il écrit `tests/test_calculator.py` avec les tests
- Il sauvegarde les fichiers sur ton disque

**5. Le VALIDATEUR vérifie** :
- Il lit les 2 fichiers
- Il cherche les bugs (division par zéro, erreurs de syntaxe, etc.)
- Si OK → il dit "VALIDE"
- Si problème → il dit "INVALIDE : voici les bugs"

**6. Si INVALIDE, le CODEUR corrige** :
- JARVIS_Maître renvoie le CODEUR corriger
- VALIDATEUR revérifie
- Maximum 2 corrections (sinon on arrête)

**7. JARVIS_Maître te répond** :
```
✅ CODE GÉNÉRÉ !

FICHIERS CRÉÉS :
- src/calculator.py (120 lignes) : Classe Calculator avec 4 méthodes
- tests/test_calculator.py (80 lignes) : 8 tests couvrant tous les cas

VALIDATION : ✅ Code validé par le VALIDATEUR

PROCHAINE ÉTAPE : Lance les tests avec "pytest tests/"
```

---

## 🧠 LA LIBRAIRIE (KNOWLEDGE BASE)

C'est comme une **bibliothèque de documentation** que les agents peuvent consulter.

### Comment ça marche ?

**1. Tu ajoutes des documents** :
- Templates de code (exemples de calculatrice, TODO app, etc.)
- Règles de codage (comment tu veux que le code soit écrit)
- Spécifications techniques (comment utiliser telle API)

**2. Les documents sont découpés** :
- Chaque document est découpé en petits morceaux (chunks)
- Chaque morceau est transformé en "empreinte numérique" (embedding)
- Tout est stocké dans une base de données (ChromaDB)

**3. Quand le CODEUR reçoit une tâche** :
- Le système cherche dans la Library les documents pertinents
- Exemple : Si tu demandes une calculatrice, il trouve le template "Calculator"
- Il ajoute ce contexte à l'instruction du CODEUR
- Le CODEUR produit du code qui respecte tes standards

### Exemple concret :

**Sans Library** :
```
CODEUR reçoit : "Crée une calculatrice"
→ Il invente sa propre structure
→ Peut ne pas respecter tes préférences
```

**Avec Library** :
```
CODEUR reçoit : "Crée une calculatrice"
+ CONTEXTE LIBRARY : "Voici un exemple de calculatrice que Valentin aime"
→ Il suit l'exemple
→ Code conforme à tes attentes
```

---

## ⚙️ LA CONFIGURATION (CE QUI CONTRÔLE TOUT)

### 1. **Le fichier `.env`** — Les Réglages Secrets

C'est comme le **panneau de contrôle** de JARVIS. Il contient :

```env
# Quelle IA utiliser pour chaque agent
JARVIS_MAITRE_MODEL=gemini-2.5-pro    # Chef de projet = IA puissante
CODEUR_MODEL=gemini-2.5-pro           # Développeur = IA puissante
BASE_MODEL=gemini-2.5-pro             # Assistant = IA standard
VALIDATEUR_MODEL=gemini-3.1-pro       # Contrôleur = IA précise

# Clé API pour accéder à Google Gemini
GEMINI_API_KEY=ta_clé_secrète
```

**Pourquoi c'est important ?** :
- Si tu changes le modèle, tu changes la qualité du code
- Si tu changes la clé API, tu changes le compte utilisé (quotas différents)

### 2. **Le fichier `agent_config.py`** — Les Caractéristiques des Agents

C'est comme la **fiche de poste** de chaque agent :

```python
"CODEUR": {
    "temperature": 0.3,      # Créativité basse = code précis
    "max_tokens": 16384,     # Peut écrire beaucoup de code d'un coup
    "min_delay_seconds": 10  # Attend 10s entre chaque requête (quotas)
}

"JARVIS_Maître": {
    "temperature": 0.3,      # Créativité basse = instructions précises
    "max_tokens": 4096,      # Répond de manière concise
    "min_delay_seconds": 4   # Attend 4s entre chaque requête
}
```

**Ce que ça change** :
- **temperature** : Plus c'est bas (0.1-0.3), plus c'est prévisible. Plus c'est haut (0.7-1.0), plus c'est créatif
- **max_tokens** : Limite la longueur de la réponse (1 token ≈ 1 mot)
- **min_delay_seconds** : Évite de dépasser les quotas gratuits de Google

### 3. **Les fichiers de prompts** (`config_agents/*.md`) — Les Instructions

C'est comme le **manuel de l'employé**. Chaque agent a son manuel :

- `JARVIS_MAITRE.md` : "Tu es le chef de projet, voici comment tu dois travailler"
- `CODEUR.md` : "Tu es le développeur, voici les règles de code à respecter"
- `BASE.md` : "Tu es l'assistant, voici comment vérifier la complétude"
- `VALIDATEUR.md` : "Tu es le contrôleur, voici comment détecter les bugs"

**Exemple extrait de `CODEUR.md`** :
```markdown
RÈGLE 1 — Storage JSON : Une classe Storage doit TOUJOURS avoir :
1. Constructeur __init__(self, filepath: str)
2. Méthode save(self, data) pour écrire
3. Méthode load(self) -> data pour lire
```

→ Ça garantit que le CODEUR respecte toujours cette règle.

---

## 🔧 LES PROBLÈMES ACTUELS (DIAGNOSTIC COMPLET)

### ✅ CE QUI FONCTIONNE

1. **L'architecture est solide** :
   - 4 agents bien définis
   - Orchestration adaptative (boucle CODEUR/BASE/VALIDATEUR)
   - Délégation via marqueurs `[DEMANDE_CODE_CODEUR: ...]`

2. **Le RAG est opérationnel** :
   - API RAG sur port 5001
   - ChromaDB pour stocker les documents
   - Enrichissement automatique des instructions CODEUR

3. **Les prompts sont bien écrits** :
   - JARVIS_Maître sait déléguer immédiatement
   - CODEUR a des règles strictes (Pydantic v2, Storage, validation types)
   - VALIDATEUR détecte les bugs

### ⚠️ CE QUI PEUT ÊTRE AMÉLIORÉ

#### 1. **Quotas Gemini gratuits trop limités**

**Problème** :
- Gemini gratuit = 15 requêtes/minute maximum
- Si projet complexe (10+ fichiers) → dépasse le quota → erreur

**Solutions** :
1. **Passer à Gemini Tier 1** (payant mais quotas 10x plus élevés)
2. **Utiliser plusieurs modèles** pour répartir les quotas :
   - JARVIS_Maître → `gemini-2.0-flash` (2000 req/min)
   - CODEUR → `gemini-2.5-pro` (150 req/min)
   - BASE → `gemini-2.0-flash-lite` (4000 req/min)
   - VALIDATEUR → `gemini-3.1-pro-preview` (25 req/min)

#### 2. **Library pas assez remplie**

**Problème** :
- Tu as une Library vide ou presque
- Le CODEUR n'a pas d'exemples à suivre
- Il invente sa propre structure

**Solution** :
- Ajouter des templates dans `RAG/doc/` :
  - `template_calculator.md` : Exemple de calculatrice bien faite
  - `template_todo_app.md` : Exemple d'app TODO bien faite
  - `keamder_coding_rules.md` : Tes règles de code personnelles

#### 3. **Pas de mémoire entre sessions**

**Problème** :
- Si tu fermes JARVIS et tu le relances, il a tout oublié
- Il ne sait plus sur quel projet tu travaillais

**Solution** :
- Ajouter un système de "rappel de contexte" au démarrage
- Stocker l'état du projet dans une base de données

#### 4. **Validation manuelle trop fréquente**

**Problème** :
- JARVIS_Maître demande validation même pour des choses simples
- Ralentit le workflow

**Solution** :
- Améliorer la détection de "projet vide" (pas de validation requise)
- Ajouter une règle : "Si <5 fichiers, génère directement"

---

## 🎯 OPTIMISATIONS RECOMMANDÉES POUR TOI

### Priorité 1 : Remplir la Library

**Pourquoi** : C'est la clé pour avoir du code de qualité conforme à tes attentes.

**Actions** :
1. Crée un dossier `RAG/templates/`
2. Ajoute des fichiers markdown avec des exemples de code que tu aimes
3. Lance le script d'indexation : `python RAG/index_jarvis_library.py`

**Exemple de template** :
```markdown
# Template : Calculatrice Python

## Structure recommandée

src/
  calculator.py  # Classe Calculator
tests/
  test_calculator.py  # Tests pytest

## Code de référence

### calculator.py
```python
class Calculator:
    def add(self, a, b):
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Les arguments doivent être des nombres")
        return a + b
```

### test_calculator.py
```python
import pytest
from src.calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_add_invalid_type():
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.add("2", 3)
```
```

### Priorité 2 : Passer à Gemini Tier 1 (ou répartir les modèles)

**Pourquoi** : Les quotas gratuits sont trop limités pour des projets réels.

**Option A — Passer à Tier 1 (recommandé)** :
- Coût : ~5-10€/mois pour usage normal
- Quotas : 10-15x plus élevés
- Pas de limite RPD (requêtes par jour)

**Option B — Répartir sur plusieurs modèles gratuits** :
- Modifier `.env` pour utiliser des modèles différents par agent
- Cumule les quotas (2000 + 150 + 4000 + 25 = 6175 req/min)
- Gratuit mais plus complexe

### Priorité 3 : Créer un profil utilisateur dans la Library

**Pourquoi** : Les agents sauront qui tu es et comment tu travailles.

**Action** :
Crée `RAG/doc/keamder_profile.md` :
```markdown
# Profil : Valentin Coutry (Keamder)

## Qui je suis
- Pilote de projet assisté par IA à 100%
- Ne code JAMAIS sans IA
- Forte capacité de conception produit
- Besoin d'instructions claires et guidées

## Comment je travaille
- Je donne le besoin en français simple
- Je veux une proposition d'architecture AVANT génération
- Je valide explicitement avant toute génération de code
- Je teste manuellement (pas de commandes complexes)

## Stack préférée
- Backend : Python + FastAPI
- Frontend : HTML/CSS/JS vanilla (simple) ou Angular (complexe)
- BDD : SQLite (dev) ou Supabase (production)
- Tests : pytest (Python)

## Ce que je déteste
- Code non documenté
- Doublons de code
- Erreurs de syntaxe
- Projets qui ne démarrent pas du premier coup
```

### Priorité 4 : Automatiser le démarrage

**Pourquoi** : Tu perds du temps à lancer manuellement backend + RAG.

**Action** :
Crée `start_jarvis.ps1` (Windows PowerShell) :
```powershell
# Démarrer l'API RAG
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd RAG; python -m src.main"

# Attendre 3 secondes
Start-Sleep -Seconds 3

# Démarrer le backend JARVIS
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python start_server.py"

# Attendre 3 secondes
Start-Sleep -Seconds 3

# Ouvrir le frontend dans le navigateur
Start-Process "http://localhost:8000"

Write-Host "✅ JARVIS 2.0 démarré !" -ForegroundColor Green
```

Ensuite : Double-clic sur `start_jarvis.ps1` → Tout démarre automatiquement.

---

## 📊 RÉSUMÉ VISUEL

```
TOI (Valentin)
    ↓
    "Je veux une calculatrice"
    ↓
JARVIS_Maître (Chef de Projet)
    ↓
    [DEMANDE_CODE_CODEUR: Crée calculator.py + tests]
    ↓
CODEUR (Développeur)
    ↓
    Consulte LIBRARY → Trouve template calculatrice
    ↓
    Écrit calculator.py + test_calculator.py
    ↓
VALIDATEUR (Contrôleur Qualité)
    ↓
    Vérifie le code → Détecte bugs éventuels
    ↓
    Si bugs → CODEUR corrige → VALIDATEUR revérifie
    ↓
JARVIS_Maître (Chef de Projet)
    ↓
    "✅ Code généré et validé ! Voici les fichiers créés."
    ↓
TOI (Valentin)
    ↓
    Tu testes manuellement
```

---

## 🚀 PROCHAINES ÉTAPES CONCRÈTES

### Aujourd'hui (1h)
1. ✅ Lire ce document en entier
2. ⬜ Créer `RAG/templates/template_calculator.md` avec un exemple
3. ⬜ Créer `RAG/doc/keamder_profile.md` avec ton profil
4. ⬜ Lancer `python RAG/index_jarvis_library.py` pour indexer

### Cette semaine (3h)
1. ⬜ Tester JARVIS avec un projet simple (calculatrice)
2. ⬜ Vérifier que la Library est bien utilisée (logs)
3. ⬜ Ajouter 3-5 templates supplémentaires (TODO, MiniBlog, etc.)
4. ⬜ Créer le script `start_jarvis.ps1` pour automatiser

### Ce mois-ci (5h)
1. ⬜ Passer à Gemini Tier 1 (ou répartir les modèles)
2. ⬜ Créer 10+ templates dans la Library
3. ⬜ Tester JARVIS sur un vrai projet (app complète)
4. ⬜ Documenter tes retours d'expérience

---

## ❓ FAQ (Questions Fréquentes)

### Q1 : Pourquoi JARVIS ne génère pas de code parfois ?

**Réponse** : Plusieurs causes possibles :
1. **Quota dépassé** : Gemini gratuit = 15 req/min max → Attends 1 minute ou passe à Tier 1
2. **Instruction floue** : JARVIS_Maître ne comprend pas → Reformule ta demande
3. **Bug orchestration** : Vérifie les logs dans `backend/logs/jarvis_audit.log`

### Q2 : Comment savoir si la Library est utilisée ?

**Réponse** : Regarde les logs :
```
Orchestration: enrichissement RAG activé pour CODEUR
Orchestration: instruction CODEUR enrichie avec RAG
```

Si tu vois ça → Library utilisée ✅  
Si tu ne vois pas → Library vide ou API RAG non démarrée ❌

### Q3 : Pourquoi le VALIDATEUR trouve toujours des bugs ?

**Réponse** : C'est normal ! Le VALIDATEUR est strict. Mais si :
- Il trouve les MÊMES bugs 3 fois de suite → Problème prompt CODEUR
- Il trouve des bugs imaginaires → Problème prompt VALIDATEUR

### Q4 : Puis-je utiliser JARVIS sans la Library ?

**Réponse** : Oui, mais :
- ✅ Ça fonctionne (CODEUR génère du code)
- ❌ Qualité aléatoire (pas de référence)
- ❌ Pas de cohérence entre projets

**Recommandation** : Remplis la Library, même avec 2-3 templates.

### Q5 : Combien coûte Gemini Tier 1 ?

**Réponse** :
- **Gratuit** : 15 req/min, 20 req/jour (trop limité)
- **Tier 1** : ~5-10€/mois pour usage normal (100-200 projets/mois)
- **Tier 2** : ~20-50€/mois pour usage intensif (500+ projets/mois)

---

## 📞 SUPPORT

Si tu es bloqué :

1. **Vérifie les logs** : `backend/logs/jarvis_audit.log`
2. **Vérifie l'API RAG** : Ouvre `http://localhost:5001` → Doit afficher `{"message": "API Flask active"}`
3. **Vérifie le backend** : Ouvre `http://localhost:8000` → Doit afficher l'interface JARVIS
4. **Demande à JARVIS_Maître** : "Explique-moi pourquoi ça n'a pas marché"

---

## 🎉 CONCLUSION

**JARVIS 2.0 est ton équipe d'IA personnelle** :
- JARVIS_Maître = Chef de projet qui comprend tes besoins
- CODEUR = Développeur qui écrit le code
- VALIDATEUR = Contrôleur qui détecte les bugs
- BASE = Assistant qui vérifie et rapporte

**La Library est ton avantage compétitif** :
- Templates de code de qualité
- Règles personnalisées
- Cohérence entre projets

**Les optimisations recommandées** :
1. Remplir la Library (priorité absolue)
2. Passer à Gemini Tier 1 (ou répartir modèles)
3. Créer ton profil utilisateur
4. Automatiser le démarrage

**Avec ces optimisations, JARVIS devient vraiment ton remplaçant de Windsurf** : une équipe d'IA qui code pour toi, respecte tes standards, et produit du code de qualité.

---

**Prêt à optimiser JARVIS ? Commence par la Library ! 🚀**
