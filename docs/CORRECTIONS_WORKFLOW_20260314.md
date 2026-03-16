# Corrections Workflow 5 Agents - 14/03/2026

## Problème identifié

Le workflow 5 agents ne se déclenchait pas après la réponse de JARVIS_Maître contenant `[DEMANDE_CODE_CODEUR: ...]`.

### Symptômes
- L'IA répondait avec le texte de délégation mais rien ne se passait ensuite
- Aucun fichier créé
- Aucun log visible dans la console backend
- Pas de feedback visuel dans le frontend

### Cause racine

**`process_response()` en mode passthrough** (`@backend/services/orchestration.py:864-894`)

La méthode retournait simplement la réponse sans traitement :
```python
# TODO Phase 6.2-6.3 : Implémenter détection délégation et orchestration
# Pour l'instant, mode passthrough (compatibilité)
logger.info(f"Orchestration: process_response appelé pour session {session_id}")

return response, []
```

---

## Corrections appliquées

### 1. Détection et traitement de `[DEMANDE_CODE_CODEUR: ...]`

**Fichier** : `backend/services/orchestration.py`

**Changements** :
- Ajout regex pour détecter `[DEMANDE_CODE_CODEUR: ...]`
- Extraction de la demande utilisateur depuis le marqueur
- Déclenchement automatique de `start_mission()`
- Enrichissement de la réponse avec infos mission (ID, complexité, mode)

**Code** :
```python
delegation_pattern = r'\[DEMANDE_CODE_CODEUR:\s*(.*?)\]'
match = re.search(delegation_pattern, response, re.DOTALL)

if match:
    user_request = match.group(1).strip()
    mission_result = await self.start_mission(
        user_request=user_request,
        project_name=project_name,
        project_path=project_path
    )
```

### 2. Logs détaillés du workflow

**Fichier** : `backend/services/orchestration.py`

**Ajouts** :
- Séparateurs visuels pour chaque étape (`========== ÉTAPE X/3 ==========`)
- Logs avant/après chaque appel agent (CODEUR, TESTEUR, VALIDATEUR)
- Aperçu des réponses (200 premiers caractères)
- Logs de parsing et écriture fichiers
- Émojis pour faciliter la lecture (✅, ❌, ⚙️)

**Exemple** :
```
Mission mission_abc123: ========== ÉTAPE 1/3 : CODEUR ==========
Mission mission_abc123: Appel CODEUR pour génération code
Mission mission_abc123: CODEUR réponse reçue (3542 chars)
Mission mission_abc123: Aperçu réponse CODEUR: # backend/main.py...
```

### 3. Composant frontend WorkflowMonitor

**Fichiers créés** :
- `frontend/js/components/workflow-monitor.js`
- `frontend/css/workflow-monitor.css`

**Fonctionnalités** :
- Affichage en temps réel de l'état de la mission
- Polling automatique toutes les 2 secondes
- Progression visuelle (Architecture → Code → Tests)
- Liste des fichiers créés/modifiés
- Affichage des erreurs
- Positionnement fixe en bas à droite

**Intégration** :
- Importé dans `chat.js`
- Détection automatique des délégations dans la réponse API
- Démarrage automatique du monitoring si `mission_id` présent

---

## Fichiers modifiés

| Fichier | Modifications |
|---------|---------------|
| `backend/services/orchestration.py` | Détection délégation + logs détaillés |
| `frontend/js/components/chat.js` | Intégration WorkflowMonitor |
| `frontend/index.html` | Import CSS WorkflowMonitor |
| `frontend/js/components/workflow-monitor.js` | **NOUVEAU** |
| `frontend/css/workflow-monitor.css` | **NOUVEAU** |

---

## Guide de test

### Prérequis
1. Serveur JARVIS démarré : `.\start_jarvis_complete.ps1`
2. Projet créé dans l'interface
3. Conversation ouverte avec JARVIS_Maître

### Scénario de test

**1. Créer un projet simple**
```
Projet : "Todo App"
Chemin : C:\DEV\PROJETS\test_todo
```

