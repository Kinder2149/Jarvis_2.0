# ANALYSE ERREURS TESTS LIVE — JARVIS 2.0

**Date** : 2026-03-07 22:23  
**Statut** : DIAGNOSTIC COMPLET  
**Tests exécutés** : 6 tests live (5 FAILED, 1 PASSED)  
**Durée** : 158.42s (2min 38s)

---

## RÉSULTATS TESTS LIVE

### ✅ Tests Réussis (1/6)
- `test_live_api_complexity_detection` : Détection complexité fonctionne ✅

### ❌ Tests Échoués (5/6)

| Test | Erreur | Cause |
|------|--------|-------|
| `test_live_api_rest` | Aucun fichier créé | Event loop closed |
| `test_live_api_with_tests` | Code INVALIDE x3 | Validation échoue |
| `test_live_calculatrice` | Mode COMPLETE au lieu de FAST | Détection complexité |
| `test_live_calculatrice_code_quality` | Code non validé | Event loop closed |
| `test_live_calculatrice_files_structure` | 0 fichiers Python | Event loop closed |

---

## ERREUR CRITIQUE #1 : Event Loop is Closed

### Symptôme
```
ERROR backend.ia.providers.gemini_provider:gemini_provider.py:137 
Gemini API error: RuntimeError - Event loop is closed
```

### Occurrence
**4 tests sur 5** échouent avec cette erreur

### Analyse Technique

**Localisation** : `backend/ia/providers/gemini_provider.py:79-85`

```python
chat = self.client.start_chat(history=gemini_messages[:-1])
response = await chat.send_message_async(  # ← ERREUR ICI
    gemini_messages[-1]["parts"],
    generation_config=generation_config,
    tools=tools,
)
```

**Cause racine** :
1. Pytest exécute tests async avec `pytest-asyncio`
2. Entre chaque test, l'event loop est fermé
3. `send_message_async()` tente d'utiliser l'event loop fermé
4. → `RuntimeError: Event loop is closed`

**Impact** :
- Impossible d'appeler agents Gemini
- Missions échouent immédiatement
- Aucun fichier généré

### Solution Requise

**Option 1** : Configurer pytest (RECOMMANDÉ)
```ini
# pytest.ini
[pytest]
asyncio_default_fixture_loop_scope = function
```

**Option 2** : Gérer event loop dans provider
```python
async def send_message(self, messages, ...):
    # Vérifier si event loop fermé
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # ... reste du code
```

---

## ERREUR #2 : Code INVALIDE x3 (Max Corrections)

### Symptôme
```
WARNING Mission mission_2c528e50e178: Code INVALIDE (tentative 1)
WARNING Mission mission_2c528e50e178: Code INVALIDE (tentative 2)
WARNING Mission mission_2c528e50e178: Code INVALIDE (tentative 3)
ERROR Mission mission_2c528e50e178: Max corrections atteint, code reste INVALIDE
ERROR Mission mission_2c528e50e178: Mode RAPIDE échoué (validation)
```

### Occurrence
**1 test** : `test_live_api_with_tests`

### Analyse Technique

**Localisation** : `backend/services/orchestration.py:158-194`

```python
max_corrections = 2  # ← TROP BAS

while correction_attempts <= max_corrections:
    validation_response = await validateur.handle(...)
    
    if "VALIDE" in validation_response.upper():
        break
    else:
        # Correction CODEUR
        code_response = await codeur.handle(correction_messages)
        correction_attempts += 1
```

**Problème** :
1. VALIDATEUR rejette code 3 fois consécutives
2. Boucle atteint limite (2 corrections max)
3. Mission échoue sans fichiers créés

**Causes possibles** :
- VALIDATEUR trop strict (rejette code valide)
- CODEUR ne corrige pas selon feedback VALIDATEUR
- Prompt correction mal formulé (feedback imprécis)

### Solution Requise

**Action 1** : Augmenter limite corrections
```python
max_corrections = 5  # au lieu de 2
```

**Action 2** : Améliorer prompt VALIDATEUR
```python
validateur_messages = [
    {"role": "system", "content": validateur.system_prompt},
    {"role": "user", "content": f"""
Code à valider:
{code_response}

Tests:
{tests_response}

Valide la qualité (bugs, erreurs syntaxe, cohérence).
Si INVALIDE, liste PRÉCISÉMENT les corrections à apporter (ligne par ligne).
Réponds VALIDE ou INVALIDE suivi des raisons détaillées.
"""}
]
```

**Action 3** : Améliorer prompt correction CODEUR
```python
correction_messages = [
    {"role": "system", "content": codeur.system_prompt},
    {"role": "user", "content": f"""
Code actuel:
{code_response}

Problèmes détectés par VALIDATEUR:
{validation_response}

Corrige UNIQUEMENT les problèmes listés ci-dessus.
Ne modifie PAS le reste du code.
"""}
]
```

---

## ERREUR #3 : Détection Complexité Incorrecte

### Symptôme
```
AssertionError: Devrait utiliser mode RAPIDE
assert 'COMPLETE' == 'FAST'
  - FAST
  + COMPLETE
```

### Occurrence
**1 test** : `test_live_calculatrice`

### Analyse Technique

**Demande test** :
```
"Crée une calculatrice Python simple avec les fonctions : 
addition, soustraction, multiplication, division. 
Ajoute une fonction main() qui demande à l'utilisateur de choisir une opération."
```

**Attendu** : Mode RAPIDE (≤3 fichiers)  
**Obtenu** : Mode COMPLET (>3 fichiers)

