# Workflow Unique JARVIS 2.0

## Vue d'ensemble

Toutes les missions JARVIS 2.0 suivent désormais le **même workflow unique** en 6 étapes, quel que soit le type de projet.

## Architecture du Workflow

```
JARVIS_Maître → ARCHITECTE → VALIDATION USER → CODEUR → TESTEUR → VALIDATEUR
```

### Étapes Détaillées

1. **JARVIS_Maître** : Reçoit la demande utilisateur et propose une architecture
2. **ARCHITECTE** : Conçoit l'architecture détaillée du projet
3. **VALIDATION USER** : L'utilisateur valide l'architecture via le workflow monitor
4. **CODEUR** : Génère le code selon l'architecture validée
5. **TESTEUR** : Génère les tests unitaires
6. **VALIDATEUR** : Valide le code, les tests et la cohérence avec l'architecture

## Marqueur de Délégation

JARVIS_Maître utilise un **marqueur unique** pour déléguer au workflow :

```
[DEMANDE_CODE_CODEUR: description complète du projet]
```

### Format Attendu

```
[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour [description projet] :
- fichier1.py : [description précise]
- fichier2.py : [description précise]
- tests/test_fichier1.py : [description précise]
Utilise [framework], [dépendances]]
```

### ⚠️ Formats Obsolètes

Les marqueurs suivants ne sont **plus utilisés** :
- ❌ `[DEMANDE_CODE_CODEUR_SIMPLE: ...]`
- ❌ `[DEMANDE_CODE_CODEUR_COMPLEX: ...]`

## Validation Architecture

### Processus

1. **Workflow s'arrête** après l'étape ARCHITECTE
2. **Mission passe en statut** `VALIDATING`
3. **Phase devient** `VALIDATION_ARCHI`
4. **Workflow monitor affiche** :
   - Architecture proposée
   - Bouton "✅ Valider l'architecture"
5. **Utilisateur clique** sur le bouton
6. **API appelée** : `POST /api/missions/{mission_id}/continue`
7. **Workflow reprend** avec CODEUR → TESTEUR → VALIDATEUR

### Interface Utilisateur

Le workflow monitor détecte automatiquement le statut `VALIDATING` et affiche :

```
🏗️ Validation Architecture

L'ARCHITECTE a proposé l'architecture suivante :

[Architecture complète affichée]

[Bouton : ✅ Valider l'architecture]
```

## API Endpoints

### Démarrer une Mission

**Endpoint** : `POST /api/conversations/{conversation_id}/messages`

Le workflow démarre automatiquement quand JARVIS_Maître génère le marqueur `[DEMANDE_CODE_CODEUR: ...]`.

### Continuer après Validation

**Endpoint** : `POST /api/missions/{mission_id}/continue`

**Méthode** : POST

**Headers** : `Content-Type: application/json`

**Réponse** :
```json
{
  "success": true,
  "files_created": ["main.py", "storage.py", "tests/test_main.py"],
  "validation_result": "VALID"
}
```

### Obtenir le Statut d'une Mission

**Endpoint** : `GET /api/missions/{mission_id}`

**Réponse** :
```json
{
  "mission_id": "mission_abc123",
  "status": "VALIDATING",
  "current_phase": "VALIDATION_ARCHI",
  "pending_validation": {
    "type": "architecture",
    "data": {
      "architecture": "Architecture complète..."
    }
  }
}
```

## Statuts de Mission

| Statut | Description |
|--------|-------------|
| `PENDING` | Mission créée, en attente de démarrage |
| `IN_PROGRESS` | Workflow en cours d'exécution |
| `VALIDATING` | En attente de validation utilisateur |
| `COMPLETED` | Mission terminée avec succès |
| `FAILED` | Mission échouée |

## Phases de Mission

| Phase | Description |
|-------|-------------|
| `ARCHITECTURE` | ARCHITECTE conçoit l'architecture |
| `VALIDATION_ARCHI` | Attente validation utilisateur |
| `GENERATION_CODE` | CODEUR génère le code |
| `TESTS` | TESTEUR génère les tests |
| `VALIDATION` | VALIDATEUR valide tout |
| `FINALISATION` | Écriture fichiers sur disque |

## Exemple Complet

### 1. Utilisateur envoie une demande

```
MISSION : Crée une app de gestion de tâches

Fonctionnalités :
- ajouter une tâche
- lister les tâches
- marquer comme terminée
- supprimer une tâche

Contraintes : Python, JSON, pytest
```

### 2. JARVIS_Maître propose architecture

