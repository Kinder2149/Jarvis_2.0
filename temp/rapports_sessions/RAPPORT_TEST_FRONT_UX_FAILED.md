# RAPPORT — Tests FRONT UX FAILED

**Date :** 2026-04-18  
**Fichier :** `tests/test_front_ux.py`  
**Résultat :** 16 passed, 2 skipped, **5 FAILED**

---

## FAILED 1 : FRONT-01 - test_regression_waiting_validation_toujours_fonctionnel

**Erreur :**
```
AssertionError: Zone validation masquée pour WAITING_VALIDATION (régression FRONT-01)
```

**Cause :**
`frontend/assets/js/module-code.js` ligne 235 :
```javascript
if (!waitingStep || waitingStep.requires_validation !== 1) {
  actionZone.style.display = 'none';
  return;
}
```

**Diagnostic :**
La session WAITING_VALIDATION existe, mais le step n'a probablement pas `requires_validation = 1`.

**Solution :**
Vérifier dans la DB si les steps WAITING_VALIDATION ont bien `requires_validation = 1`. Si non, c'est un problème de données de test, pas de code.

**Action recommandée :**
Modifier le test pour vérifier que `waitingStep.requires_validation === 1` avant d'asserter la visibilité, OU créer une session de test avec un step WAITING_VALIDATION valide.

---

## FAILED 2 : FRONT-02 - test_atelier_charge_sans_erreur_js

**Erreur :**
```
AssertionError: #page-atelier absent
```

**Cause :**
Le test cherche `#page-atelier` mais `atelier.html` n'a pas cet ID. Les IDs présents sont :
- `#app-layout`
- `#sidebar`
- `#main-content`
- `#view-prospects`
- `#view-pipeline`
- `#kanban-board`

**Solution :**
Modifier le test pour chercher un ID existant, par exemple `#view-prospects` ou `#kanban-board`.

**Action recommandée :**
```python
assert page.query_selector("#view-prospects") is not None, "#view-prospects absent"
```

---

## FAILED 3 : FRONT-04 - test_icones_statut_presentes_dans_kanban

**Erreur :**
```
AssertionError: Aucune icône de statut session dans le kanban.
Icônes attendues : ['⏸️', '✅', '❌', '⚙️', '⛔'].
```

**Cause :**
La fonction `getSessionIndicator()` est appelée (ligne 119 de `atelier.js`), mais retourne probablement une chaîne vide pour les prospects testés.

**Diagnostic :**
Les 3 prospects en DB ont probablement des `session_status` qui ne correspondent pas aux valeurs attendues, ou `getSessionIndicator()` retourne vide.

**Vérification nécessaire :**
```python
r = requests.get("http://localhost:8000/api/atelier/prospects")
for p in r.json():
    print(f"Prospect {p['id']}: session_status={p.get('session_status')}")
```

**Solution :**
1. Vérifier que les prospects ont bien des `session_status` non-null
2. Vérifier que `getSessionIndicator()` retourne bien des icônes pour ces statuts
3. Si les données sont absentes, le test devrait skip (déjà le cas si aucun prospect avec session)

**Action recommandée :**
Ajouter un log dans le test pour afficher les `session_status` des prospects avant d'asserter, OU accepter que ce test skip si aucun prospect n'a de session active.

---

## FAILED 4 : FRONT-06 - test_nouveau_chat_sans_modal

**Erreur :**
```
AssertionError: Modal ouvert après clic 'Nouveau Chat' depuis project.html —
FRONT-06 exige un redirect direct sans modal
```

**Cause probable :**
Le test détecte `.modal-overlay` présent dans le DOM. Deux possibilités :
1. Un toast de confirmation est affiché (qui utilise `.modal-overlay`)
2. La fonction `createNewChat()` affiche effectivement une modal d'erreur

**Vérification :**
`frontend/assets/js/project.js` ligne 236-253 :
```javascript
async function createNewChat() {
  try {
    const conv = await window.API.createConversation({
      project_id: parseInt(projectId),
      title: 'Nouvelle conversation'
    });
    location.href = `chat.html?id=${conv.id}&project_id=${projectId}`;
  } catch (error) {
    console.error('Erreur création chat:', error);
    if (window.showToast) window.showToast('Erreur création chat', 'error');
  }
}
```

**Diagnostic :**
Le code ne crée pas de modal. Le test détecte probablement un élément `.modal-overlay` qui existe déjà dans le DOM (même masqué).

**Solution :**
Modifier le test pour vérifier que la modal est **visible** (pas juste présente) :
```python
modal = page.query_selector(".modal-overlay")
if modal:
    is_visible = modal.evaluate("el => el.style.display !== 'none'")
    assert not is_visible, "Modal visible après clic 'Nouveau Chat'"
```

**Action recommandée :**
Corriger le test pour vérifier la visibilité, pas la présence.

---

## FAILED 5 : FRONT-06 - test_nouveau_module_modal_projet_prerempli

**Erreur :**
```
AssertionError: Select projet non désactivé — le projet courant doit être pré-rempli et grisé (FRONT-06)
```

**Cause :**
Le select `#modal-module-project` n'est pas désactivé après ouverture de la modal.

**Vérification :**
`frontend/assets/js/sidebar.js` - fonction `handleNewModulePreset()` (FRONT-01) :
Cette fonction devrait désactiver le select projet quand appelée avec un `projectId` pré-rempli.

**Diagnostic :**
Soit `handleNewModulePreset()` ne désactive pas le select, soit elle n'est pas appelée (fallback vers `handleNewModule()`).

**Vérification nécessaire :**
Lire `sidebar.js` pour voir si `handleNewModulePreset()` désactive bien le select :
```javascript
const projectSelect = document.getElementById('modal-module-project');
if (presetProjectId) {
  projectSelect.value = presetProjectId;
  projectSelect.disabled = true; // ← Cette ligne doit être présente
}
```

**Action recommandée :**
1. Vérifier que `handleNewModulePreset()` existe et désactive le select
2. Si absent, ajouter `projectSelect.disabled = true;` dans la fonction
3. Si la fonction n'existe pas, c'est que FRONT-01 n'a pas été complètement implémenté

---

## SYNTHÈSE

**Tests à corriger dans test_front_ux.py (2) :**
1. FAILED 2 : Changer `#page-atelier` → `#view-prospects`
2. FAILED 4 : Vérifier visibilité modal, pas présence

**Tests nécessitant vérification données (2) :**
3. FAILED 1 : Vérifier que session WAITING_VALIDATION a `requires_validation = 1`
4. FAILED 3 : Vérifier que prospects ont `session_status` non-null

**Code à corriger dans sidebar.js (1) :**
5. FAILED 5 : Ajouter `projectSelect.disabled = true` dans `handleNewModulePreset()`

---

## DÉCISION REQUISE

**Option A : Corriger les tests uniquement (rapide)**
- Modifier FAILED 2 et FAILED 4 dans `test_front_ux.py`
- Accepter que FAILED 1, 3, 5 skip si données absentes
- **Temps estimé :** 10 min

**Option B : Corriger tests + code (complet)**
- Corriger FAILED 2 et FAILED 4 dans tests
- Corriger FAILED 5 dans `sidebar.js` (ajouter `disabled = true`)
- Vérifier/corriger données pour FAILED 1 et 3
- **Temps estimé :** 30 min

**Recommandation :**
Option B — Les corrections de code sont mineures et garantissent que FRONT-01 et FRONT-06 sont complets.
