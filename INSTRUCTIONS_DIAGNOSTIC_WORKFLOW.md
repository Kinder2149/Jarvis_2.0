# 🔍 Diagnostic du Workflow de Délégation - Instructions

## ✅ Modifications effectuées

J'ai ajouté des **logs de diagnostic détaillés** pour identifier pourquoi JARVIS_Maître génère du code directement au lieu de déléguer.

### 1. Logs de vérification du prompt (`backend/agents/jarvis_maitre.py`)

Au démarrage de JARVIS_Maître, le système vérifie maintenant :
- ✅ Si le prompt contient `DEMANDE_CODE_CODEUR_SIMPLE`
- ✅ Si le prompt contient `DEMANDE_CODE_CODEUR_COMPLEX`
- ✅ Si le prompt contient la section `ÉTAPE DE VALIDATION DU WORKFLOW`

### 2. Logs d'analyse de la réponse (`backend/agents/base_agent.py`)

Quand JARVIS_Maître génère une réponse, le système vérifie :
- ✅ Si la réponse contient `[DEMANDE_CODE_CODEUR_SIMPLE:`
- ✅ Si la réponse contient `[DEMANDE_CODE_CODEUR_COMPLEX:`
- ⚠️ Si la réponse contient l'ancien marqueur `[DEMANDE_CODE_CODEUR:` (sans SIMPLE/COMPLEX)
- ❌ Si la réponse ne contient aucun marqueur

## 🚀 Prochaines étapes

### Étape 1 : Redémarrer le serveur

**IMPORTANT** : Les modifications du prompt ne sont chargées qu'au démarrage du serveur.

```powershell
# Arrêter le serveur actuel (Ctrl+C)
# Puis relancer :
.\start_jarvis_complete.ps1
```

### Étape 2 : Vérifier les logs au démarrage

Lors du démarrage, vous devriez voir dans les logs :

```
INFO - JARVIS_Maître prompt chargé (XXXX chars)
INFO - ✅ Prompt contient DEMANDE_CODE_CODEUR_SIMPLE
INFO - ✅ Prompt contient DEMANDE_CODE_CODEUR_COMPLEX
INFO - ✅ Prompt contient section 'ÉTAPE DE VALIDATION DU WORKFLOW'
```

**Si vous voyez des ❌**, cela signifie que le prompt n'a pas été correctement chargé.

### Étape 3 : Tester avec une nouvelle conversation

1. Créer une **nouvelle conversation** dans l'interface
2. Demander : "Je veux créer une petite application de gestion de tâches"
3. Suivre le dialogue jusqu'à la validation
4. **Observer les logs** pour voir quel marqueur est généré

### Étape 4 : Analyser les logs de la réponse

Quand JARVIS_Maître répond après votre validation, vous devriez voir :

**Cas 1 : Succès** ✅
```
INFO - Agent JARVIS_Maître - Réponse brute (XXX chars)
INFO - ✅ Réponse contient [DEMANDE_CODE_CODEUR_SIMPLE:
```

**Cas 2 : Ancien marqueur** ⚠️
```
INFO - Agent JARVIS_Maître - Réponse brute (XXX chars)
WARNING - ⚠️ Réponse contient ancien marqueur [DEMANDE_CODE_CODEUR: (sans _SIMPLE/_COMPLEX)
```

**Cas 3 : Aucun marqueur** ❌
```
INFO - Agent JARVIS_Maître - Réponse brute (XXX chars)
WARNING - ❌ Réponse ne contient AUCUN marqueur de délégation
```

## 🔧 Solutions selon le diagnostic

### Si le prompt n'est pas chargé (❌ au démarrage)

**Problème** : Le fichier `config_agents/JARVIS_MAITRE.md` n'est pas trouvé ou mal formaté.

**Solution** :
1. Vérifier que le fichier existe : `config_agents/JARVIS_MAITRE.md`
2. Vérifier les permissions de lecture
3. Redémarrer le serveur

### Si Gemini génère l'ancien marqueur (⚠️)

**Problème** : Gemini n'a pas compris les nouvelles instructions ou les ignore.

**Solutions** :
1. **Réduire la température** : Modifier `backend/agents/agent_config.py` ligne 89
   ```python
   "temperature": 0.1,  # Au lieu de 0.3
   ```

2. **Renforcer le prompt** : Simplifier les instructions dans `config_agents/JARVIS_MAITRE.md`

3. **Changer de modèle** : Tester avec `gemini-2.0-flash-exp` dans `.env`
   ```
   JARVIS_MAITRE_MODEL=gemini-2.0-flash-exp
   ```

### Si Gemini ne génère aucun marqueur (❌)

**Problème** : Gemini génère du code directement malgré les instructions.

**Solutions** :
1. **Ajouter une détection automatique** dans `backend/api.py` :
   - Si l'utilisateur dit "je valide" après une proposition d'architecture
   - Injecter automatiquement le marqueur `[DEMANDE_CODE_CODEUR_SIMPLE: ...]`

2. **Bloquer la génération de code** :
   - Vérifier si la réponse contient des blocs de code (```python)
   - Si oui, redemander à JARVIS_Maître de déléguer au lieu de générer

## 📊 Rapport à fournir

Après le test, merci de me fournir :

1. **Les logs au démarrage** (section JARVIS_Maître prompt)
2. **Les logs de la réponse** (section "Réponse brute")
3. **La conversation complète** (ce que vous avez demandé et ce que JARVIS a répondu)

Avec ces informations, je pourrai :
- Identifier la cause exacte du problème
- Implémenter la solution appropriée (Phase 3 ou 4 du plan)
- Tester et valider la correction

## 🎯 Objectif final

Après correction, le workflow devrait être :

1. Utilisateur : "Je veux créer une app de gestion de tâches"
2. JARVIS_Maître : Analyse et propose une architecture
3. Utilisateur : "Je valide"
4. JARVIS_Maître : "Je propose un workflow SIMPLE car ≤3 fichiers. Validez-vous ?"
5. Utilisateur : "Je valide"
6. JARVIS_Maître : `[DEMANDE_CODE_CODEUR_SIMPLE: ...]`
7. Backend : Déclenche le workflow automatiquement
8. Fichiers créés dans le projet
9. WorkflowMonitor affiche la progression

---

**Note** : Les modifications sont déjà en place. Il suffit de redémarrer le serveur et de tester avec une nouvelle conversation.
