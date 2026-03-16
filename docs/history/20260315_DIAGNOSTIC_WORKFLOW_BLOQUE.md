# Diagnostic Workflow Bloqué - 15 Mars 2026

**Date** : 15 mars 2026 13:15  
**Problème** : Mission créée mais workflow ne s'exécute pas complètement

---

## ✅ Corrections Appliquées (Fonctionnelles)

### 1. Boucle Function Calls Corrigée
**Fichier** : `backend/api.py`  
**Changement** : Désactivation `function_executor` pour JARVIS_Maître en mode projet

```python
# AVANT : JARVIS_Maître recevait function_executor → boucle get_project_structure
if conversation["project_id"]:
    function_executor = FunctionExecutor(...)

# APRÈS : function_executor désactivé pour JARVIS_Maître
if conversation["project_id"]:
    if conversation["agent_id"] != "JARVIS_Maître":
        function_executor = FunctionExecutor(...)
```

**Résultat** : ✅ JARVIS_Maître génère le marqueur `[DEMANDE_CODE_CODEUR:]` correctement

---

### 2. Log Vérification Marqueur Corrigé
**Fichier** : `backend/ia/providers/gemini_provider.py`  
**Changement** : Vérification limitée à JARVIS_Maître uniquement

```python
# AVANT : Vérification pour tous les agents (incorrect)
if "[DEMANDE_CODE_CODEUR:" in system_prompt:
    logger.info("✅ System prompt contient [DEMANDE_CODE_CODEUR:")

# APRÈS : Vérification uniquement pour JARVIS_Maître
if "JARVIS_Maître" in system_prompt:
    if "[DEMANDE_CODE_CODEUR:" in system_prompt:
        logger.info("✅ JARVIS_Maître prompt contient [DEMANDE_CODE_CODEUR:")
```

**Résultat** : ✅ Logs corrects, pas de warning erroné pour ARCHITECTE

---

## ❌ Problème Actuel : Workflow Asynchrone Bloqué

### Logs Serveur

```
✅ [ORCHESTRATION] Marqueur [DEMANDE_CODE_CODEUR:] détecté
🚀 [ORCHESTRATION] Démarrage mission pour projet 'test_calculatrice_audit_20260315_131317'
📋 [ORCHESTRATION] Mission mission_86d9923d62e1 créée
```

**Observation** :
- ✅ Mission créée
- ❌ Aucun log ARCHITECTE
- ❌ Workflow ne démarre pas

---

### Analyse Code Orchestration

**Fichier** : `backend/services/orchestration.py`

**Méthode `start_mission`** (ligne 468-518) :
```python
async def start_mission(...):
    # 1. Vérifier projet existant
    # 2. Créer mission
    mission = self.mission_manager.create_mission(...)
    
    print(f"📋 [ORCHESTRATION] Mission {mission_id} créée")
    
    # 3. Exécuter workflow unique (toujours COMPLET)
    result = await self.execute_complete_mode(mission, user_request, project_path)
    
    return {"success": True, "mission_id": mission_id, ...}
```

**Méthode `execute_complete_mode`** (ligne 108-204) :
```python
async def execute_complete_mode(...):
    # 1. ARCHITECTE : Propose architecture
    architecte = get_agent("ARCHITECTE")
    architecture_response = await architecte.handle(...)
    
    # 2. Demander validation USER
    mission.request_validation("architecture", {...})
    
    # Note: Le workflow s'arrête ici en attendant validation USER
    # L'API devra appeler continue_complete_mode() après validation
    
    return {
        "requires_user_validation": True,
        "user_message": "⏸️ Le workflow est en pause..."
    }
```

---

## 🔍 Cause Racine Identifiée

**Le workflow est ASYNCHRONE et s'arrête intentionnellement** après ARCHITECTE pour attendre validation utilisateur.

**Flux actuel** :
1. ✅ JARVIS_Maître génère `[DEMANDE_CODE_CODEUR:]`
2. ✅ `process_response()` détecte marqueur
3. ✅ `start_mission()` créé mission
4. ✅ `execute_complete_mode()` appelé
5. ⏸️ **ARCHITECTE génère architecture**
6. ⏸️ **Workflow se met en PAUSE** (`VALIDATING`)
7. ❌ **Attente validation USER** (jamais reçue dans le test)
8. ❌ **CODEUR jamais appelé**

