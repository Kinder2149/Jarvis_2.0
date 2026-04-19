# TEST-03 — Run complet + analyse + rapport final

> Lire PROJET_CONTEXTE.md en entier avant toute action.
> Prérequis : TEST-01 ✅ + TEST-02 ✅ (tests écrits, 0 FAILED)

---

## Objectif

Lancer la suite complète de tests, analyser les résultats, corriger les échecs
mineurs, et produire un rapport final qui sera transmis à Claude.

---

## ÉTAPE 1 — Run complet

Lancer dans cet ordre :

```bash
# 1. Tests backend (base stable)
pytest tests/ --ignore=tests/live --ignore=tests/frontend -q 2>&1

# 2. Tests E2E frontend V2 (existants)
pytest tests/test_frontend_e2e.py -v 2>&1

# 3. Tests E2E UX Refactoring (nouveaux)
pytest tests/test_front_ux.py -v 2>&1

# 4. Test Atelier standalone (non-pytest)
python tests/test_atelier_e2e.py 2>&1
```

Collecter les résultats de chaque commande.

---

## ÉTAPE 2 — Triage des résultats

Pour chaque test FAILED :

### Catégorie A — Correction immédiate (< 15 min, 1 fichier)

Exemples :
- Sélecteur CSS/ID légèrement différent de celui attendu
- Texte du message différent mais fonctionnellement correct
- Timing trop court (augmenter `wait_for_timeout`)

Action : corriger dans `tests/test_front_ux.py` et relancer.

### Catégorie B — Bug dans le frontend à corriger (1-2 fichiers)

Exemples :
- La zone CTA ne s'affiche pas pour COMPLETED (FRONT-01 non appliqué)
- session_status absent de la réponse API (FRONT-03 non appliqué)
- Banner .waiting-banner absent du CSS (FRONT-05 non appliqué)

Action : corriger dans le fichier frontend concerné, relancer les tests.

### Catégorie C — Problème architectural ou ambigu

Exemples :
- Comportement différent de ce qui était spécifié dans les missions FRONT
- Conflit entre deux missions
- Test qui nécessite une refonte de la logique

Action : **STOP — documenter précisément et revenir vers Claude**.

---

## ÉTAPE 3 — Vérification finale après corrections

```bash
# Run complet post-corrections
pytest tests/ --ignore=tests/live --ignore=tests/frontend -q
pytest tests/test_frontend_e2e.py -q
pytest tests/test_front_ux.py -v
```

Cible :
- Backend : **162+ passed, 0 failed**
- E2E V2 : **41 passed** (skip OK)
- E2E UX : **0 FAILED** (skip OK pour tests sans données)

---

## ÉTAPE 4 — Mise à jour documentation

### PROJET_CONTEXTE.md — section 4

Déplacer dans **✅ Stables** :
```
- UX Refactoring Frontend (FRONT-01 à 06) : 6 corrections UX validées par tests E2E
- Tests E2E UX Refactoring : tests/test_front_ux.py (N tests)
```

Mettre à jour le compteur de tests :
```
- Suite de tests : 162/162 backend + [N+41] E2E Playwright
```

Vider **🚧 En cours** (les 6 missions FRONT sont terminées).

### PROJET_CONTEXTE.md — section 8

```
**Graphify :** ☐ À mettre à jour
**Objectif :** Tests E2E UX Refactoring terminés
**Contexte :** tests/test_front_ux.py créé — [N] tests, [N] passed, [N] skipped
**Blocage :** Aucun
**Résultat attendu :** Suite de tests complète validant les 6 missions FRONT
```

### CHANGELOG.md

```
[2026-04-18] | Tests E2E UX Refactoring | Suite tests/test_front_ux.py créée : 
[N] tests couvrant FRONT-01 à 06 (CTA, badges kanban, sidebar counter, 
dashboard waiting, project inline). [N] passed, [N] skipped. | tests/test_front_ux.py
```

---

## RAPPORT FINAL (à transmettre à Claude)

```
═══════════════════════════════════════════════════════
RAPPORT TEST-03 — Run complet [date]
═══════════════════════════════════════════════════════

RÉSULTATS :
  Backend (unitaires + intégration) : [N]/162 passed  ✅/❌
  E2E Frontend V2 (existants)       : [N]/41  passed  ✅/❌
  E2E UX Refactoring (nouveaux)     : [N] passed, [N] skipped, [N] failed  ✅/❌
  Atelier standalone                : ✅/❌

CORRECTIONS APPLIQUÉES (catégorie A/B) :
  1. [description de la correction]
  2. [...]

PROBLÈMES RESTANTS (catégorie C — pour Claude) :
  → [description si applicable, sinon "Aucun"]

COUVERTURE MISSIONS FRONT :
  FRONT-01 CTA Module Code      : [N] tests — [N passed / N skipped]
  FRONT-02 CTA Atelier          : [N] tests — [N passed / N skipped]
  FRONT-03 Sidebar counter      : [N] tests — [N passed / N skipped]
  FRONT-04 Kanban badges        : [N] tests — [N passed / N skipped]
  FRONT-05 Dashboard waiting    : [N] tests — [N passed / N skipped]
  FRONT-06 Project inline       : [N] tests — [N passed / N skipped]

VERDICT GLOBAL : ✅ Suite de tests validée  /  ❌ Problèmes à résoudre
═══════════════════════════════════════════════════════
```

**Transmettre ce rapport à Claude avant toute autre action.**