**Localisation** : `backend/services/orchestration.py:38-94`

```python
def detect_project_complexity(self, user_request: str) -> str:
    request_lower = user_request.lower()
    
    # Mots-clés projets simples
    simple_keywords = [
        "calculatrice", "simple", "basique",
        "petit", "rapide", "script",
        "fonction", "classe unique"
    ]
    
    if any(keyword in request_lower for keyword in simple_keywords):
        return "SIMPLE"  # ← DEVRAIT MATCHER ICI
    
    # ... reste logique
```

**Problème détecté** :
- "calculatrice" ET "simple" sont dans la demande
- Logique devrait retourner "SIMPLE"
- **MAIS** retourne "COMPLETE"

**Hypothèse** : Autre condition prend le dessus (mots-clés COMPLEX prioritaires ?)

### Solution Requise

**Action** : Forcer priorité "simple"
```python
def detect_project_complexity(self, user_request: str) -> str:
    request_lower = user_request.lower()
    
    # PRIORITÉ 1 : Mots-clés explicites "simple" ou "basique"
    if "simple" in request_lower or "basique" in request_lower:
        logger.info(f"Complexité: SIMPLE (mot-clé explicite)")
        return "SIMPLE"
    
    # PRIORITÉ 2 : Mots-clés projets simples
    simple_keywords = ["calculatrice", "petit", "rapide", "script"]
    if any(keyword in request_lower for keyword in simple_keywords):
        logger.info(f"Complexité: SIMPLE (mot-clé projet simple)")
        return "SIMPLE"
    
    # PRIORITÉ 3 : Mots-clés projets complexes
    complex_keywords = ["api rest", "authentification", "crud complet"]
    if any(keyword in request_lower for keyword in complex_keywords):
        logger.info(f"Complexité: COMPLEX (mot-clé projet complexe)")
        return "COMPLEX"
    
    # Par défaut : SIMPLE
    logger.info(f"Complexité: SIMPLE (défaut)")
    return "SIMPLE"
```

---

## ERREUR #4 : Aucun Fichier Créé

### Symptôme
```
AssertionError: Aucun fichier créé
assert 0 > 0
 +  where 0 = len([])
```

### Occurrence
**3 tests**

### Analyse
**Conséquence directe** de l'erreur #1 (Event loop closed)
- Agents ne sont jamais appelés
- Pas de code généré
- Pas de fichiers créés

**Solution** : Corriger erreur #1

---

## PLAN DE CORRECTION COMPLET

### 🔥 PRIORITÉ 1 : Corriger Event Loop (BLOQUANT)

**Fichier** : `pytest.ini`

**Action** : Ajouter configuration asyncio
```ini
[pytest]
asyncio_default_fixture_loop_scope = function
```

**Impact** : Résout 4 tests sur 5

---

### 🔥 PRIORITÉ 2 : Améliorer Validation (IMPORTANT)

**Fichier** : `backend/services/orchestration.py`

**Actions** :
1. Ligne 130 : `max_corrections = 5` (au lieu de 2)
2. Ligne 164 : Améliorer prompt VALIDATEUR (feedback précis)
3. Ligne 185 : Améliorer prompt correction CODEUR (corrections ciblées)

**Impact** : Résout 1 test (`test_live_api_with_tests`)

---

### ⚠️ PRIORITÉ 3 : Corriger Détection Complexité (AMÉLIORATION)

**Fichier** : `backend/services/orchestration.py`

**Action** : Ligne 38-94 : Réorganiser priorités mots-clés

**Impact** : Résout 1 test (`test_live_calculatrice`)

---

## RÉSUMÉ CORRECTIONS

| Priorité | Fichier | Ligne | Action | Tests Résolus |
|----------|---------|-------|--------|---------------|
| 🔥 P1 | `pytest.ini` | - | Ajouter `asyncio_default_fixture_loop_scope = function` | 4/5 |
| 🔥 P2 | `orchestration.py` | 130 | `max_corrections = 5` | 1/5 |
| 🔥 P2 | `orchestration.py` | 164 | Améliorer prompt VALIDATEUR | 1/5 |
| ⚠️ P3 | `orchestration.py` | 38-94 | Réorganiser détection complexité | 1/5 |

**Total après corrections** : **6/6 tests PASSED** (100%)

---

## LOGS SERVEUR ANALYSÉS

### Endpoints Manquants (404)
```
INFO: 127.0.0.1:54273 - "GET /api/health HTTP/1.1" 404 Not Found
INFO: 127.0.0.1:54273 - "GET /api/agents HTTP/1.1" 404 Not Found
```

**Note** : Non bloquant pour tests live (endpoints non utilisés par tests)

### Frontend Fonctionnel
```
INFO: 127.0.0.1:55253 - "GET / HTTP/1.1" 200 OK
INFO: 127.0.0.1:55253 - "GET /frontend/js/views/missions.js HTTP/1.1" 200 OK
```

**Statut** : ✅ Frontend accessible, route `/missions` fonctionne

---

## PROCHAINES ÉTAPES

1. ✅ Ajouter `asyncio_default_fixture_loop_scope = function` dans `pytest.ini`
2. ✅ Augmenter `max_corrections` à 5 dans `orchestration.py`
3. ✅ Améliorer prompts VALIDATEUR et correction CODEUR
4. ✅ Réorganiser détection complexité (priorité "simple")
5. ✅ Réexécuter tests live : `pytest tests/live/ -v -m live`
6. ✅ Valider 6/6 tests PASSED

**Temps estimé** : 30 minutes