---

## 🎯 Pourquoi Aucun Log ARCHITECTE ?

**Hypothèse #1 : Exécution Asynchrone Non Attendue**

Le workflow s'exécute en **arrière-plan** (async) mais le test n'attend que 5 secondes.

**Vérification nécessaire** :
- Vérifier si `start_mission()` est bien `await`é
- Vérifier si l'exécution est vraiment asynchrone ou bloquante

**Code `process_response`** (ligne 591) :
```python
mission_result = await self.start_mission(...)  # ✅ await présent
```

**Donc `start_mission` devrait bloquer jusqu'à ce que ARCHITECTE réponde.**

---

**Hypothèse #2 : Exception Silencieuse**

Une exception se produit dans `execute_complete_mode` mais n'est pas loggée.

**Vérification** : Ajouter logs détaillés dans `execute_complete_mode`

---

**Hypothèse #3 : Configuration API Keys**

Les agents utilisent-ils bien leurs propres API keys ?

**Vérification nécessaire** :
- Vérifier `.env` pour chaque agent
- Vérifier `agent_config.py` pour mapping modèles

---

## 📋 Configuration API Keys par Agent

**Question utilisateur** : "Est ce que chaque agent utilise bien sa clef api propre ?"

**Réponse** : **NON**, tous les agents utilisent la **même API key Gemini**.

**Fichier** : `backend/ia/providers/gemini_provider.py`

```python
class GeminiProvider(BaseProvider):
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.api_key = os.getenv("GEMINI_API_KEY")  # ← Même clé pour tous
        self.model_name = model_name
```

**Fichier** : `backend/agents/agent_config.py`

```python
AGENT_CONFIGS = {
    "JARVIS_Maître": {
        "model": os.getenv("JARVIS_MAITRE_MODEL", "gemini-2.5-pro"),
        # Pas de clé API spécifique
    },
    "ARCHITECTE": {
        "model": os.getenv("ARCHITECTE_MODEL", "gemini-2.5-pro"),
        # Pas de clé API spécifique
    },
    # ...
}
```

**Conclusion** : Tous les agents utilisent `GEMINI_API_KEY` du `.env`. Chaque agent peut utiliser un **modèle différent** mais la **même clé API**.

---

## 🔧 Solutions Proposées

### Solution #1 : Ajouter Logs Détaillés

Ajouter logs dans `execute_complete_mode` pour voir où ça bloque :

```python
async def execute_complete_mode(...):
    logger.info(f"🚀 execute_complete_mode démarré pour mission {mission.mission_id}")
    
    try:
        logger.info(f"📞 Appel ARCHITECTE...")
        architecte = get_agent("ARCHITECTE")
        logger.info(f"✅ ARCHITECTE récupéré : {architecte.name}")
        
        architecture_response = await architecte.handle(...)
        logger.info(f"✅ ARCHITECTE réponse reçue ({len(architecture_response)} chars)")
        
        # ...
```

---

### Solution #2 : Vérifier Exécution Réelle

Vérifier si `execute_complete_mode` est vraiment appelé en ajoutant un print au début :

```python
async def execute_complete_mode(...):
    print(f"🚀 [EXECUTE_COMPLETE_MODE] Démarré pour mission {mission.mission_id}")
    # ...
```

---

### Solution #3 : Test avec Validation Automatique

Modifier le test pour valider automatiquement l'architecture :

```python
# Après attente 5 secondes
# Récupérer état mission
response = await client.get(f"{API_URL}/missions/{mission_id}")
mission_status = response.json()

if mission_status["status"] == "VALIDATING":
    # Valider automatiquement
    await client.post(
        f"{API_URL}/missions/{mission_id}/validate",
        json={"approved": True}
    )
    
    # Attendre exécution CODEUR
    await asyncio.sleep(30)
```

---

## 🎯 Prochaines Actions

1. **Ajouter logs détaillés** dans `execute_complete_mode`
2. **Redémarrer serveur** et relancer test
3. **Analyser logs** pour voir où ça bloque
4. **Si workflow bloqué en VALIDATING** : Modifier test pour valider automatiquement
5. **Si exception** : Corriger l'erreur

---

**Date rapport** : 15 mars 2026 13:20  
**Statut** : Investigation en cours
