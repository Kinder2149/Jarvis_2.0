# Guide d'exécution des tests du workflow

## Tests créés

### 1. `test_orchestration_process_response.py`
**Tests unitaires pour `process_response()`**

Vérifie la détection du marqueur `[DEMANDE_CODE_CODEUR: ...]` et le déclenchement du workflow.

**Tests inclus** :
- ✅ Détection correcte du marqueur
- ✅ Pas de déclenchement sans marqueur
- ✅ Gestion des marqueurs mal formés
- ✅ Gestion de l'absence de `project_path`
- ✅ Extraction de demandes complexes
- ✅ Marqueurs multilignes
- ✅ Détection quand JARVIS_Maître génère du code directement (erreur)

**Exécution** :
```powershell
pytest tests/test_orchestration_process_response.py -v
```

---

### 2. `test_jarvis_maitre_delegation.py`
**Tests d'intégration pour JARVIS_Maître**

Vérifie que JARVIS_Maître génère le marqueur au lieu de générer du code directement.

**Tests inclus** :
- ✅ Génération du marqueur de délégation (avec mock)
- ✅ Interdiction de générer du code directement
- 🔴 **Test LIVE** : Appel réel à l'API Gemini pour vérifier le comportement réel
- 🔴 **Test LIVE** : Vérification que le prompt est bien chargé

**Exécution (sans tests live)** :
```powershell
pytest tests/test_jarvis_maitre_delegation.py -v -m "not live"
```

**Exécution (avec tests live - nécessite API key)** :
```powershell
pytest tests/test_jarvis_maitre_delegation.py -v
```

---

### 3. `test_integration_workflow_delegation.py`
**Tests d'intégration end-to-end**

Teste le flux complet : JARVIS_Maître → process_response → workflow

**Tests inclus** :
- ✅ Intégration complète avec mock
- ✅ Pas de déclenchement sans marqueur
- 🔴 **Test LIVE** : Flux complet avec appel réel à Gemini
- ✅ Extraction correcte de la demande

**Exécution (sans tests live)** :
```powershell
pytest tests/test_integration_workflow_delegation.py -v -m "not live"
```

**Exécution (avec tests live - nécessite API key)** :
```powershell
pytest tests/test_integration_workflow_delegation.py -v
```

---

## Exécution de tous les tests

### Tests unitaires et d'intégration (sans API)
```powershell
pytest tests/test_orchestration_process_response.py tests/test_jarvis_maitre_delegation.py tests/test_integration_workflow_delegation.py -v -m "not live"
```

### Tous les tests (avec tests live - nécessite API key)
```powershell
pytest tests/test_orchestration_process_response.py tests/test_jarvis_maitre_delegation.py tests/test_integration_workflow_delegation.py -v
```

### Tests live uniquement
```powershell
pytest tests/test_jarvis_maitre_delegation.py tests/test_integration_workflow_delegation.py -v -m "live"
```

---

## Interprétation des résultats

### ✅ Tous les tests passent
**Signification** : Le workflow fonctionne correctement
- `process_response()` détecte bien le marqueur
- JARVIS_Maître génère le marqueur (au moins dans les tests mockés)
- Le workflow se déclenche correctement

**Action** : Passer aux tests manuels

---

### ❌ Tests unitaires échouent
**Signification** : Problème dans `process_response()`
- La regex de détection est incorrecte
- L'extraction de la demande ne fonctionne pas
- Le déclenchement de `start_mission` est cassé

**Action** : Corriger `backend/services/orchestration.py`

---

### ❌ Tests live échouent
**Signification** : JARVIS_Maître ne génère PAS le marqueur
- Le prompt n'est pas chargé correctement
- Gemini ignore les instructions
- Le prompt est trop long ou mal structuré

**Action** :
1. Vérifier que le prompt est bien chargé
2. Réduire la température (0.3 → 0.1)
3. Simplifier le prompt
4. Envisager un autre modèle (Claude, GPT-4)

---

## Tests existants (déjà présents)

### Tests d'intégration workflow
- `tests/live/integration/test_workflow_rapide.py` : Workflow RAPIDE complet
- `tests/live/integration/test_workflow_complet.py` : Workflow COMPLET
- `tests/live/integration/test_boucle_correction.py` : Boucle de correction

