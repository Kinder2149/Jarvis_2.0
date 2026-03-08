# Checklist Déploiement Gemini — 7 mars 2026

**Version CODEUR** : 3.3  
**Version JARVIS_Maître** : 5.2  
**Objectif** : Résoudre problèmes MAX_TOKENS, parsing, et validation inutile

---

## 🎯 PROBLÈMES RÉSOLUS

### Problème 1 : Gemini MAX_TOKENS (4 occurrences)
- **Cause** : `max_tokens=4096` insuffisant pour CODEUR
- **Solution** : Augmentation à `max_tokens=8192`
- **Impact** : Résout réponses tronquées/vides

### Problème 2 : Parsing Échoué (7 occurrences)
- **Cause** : Format `# src/todo.py` sans ligne vide
- **Solution** : Format strict avec ligne vide obligatoire
- **Impact** : Résout pattern alternatif non détecté

### Problème 3 : Incohérence Noms Classes
- **Cause** : `TodoList` au lieu de `TodoManager`
- **Solution** : Règle cohérence noms exacts renforcée
- **Impact** : Résout erreurs import tests

### Problème 4 : Validation Inutile Projets TEST
- **Cause** : Exception projets vides trop bas dans prompt
- **Solution** : Déplacement section EXCEPTION en priorité
- **Impact** : Supprime validation inutile, workflow fluide

---

## 📋 CHECKLIST DÉPLOIEMENT GOOGLE AI STUDIO

### Étape 1 : Accéder à Google AI Studio
- [ ] Ouvrir https://aistudio.google.com/
- [ ] Se connecter avec compte Google
- [ ] Vérifier clé API : `AIzaSyCmhnxKvTM7cIxdEAmnlucQDCV7r48FI6g`

---

### Étape 2 : Configurer Agent CODEUR

**URL** : https://aistudio.google.com/prompts/new_chat

#### Paramètres Modèle
- [ ] **Modèle** : `gemini-2.0-flash` (ou `gemini-2.5-pro` si quotas disponibles)
- [ ] **Temperature** : `0.3`
- [ ] **Max output tokens** : `8192` ⚠️ **CRITIQUE** (était 4096)
- [ ] **Top-p** : `0.95` (par défaut)
- [ ] **Top-k** : `40` (par défaut)

#### Prompt
- [ ] Copier intégralement `config_agents/CODEUR.md` (v3.3)
- [ ] Vérifier ligne 7 : `**Max tokens** : 8192`
- [ ] Coller dans le champ "System instructions"

#### Vérification
- [ ] Tester avec : "Crée un fichier src/test.py avec une classe Test"
- [ ] Vérifier format : `# src/test.py` + ligne vide + ` ```python`
- [ ] Vérifier réponse complète (pas de troncature)

---

### Étape 3 : Configurer Agent JARVIS_Maître

**URL** : https://aistudio.google.com/prompts/new_chat

#### Paramètres Modèle
- [ ] **Modèle** : `gemini-2.0-flash`
- [ ] **Temperature** : `0.3`
- [ ] **Max output tokens** : `4096` (suffisant pour orchestration)
- [ ] **Top-p** : `0.95` (par défaut)
- [ ] **Top-k** : `40` (par défaut)

#### Prompt
- [ ] Copier intégralement `config_agents/JARVIS_MAITRE.md` (v5.2)
- [ ] Vérifier ligne 4 : `**Version** : 5.2`
- [ ] Vérifier présence section "EXCEPTION — PROJETS VIDES" (ligne ~93)
- [ ] Coller dans le champ "System instructions"

#### Vérification
- [ ] Tester avec projet TEST : "PROJET: Test PATH: D:\Coding\TEST\test_demo DESC: Demo"
- [ ] Vérifier : PAS de validation demandée
- [ ] Vérifier : Délégation immédiate `[DEMANDE_CODE_CODEUR: ...]`

---

### Étape 4 : Sauvegarder Configuration

- [ ] CODEUR : Cliquer "Save" → Nommer "JARVIS_CODEUR_v3.3"
- [ ] JARVIS_Maître : Cliquer "Save" → Nommer "JARVIS_MAITRE_v5.2"
- [ ] Noter les URLs des prompts sauvegardés

---

## 🧪 TESTS DE VALIDATION

### Test 1 : CODEUR — Format Strict
**Commande** :
```
Crée les fichiers suivants :
- src/calculator.py : classe Calculator avec méthode add(a, b)
- tests/test_calculator.py : test pytest pour add()
```

**Résultat attendu** :
```
# src/calculator.py

