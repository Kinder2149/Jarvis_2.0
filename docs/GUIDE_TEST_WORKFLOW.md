# Guide de test du workflow 5 agents - JARVIS 2.0

## ✅ Corrections appliquées

### 1. Prompt JARVIS_Maître renforcé
**Fichier** : `config_agents/JARVIS_MAITRE.md`

**Changements** :
- ⚠️ **INTERDICTION FORMELLE** de générer du code directement
- Format obligatoire de réponse avec `[DEMANDE_CODE_CODEUR: ...]`
- Liste explicite des interdictions (montrer du code, dire "Voici le fichier...")
- Message clair : "SI TU GÉNÈRES DU CODE DIRECTEMENT, TU AS ÉCHOUÉ TA MISSION"

### 2. Endpoint missions corrigé
**Fichier** : `frontend/js/views/project-detail.js:317`
- Changé `status=IN_PROGRESS` → `status=in_progress`

### 3. Logs détaillés ajoutés
**Fichier** : `backend/services/orchestration.py:906-916`
- Affiche réponse complète de JARVIS_Maître
- Avertissements si marqueur non détecté

### 4. Interface 3 colonnes
**Fichier** : `frontend/js/views/project-detail.js`
- Layout : Conversations (haut) + Workflow (bas) | Chat | Fichiers
- Workflow visible en permanence sous conversations

---

## 🧪 Procédure de test

### Étape 1 : Redémarrer le serveur

```powershell
# Arrêter le serveur actuel (Ctrl+C dans le terminal)
# Redémarrer
.\start_jarvis_complete.ps1
```

**Important** : Le nouveau prompt JARVIS_Maître sera chargé au redémarrage.

---

### Étape 2 : Créer un nouveau projet de test

1. Aller sur http://localhost:8000
2. Cliquer sur **Projets**
3. Créer un nouveau projet :
   - Nom : `test_workflow_todo`
   - Chemin : `C:\DEV\TEST\test_workflow_todo` (ou autre dossier vide)

---

### Étape 3 : Créer une conversation

1. Cliquer sur le projet créé
2. Cliquer sur **+ Nouvelle conversation**
3. Sélectionner agent : **JARVIS_Maître**

---

### Étape 4 : Envoyer la demande de mission

**Copier-coller exactement ce prompt** :

```
MISSION : Création d'un gestionnaire de tâches

Je veux créer une application CLI simple pour gérer des tâches.

Fonctionnalités :
- ajouter une tâche
- lister les tâches
- marquer comme terminée
- supprimer une tâche

Contraintes :
- Python
- Stockage JSON
- Tests pytest

Je valide d'avance l'architecture que tu proposeras.
Génère directement le projet complet.
```

---

### Étape 5 : Observer la réponse de JARVIS_Maître

#### ✅ Comportement attendu (CORRECT)

JARVIS_Maître doit répondre :

```
Parfait. Je délègue au CODEUR.

[DEMANDE_CODE_CODEUR: Crée les fichiers suivants pour un gestionnaire de tâches CLI en Python :
- main.py : script principal avec menu interactif, fonctions add_task(), list_tasks(), mark_done(), delete_task()
- storage.py : classe JsonStorage pour sauvegarder/charger tasks.json
- tests/test_main.py : tests pytest pour toutes les fonctions
Utilise Python 3, stockage JSON, pytest pour les tests]
```

**Indicateurs de succès** :
- ✅ Pas de code Python affiché dans la réponse
- ✅ Présence du marqueur `[DEMANDE_CODE_CODEUR: ...]`
- ✅ Instruction complète dans le marqueur

#### ❌ Comportement incorrect (À CORRIGER)

Si JARVIS_Maître répond :

```
Parfait. Je génère le projet complet.

Fichier : main.py
```python
import json
...
```

**Indicateurs d'échec** :
- ❌ Code Python affiché directement
- ❌ Blocs de code avec ```python
- ❌ Pas de marqueur `[DEMANDE_CODE_CODEUR: ...]`

---

### Étape 6 : Observer les logs backend

Dans le terminal PowerShell où tourne le serveur, chercher :

#### ✅ Logs attendus (workflow déclenché)