**Ces tests sont OK** mais ne testent PAS la délégation depuis JARVIS_Maître.

---

## Ordre d'exécution recommandé

### 1. Tests unitaires (rapides, sans API)
```powershell
pytest tests/test_orchestration_process_response.py -v
```

**Durée** : ~5 secondes
**Si échec** : Corriger `orchestration.py` avant de continuer

---

### 2. Tests d'intégration mockés (rapides, sans API)
```powershell
pytest tests/test_jarvis_maitre_delegation.py tests/test_integration_workflow_delegation.py -v -m "not live"
```

**Durée** : ~10 secondes
**Si échec** : Vérifier les mocks et l'intégration

---

### 3. Tests live (lents, nécessite API key)
```powershell
pytest tests/test_jarvis_maitre_delegation.py::test_jarvis_maitre_delegation_live -v -s
```

**Durée** : ~30 secondes
**Si échec** : JARVIS_Maître ne délègue pas → Problème de prompt ou de modèle

---

### 4. Test live end-to-end complet
```powershell
pytest tests/test_integration_workflow_delegation.py::test_integration_live_jarvis_maitre_vers_workflow -v -s
```

**Durée** : ~1 minute
**Si échec** : Workflow complet ne fonctionne pas

---

## Résultats attendus

### Si tout fonctionne
```
test_orchestration_process_response.py::test_process_response_detecte_marqueur_codeur PASSED
test_orchestration_process_response.py::test_process_response_sans_marqueur PASSED
test_orchestration_process_response.py::test_process_response_marqueur_mal_forme PASSED
test_orchestration_process_response.py::test_process_response_sans_project_path PASSED
test_orchestration_process_response.py::test_process_response_extraction_demande_complexe PASSED
test_orchestration_process_response.py::test_process_response_marqueur_multilignes PASSED
test_orchestration_process_response.py::test_process_response_code_genere_directement PASSED

test_jarvis_maitre_delegation.py::test_jarvis_maitre_genere_marqueur_delegation PASSED
test_jarvis_maitre_delegation.py::test_jarvis_maitre_ne_genere_pas_code_direct PASSED
test_jarvis_maitre_delegation.py::test_jarvis_maitre_delegation_live PASSED
test_jarvis_maitre_delegation.py::test_jarvis_maitre_prompt_charge PASSED

test_integration_workflow_delegation.py::test_integration_delegation_complete_mock PASSED
test_integration_workflow_delegation.py::test_integration_pas_de_delegation_sans_marqueur PASSED
test_integration_workflow_delegation.py::test_integration_live_jarvis_maitre_vers_workflow PASSED
test_integration_workflow_delegation.py::test_integration_extraction_demande_correcte PASSED
```

---

## Diagnostic rapide

### Problème : Tests unitaires OK, tests live échouent
**Cause** : JARVIS_Maître ne génère pas le marqueur
**Solution** : Renforcer le prompt ou changer de modèle

### Problème : Tous les tests échouent
**Cause** : `process_response()` ne fonctionne pas
**Solution** : Vérifier la regex et l'extraction

### Problème : Tests passent mais workflow manuel ne fonctionne pas
**Cause** : Problème dans l'API ou l'interface frontend
**Solution** : Vérifier les logs backend et l'appel à `process_response()`

---

## Commandes utiles

### Exécuter un seul test
```powershell
pytest tests/test_jarvis_maitre_delegation.py::test_jarvis_maitre_delegation_live -v -s
```

### Voir les prints dans les tests
```powershell
pytest tests/test_orchestration_process_response.py -v -s
```

### Arrêter au premier échec
```powershell
pytest tests/test_orchestration_process_response.py -v -x
```

### Afficher les logs détaillés
```powershell
pytest tests/test_orchestration_process_response.py -v -s --log-cli-level=INFO
```

---

## Prochaines étapes

1. ✅ Exécuter les tests unitaires
2. ✅ Exécuter les tests d'intégration mockés
3. ✅ Exécuter les tests live
4. ✅ Si tous passent → Tests manuels
5. ❌ Si échec → Analyser les logs et corriger