```python
class Calculator:
    def add(self, a, b):
        return a + b
```

# tests/test_calculator.py

```python
import pytest
from src.calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5
```
```

**Vérifications** :
- [ ] Ligne vide après `# src/calculator.py`
- [ ] Ligne vide après `# tests/test_calculator.py`
- [ ] Code complet (pas de troncature)
- [ ] Imports corrects

---

### Test 2 : CODEUR — Cohérence Noms
**Commande** :
```
Crée les fichiers suivants :
- src/todo.py : classe TodoManager avec méthode add_task()
- tests/test_todo.py : test pytest qui importe TodoManager
```

**Résultat attendu** :
```python
# src/todo.py
class TodoManager:  # ✅ Nom exact (pas TodoList)
    def add_task(self, description):
        pass

# tests/test_todo.py
from src.todo import TodoManager  # ✅ Import cohérent
```

**Vérifications** :
- [ ] Classe nommée `TodoManager` (pas `TodoList`)
- [ ] Import `from src.todo import TodoManager`
- [ ] Pas d'erreur import

---

### Test 3 : JARVIS_Maître — Exception Projets TEST
**Commande** :
```
PROJET: Test Calculatrice
PATH: D:\Coding\TEST\test_calculatrice
DESC: Calculatrice CLI pour tests live

Crée une calculatrice Python simple.
```

**Résultat attendu** :
```
[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour une calculatrice Python :
- src/calculator.py : CLASSE Calculator (nom exact) avec méthodes add(a,b), subtract(a,b), multiply(a,b), divide(a,b)
- tests/test_calculator.py : tests pytest couvrant tous les cas]
```

**Vérifications** :
- [ ] PAS de message "⚠️ VALIDATION REQUISE"
- [ ] PAS de message "⚠️ CLARIFICATION NÉCESSAIRE"
- [ ] Délégation immédiate (première réponse)
- [ ] Marqueur `[DEMANDE_CODE_CODEUR: ...]` présent

---

## 🔄 SYNCHRONISATION BACKEND

**Fichiers à vérifier** :
- [ ] `.env` : `CODEUR_MODEL=gemini-2.0-flash`
- [ ] `.env` : `JARVIS_MAITRE_MODEL=gemini-2.0-flash`
- [ ] Backend utilise bien les prompts v3.3 et v5.2

**Commande test** :
```bash
python tests/live/test_live_projects.py -v
```

**Score attendu** : 3/3 (100%)

---

## 📊 MÉTRIQUES ATTENDUES

**Avant corrections** :
- ❌ MAX_TOKENS : 4 occurrences
- ❌ Parsing échoué : 7 occurrences
- ❌ Validation inutile : 3/3 tests
- ❌ Score : 2/3 (67%)

**Après corrections** :
- ✅ MAX_TOKENS : 0 occurrence
- ✅ Parsing échoué : 0 occurrence
- ✅ Validation inutile : 0/3 tests
- ✅ Score : 3/3 (100%)

---

## ⚠️ POINTS D'ATTENTION

1. **MAX_TOKENS=8192** : CRITIQUE pour CODEUR (ne pas oublier)
2. **Format strict** : Ligne vide obligatoire après chemin fichier
3. **Noms exacts** : JARVIS_Maître doit spécifier noms exacts dans instructions
4. **Exception TEST** : Vérifier que section est bien en haut du prompt

---

## 📝 NOTES DE DÉPLOIEMENT

**Date déploiement** : _________  
**Déployé par** : _________  
**Tests validés** : ☐ Oui ☐ Non  
**Score tests live** : ___/3  
**Problèmes rencontrés** : _________

---

**Document créé le** : 7 mars 2026  
**Auteur** : Cascade (analyse logs + corrections)  
**Statut** : WORK (à archiver après déploiement réussi)