**2. Envoyer une demande de mission**
```
MISSION : Création d'un petit outil utile

Je veux créer une petite application simple qui permet de gérer une liste de tâches quotidiennes.

Fonctionnalités attendues :
- ajouter une tâche
- marquer une tâche comme terminée
- supprimer une tâche
- voir toutes les tâches

Contraintes :
- application simple
- utilisable facilement
- données sauvegardées

Je veux que tu :
1. analyses le besoin
2. proposes une architecture
3. attendes ma validation
4. génères le projet complet
5. crées les tests nécessaires
6. valides la cohérence globale

Je veux un projet **simple mais propre et complet**.

Important :
ne me pose des questions que si c'est réellement nécessaire.
Sinon prends les décisions techniques adaptées.

Objectif :
créer un petit projet complet prêt à fonctionner.
```

**3. Valider la réponse de JARVIS_Maître**

JARVIS_Maître devrait répondre avec :
- Analyse du besoin
- Proposition d'architecture
- `[DEMANDE_CODE_CODEUR: ...]` à la fin

**4. Vérifier le déclenchement du workflow**

✅ **Logs backend attendus** :
```
Orchestration: DEMANDE_CODE_CODEUR détectée pour session <id>
Orchestration: Démarrage mission pour projet 'Todo App'
Mission mission_xxx: ========== ÉTAPE 1/3 : CODEUR ==========
Mission mission_xxx: Appel CODEUR pour génération code
...
```

✅ **Frontend attendu** :
- Message enrichi avec infos mission
- WorkflowMonitor apparaît en bas à droite
- Progression visible (⚙️ Code en cours)
- Polling automatique toutes les 2s

**5. Vérifier la finalisation**

✅ **Logs backend attendus** :
```
Mission mission_xxx: ✅ Code VALIDÉ par VALIDATEUR
Mission mission_xxx: Écriture fichiers code sur disque
Mission mission_xxx: ✅ 5 fichiers créés, 0 mis à jour
Mission mission_xxx: ========== MODE RAPIDE COMPLÉTÉ AVEC SUCCÈS ==========
```

✅ **Frontend attendu** :
- WorkflowMonitor affiche "✅ Mission complétée avec succès !"
- Liste des fichiers créés visible
- Polling s'arrête automatiquement

**6. Vérifier les fichiers créés**

Naviguer vers `C:\DEV\PROJETS\test_todo` et vérifier :
- Structure projet conforme
- Fichiers code présents
- Fichiers tests présents
- `requirements.txt` présent
- `README.md` présent

---

## Points d'attention

### Logs backend
- Surveiller la console PowerShell pour les logs détaillés
- Vérifier que chaque étape est loggée (CODEUR, TESTEUR, VALIDATEUR)
- Vérifier les aperçus de réponses (200 premiers chars)

### Frontend
- WorkflowMonitor doit apparaître automatiquement
- Polling doit se faire toutes les 2 secondes
- Progression doit être mise à jour en temps réel
- Monitoring doit s'arrêter quand mission terminée

### Erreurs possibles

**1. WorkflowMonitor ne s'affiche pas**
- Vérifier que `data.delegations` est bien présent dans la réponse API
- Vérifier que `delegation.mission_id` existe
- Vérifier la console navigateur pour erreurs JS

**2. Logs backend manquants**
- Vérifier que `process_response()` est bien appelé
- Vérifier que le regex détecte bien `[DEMANDE_CODE_CODEUR: ...]`
- Vérifier que `project_path` est bien fourni

**3. Fichiers non créés**
- Vérifier les logs de parsing (`CodeParser.parse_and_write`)
- Vérifier les permissions d'écriture sur le dossier projet
- Vérifier que la validation a réussi (VALID vs INVALID)

---

## Améliorations futures

### Court terme
1. Ajouter SSE (Server-Sent Events) pour streaming temps réel au lieu de polling
2. Afficher les logs détaillés dans WorkflowMonitor (pas seulement l'état)
3. Permettre d'annuler une mission en cours

### Moyen terme
1. Historique des missions dans l'interface
2. Replay d'une mission échouée
3. Notifications navigateur quand mission terminée

### Long terme
1. Visualisation graphique du workflow (diagramme de flux)
2. Métriques de performance (temps par agent, tokens utilisés)
3. Export des logs de mission en JSON/Markdown

---

## Conclusion

Les corrections appliquées résolvent le problème de workflow bloqué en :
1. **Détectant** les délégations dans `process_response()`
2. **Déclenchant** automatiquement le workflow 5 agents
3. **Loggant** chaque étape de manière détaillée
4. **Affichant** l'état en temps réel dans le frontend

Le workflow est maintenant **opérationnel** et **observable**.