```
Orchestration: process_response appelé pour session <id>
Orchestration: Réponse complète (XXX chars): Parfait. Je délègue au CODEUR...
Orchestration: ✅ DEMANDE_CODE_CODEUR détectée pour session <id>
Orchestration: Demande extraite (XXX chars)
Orchestration: Démarrage mission pour projet <path>
Orchestration: Mission <mission_id> créée
```

#### ❌ Logs problématiques (workflow non déclenché)

```
Orchestration: process_response appelé pour session <id>
Orchestration: Réponse complète (XXX chars): Parfait. Je génère le projet...
Orchestration: ❌ Aucune délégation détectée pour session <id>
Orchestration: Pattern recherché: \[DEMANDE_CODE_CODEUR:\s*(.*?)\]
Orchestration: Réponse ne contient pas [DEMANDE_CODE_CODEUR: ...]
```

---

### Étape 7 : Observer l'interface workflow

**Zone workflow** (en bas à gauche, sous conversations) :

#### ✅ Si workflow déclenché

La zone workflow affichera :
```
⚙️ Workflow

Mission ID: mission_xxx
Statut: IN_PROGRESS
Phase: ARCHITECTURE

Fichiers créés :
- main.py
- storage.py
- tests/test_main.py
```

#### ❌ Si workflow non déclenché

La zone workflow restera vide :
```
⚙️ Workflow

Aucun workflow actif

Le workflow apparaîtra ici quand JARVIS_Maître
délèguera une tâche.
```

---

## 📊 Résultats attendus

### Scénario 1 : Succès total ✅

1. JARVIS_Maître génère `[DEMANDE_CODE_CODEUR: ...]`
2. Logs backend montrent "✅ DEMANDE_CODE_CODEUR détectée"
3. Mission créée et workflow démarre
4. Zone workflow affiche la progression
5. Fichiers créés dans le dossier projet

### Scénario 2 : Échec prompt (JARVIS_Maître ignore instructions) ❌

1. JARVIS_Maître génère du code directement
2. Logs backend montrent "❌ Aucune délégation détectée"
3. Pas de mission créée
4. Zone workflow reste vide
5. Aucun fichier créé

**Si scénario 2** → Le prompt JARVIS_Maître est toujours ignoré par Gemini

---

## 🔍 Diagnostic si échec

### Vérifier que le prompt est bien chargé

```powershell
# Vérifier le contenu du fichier prompt
Get-Content config_agents\JARVIS_MAITRE.md | Select-String "INTERDICTION FORMELLE"
```

Doit afficher :
```
⚠️ **INTERDICTION FORMELLE DE GÉNÉRER DU CODE TOI-MÊME** ⚠️
```

### Vérifier les logs complets

Copier les lignes commençant par `Orchestration:` et me les envoyer.

---

## 📝 Rapport de test

Après le test, noter :

- [ ] JARVIS_Maître a généré `[DEMANDE_CODE_CODEUR: ...]` ?
- [ ] Logs backend montrent "✅ DEMANDE_CODE_CODEUR détectée" ?
- [ ] Mission créée (visible dans logs) ?
- [ ] Zone workflow affiche la progression ?
- [ ] Fichiers créés dans le dossier projet ?

**Si tous ✅** → Workflow fonctionne correctement
**Si un seul ❌** → Copier les logs et la réponse de JARVIS_Maître pour diagnostic

---

## 🚨 Si le problème persiste

Si après redémarrage JARVIS_Maître génère toujours du code directement :

**Hypothèses** :
1. Gemini ignore les instructions de format strict
2. Le prompt est trop long et Gemini ne lit pas tout
3. La température est trop élevée (> 0.5)

**Solutions possibles** :
1. Réduire la température à 0.1 (plus strict)
2. Simplifier le prompt (garder uniquement les règles de délégation)
3. Ajouter des exemples concrets dans le prompt
4. Utiliser un autre modèle (Claude, GPT-4)

---

## ✅ Checklist finale

Avant de tester :

- [ ] Serveur redémarré (nouveau prompt chargé)
- [ ] Nouveau projet créé (dossier vide)
- [ ] Nouvelle conversation avec JARVIS_Maître
- [ ] Prompt de test copié-collé exactement
- [ ] Terminal backend visible pour voir les logs

Après le test :

- [ ] Copier la réponse complète de JARVIS_Maître
- [ ] Copier les logs backend (lignes "Orchestration:")
- [ ] Vérifier si fichiers créés dans le dossier projet
- [ ] Noter si zone workflow affiche quelque chose