```
Voici l'architecture que je propose :

FICHIERS À CRÉER :
- main.py : classe TaskManager avec add_task(), list_tasks(), mark_done(), delete_task()
- storage.py : classe JsonStorage pour sauvegarder dans tasks.json
- tests/test_main.py : tests pytest

STRUCTURE :
Application CLI simple avec stockage JSON

TECHNOLOGIES :
- Python 3
- JSON (stockage)
- pytest (tests)

Validez-vous cette architecture ?
```

### 3. Utilisateur valide

```
Je valide
```

### 4. JARVIS_Maître génère le marqueur

```
[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour une app de gestion de tâches :
- main.py : classe TaskManager avec méthodes add_task(title, description), list_tasks(), mark_done(task_id), delete_task(task_id)
- storage.py : classe JsonStorage avec méthodes save(tasks), load() -> tasks
- tests/test_main.py : tests pytest pour toutes les méthodes
Utilise Python 3, stockage JSON, pytest]
```

### 5. Workflow démarre automatiquement

- Mission créée : `mission_abc123`
- ARCHITECTE génère architecture détaillée
- Workflow s'arrête en `VALIDATING`

### 6. Workflow monitor affiche

```
🏗️ Validation Architecture

L'ARCHITECTE a proposé l'architecture suivante :

[Architecture détaillée]

[Bouton : ✅ Valider l'architecture]
```

### 7. Utilisateur clique sur "Valider"

- API : `POST /api/missions/mission_abc123/continue`
- Workflow reprend : CODEUR → TESTEUR → VALIDATEUR
- Fichiers créés dans `projects/`

## Logs Console

Le système affiche des logs en temps réel dans la console PowerShell :

```
🔍 [ORCHESTRATION] process_response appelé - session abc123
📝 [ORCHESTRATION] Réponse (150 chars): [DEMANDE_CODE_CODEUR: Crée...
✅ [ORCHESTRATION] Marqueur [DEMANDE_CODE_CODEUR:] détecté
🚀 [ORCHESTRATION] Démarrage mission pour projet 'test_app'
📋 [ORCHESTRATION] Mission mission_abc123 créée
```

## Différences avec l'Ancien Système

| Aspect | Ancien Système | Nouveau Système |
|--------|----------------|-----------------|
| **Workflows** | SIMPLE et COMPLEX | Un seul workflow |
| **Marqueurs** | `_SIMPLE` / `_COMPLEX` | Marqueur unique |
| **Détection** | Automatique par mots-clés | N/A (un seul workflow) |
| **Architecture** | Optionnelle (SIMPLE) | Toujours présente |
| **Validation** | Optionnelle | Toujours requise |

## Avantages du Workflow Unique

1. **Simplicité** : Un seul chemin, plus facile à comprendre et maintenir
2. **Qualité** : Architecture toujours validée avant génération code
3. **Cohérence** : Tous les projets suivent le même processus
4. **Traçabilité** : Workflow clair et prévisible
5. **Flexibilité** : Même workflow pour petits et grands projets

## Dépannage

### Le workflow ne démarre pas

**Vérifier** :
1. JARVIS_Maître génère bien `[DEMANDE_CODE_CODEUR: ...]`
2. Logs console montrent `✅ [ORCHESTRATION] Marqueur détecté`
3. `project_path` est défini dans la conversation

### Le workflow monitor reste vide

**Vérifier** :
1. Mission créée : `GET /api/missions/{mission_id}`
2. Statut mission : doit être `VALIDATING`
3. Phase mission : doit être `VALIDATION_ARCHI`

### Le bouton "Valider" ne fonctionne pas

**Vérifier** :
1. Console navigateur : erreurs JavaScript
2. Endpoint `/api/missions/{id}/continue` accessible
3. Mission existe et est en statut `VALIDATING`

## Tests

Exécuter les tests du workflow unique :

```bash
pytest tests/test_workflow_unique.py -v
```

Tests disponibles :
- `test_workflow_unique_demarre_avec_marqueur` : Vérification démarrage
- `test_workflow_unique_sans_marqueur` : Vérification non-démarrage
- `test_workflow_unique_genere_code_interdit` : Détection erreur
- `test_start_mission_toujours_workflow_complet` : Vérification workflow
- `test_process_response_extraction_demande` : Extraction marqueur

## Maintenance

### Redémarrage Serveur

Après modification de `config_agents/JARVIS_MAITRE.md`, **redémarrer le serveur** :

```bash
# Arrêter (Ctrl+C)
# Relancer
.\start_jarvis_complete.ps1
```

### Vérification Logs

Les logs sont dans `backend/logs/jarvis_audit.log` (ignoré par git).

Pour diagnostic en temps réel, utiliser les logs console avec `print()`.
