# JARVIS 2.0 — DOCUMENT DE TRAVAIL UNIQUE

**Date** : 7 mars 2026  
**Statut** : Document de travail consolidé (remplace tous les autres docs work)  
**Contexte** : Optimisation complète JARVIS pour Valentin (pilote projet IA, 0% code autonome, besoin précision maximale)

---

## 🎯 BESOIN RÉEL VALENTIN

**Profil** :
- Pilote de projet assisté par IA à 100%
- 0% production code autonome
- Forte capacité conception produit
- Besoin : Précision > Rapidité
- 9 projets réalisés (JARVIS, UFM, TerraNova, PaperClip2, etc.)

**Objectif JARVIS** :
- Remplacer Windsurf comme outil principal
- Équipe IA compétente produisant code structuré, sans doublons, bien documenté
- Capitalisation sur projets précédents (mémoire)
- Workflow adapté à un non-codeur

---

## 📋 DÉCISIONS VALIDÉES

### 1. Équipe d'Agents
**✅ 5 agents spécialisés + BASE template**
- JARVIS_Maître, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR
- BASE conservé comme référence (non utilisé workflow actif)
- **Configs uniquement** dans `agent_config.py` (pas fichiers séparés)
- Suppression doublons, référencement propre documentation

### 2. Méthode de Travail : Cycle ARRF
**✅ Analyse-Réflexion-Remise en Question-Fixation**
- JARVIS_Maître : Cycle ARRF complet
- ARCHITECTE : Analyse + Réflexion
- CODEUR : Fixation uniquement
- TESTEUR : Réflexion + Fixation
- VALIDATEUR : Remise en Question

**Règles Agents** :
- Honnêteté > Satisfaction utilisateur
- Signaler impossibilités, proposer alternatives
- Pas de solutions incomplètes

**Fonctionnement JARVIS_Maître** :
- Explique en langage non-technique (comme conversation actuelle)
- Pose questions pour cadrer besoin
- Challenge propositions pour valider
- Attend validation utilisateur avant exécution

### 3. Orchestration Complète
**✅ JARVIS_Maître reconnaît phases mission**
- Détection automatique phase actuelle
- Workflow adaptatif (mode rapide vs complet)
- Décision basée sur analyse préliminaire (pas mots-clés)

### 4. Gestion États Missions
**✅ Workflow asynchrone avec pause/reprise**
- Mission.status : PENDING → IN_PROGRESS → VALIDATING → COMPLETED/FAILED
- Endpoint API `/mission/{id}/validate` pour validation utilisateur
- Sauvegarde état, reprise possible après fermeture JARVIS

### 5. Interface Édition Library RAG
**✅ Édition complète Library via frontend**
- Profil utilisateur éditable
- Templates, patterns, rules éditables
- Synchronisation automatique RAG après modification
- Pas juste profil, TOUTE la Library accessible

### 6. Gestion Erreurs
**✅ Rollback + nettoyage + Mission.FAILED**
- Si échec après 3 tentatives → Mission.status = FAILED
- Option nettoyage fichiers partiels
- Demande utilisateur pour rollback

### 7. Prompts Agents
**✅ Ultra-détaillés (800+ lignes)**
- Inspirés CODEUR.md existant
- Exemples concrets, règles spécifiques
- Format output exact

### 8. Modèles Gemini
**✅ Configuration production (pas dev)**
- Modèles optimaux par rôle (précision > rapidité)
- Tests live avec vrais modèles
- Fallback si quota épuisé

### 9. Migration & Nettoyage
**✅ Suppression complète ancien système**
- Mistral/OpenRouter : Complètement supprimés
- Ancien workflow (marqueurs `[DEMANDE_CODE_CODEUR: ...]`) : Supprimé
- Tests existants : Supprimés, batterie complète recréée
- Nouvelle base propre, pas de migration

**✅ Projets Windsurf existants**
- Pas de projets JARVIS à migrer
- Possibilité indexer projets Windsurf dans RAG (optionnel)

**✅ Provider unique**
- Google Gemini Tier 1 exclusif
- Tous agents utilisent Gemini

---

## 🎯 SYNTHÈSE TECHNIQUE

### Situation Actuelle
- **Tier 1 Gemini** : ✅ Opérationnel (quotas 150-175 RPM)
- **4 agents** : JARVIS_Maître, CODEUR, BASE, VALIDATEUR
- **RAG** : ✅ Fonctionnel mais sous-utilisé (Library quasi-vide)
- **Scripts démarrage** : ✅ Existants (Python + PowerShell)
- **Documentation** : ⚠️ Riche mais dispersée (7 projets analysés)

### Problèmes Identifiés
1. **Library RAG vide** → CODEUR sans référence qualité
2. **Équipe agents non optimale** → BASE sous-utilisé, redondances
3. **Workflow rigide** → Validation manuelle excessive
4. **Pas de mémoire projets** → Perte contexte entre sessions
5. **Documentation dispersée** → 7 fichiers exemples non indexés

---

## 📊 DIAGNOSTIC DÉTAILLÉ

### 1. Configuration Gemini Tier 1

#### ✅ Ce qui fonctionne
```
JARVIS_MAITRE_MODEL=gemini-2.5-pro    # 150 RPM, 2M tokens contexte
CODEUR_MODEL=gemini-2.5-pro           # 150 RPM, 2M tokens contexte
BASE_MODEL=gemini-2.5-pro             # 150 RPM, 2M tokens contexte
VALIDATEUR_MODEL=gemini-3.1-pro       # 25 RPM, 5M tokens contexte
```

**Total quotas** : 175 RPM cumulés (largement suffisant)

#### ⚠️ Optimisations manquantes

**Problème 1 : Tous sur gemini-2.5-pro**
- JARVIS_Maître, CODEUR, BASE partagent les mêmes 150 RPM
- Risque saturation si projet complexe (10+ fichiers)

**Solution** : Répartir sur modèles différents
```env
JARVIS_MAITRE_MODEL=gemini-2.5-pro        # Orchestration (150 RPM)
CODEUR_MODEL=gemini-2.5-pro               # Code critique (150 RPM)
BASE_MODEL=gemini-2.0-flash               # Rapports simples (2000 RPM)
VALIDATEUR_MODEL=gemini-3.1-pro-preview   # Validation finale (25 RPM)
```

**Gain** : 2000 + 150 + 150 + 25 = **2325 RPM** (13x plus)

**Problème 2 : Pas de fallback**
- Si gemini-2.5-pro saturé → tout bloque
- Pas de dégradation gracieuse

**Solution** : Ajouter fallback dans `gemini_provider.py`
```python
FALLBACK_MODELS = {
    "gemini-2.5-pro": "gemini-2.0-flash",
    "gemini-3.1-pro-preview": "gemini-2.5-pro"
}
```

---

### 2. Équipe d'Agents — Challenge Complet

#### Configuration Actuelle (4 agents)

| Agent | Rôle | Modèle | Utilisation Réelle | Problème |
|-------|------|--------|-------------------|----------|
| **JARVIS_Maître** | Orchestrateur | gemini-2.5-pro | ✅ 100% | Aucun |
| **CODEUR** | Génération code | gemini-2.5-pro | ✅ 100% | Aucun |
| **BASE** | Rapports, vérification | gemini-2.5-pro | ⚠️ 30% | Sous-utilisé |
| **VALIDATEUR** | Contrôle qualité | gemini-3.1-pro | ✅ 80% | Aucun |

#### Analyse Critique

**BASE : Agent sous-utilisé**
- **Rôle théorique** : Vérifier complétude, créer rapports
- **Rôle réel** : Compte les fichiers générés (tâche triviale)
- **Coût** : 1 requête gemini-2.5-pro par projet (~$0.02)
- **Valeur ajoutée** : Faible (peut être fait en Python pur)

**VALIDATEUR : Redondant avec tests**
- **Rôle** : Vérifier syntaxe, logique, tests
- **Problème** : Si CODEUR génère tests pytest → pytest valide déjà
- **Coût** : 1 requête gemini-3.1-pro par projet (~$0.03)
- **Valeur ajoutée** : Moyenne (détecte bugs que pytest ne voit pas)

#### 🎯 Proposition : Équipe Optimisée (5 agents)

**Scénario A : Équipe Minimaliste (2 agents)**
```
JARVIS_Maître (orchestrateur)
    ↓
CODEUR (génération + auto-validation via tests)
```

**Avantages** :
- ✅ Coût minimal (~$0.03/projet)
- ✅ Workflow rapide (2 étapes)
- ✅ Quotas préservés

**Inconvénients** :
- ❌ Pas de contrôle qualité humain-like
- ❌ Bugs subtils non détectés

**Verdict** : ❌ Trop risqué pour ton besoin (tu ne codes pas)

---

**Scénario B : Équipe Équilibrée (3 agents) — RECOMMANDÉ**
```
JARVIS_Maître (orchestrateur)
    ↓
CODEUR (génération code + tests)
    ↓
VALIDATEUR (contrôle qualité final)
```

**Changements** :
- ❌ Supprimer BASE (remplacé par script Python)
- ✅ Garder VALIDATEUR (sécurité critique)
- ✅ CODEUR génère tests systématiquement

**Avantages** :
- ✅ Workflow simplifié (3 étapes)
- ✅ Coût réduit (~$0.05/projet vs $0.07)
- ✅ Qualité préservée (VALIDATEUR)
- ✅ Quotas optimisés (150 RPM libérés)

**Inconvénients** :
- ⚠️ Perte rapports détaillés BASE (mineur)

**Verdict** : ✅ **OPTIMAL pour ton usage**

---

**Scénario C : Équipe Spécialisée (5 agents)**
```
JARVIS_Maître (orchestrateur)
    ↓
ARCHITECTE (conception architecture)
    ↓
CODEUR (génération code)
    ↓
TESTEUR (génération tests)
    ↓
VALIDATEUR (contrôle qualité)
```

**Nouveaux agents** :
- **ARCHITECTE** : Propose architecture avant génération
- **TESTEUR** : Spécialisé tests (séparé de CODEUR)

**Avantages** :
- ✅ Séparation responsabilités maximale
- ✅ Qualité architecturale supérieure
- ✅ Tests exhaustifs

**Inconvénients** :
- ❌ Workflow lent (5 étapes)
- ❌ Coût élevé (~$0.15/projet)
- ❌ Quotas consommés rapidement
- ❌ Complexité orchestration

**Verdict** : ❌ Over-engineering pour ton besoin

---

#### 🏆 ÉQUIPE OPTIMALE POUR PRÉCISION MAXIMALE

**Besoin Valentin** : Précision > Rapidité (non-codeur, dépendance 100% IA)

**Scénario Retenu : 5 agents spécialisés**

```
JARVIS_Maître (orchestrateur)
    ↓
ARCHITECTE (conception architecture)
    ↓
CODEUR (génération code)
    ↓
TESTEUR (génération tests exhaustifs)
    ↓
VALIDATEUR (contrôle qualité final)
```

**Justification** :
1. **ARCHITECTE** (nouveau, basé sur BASE)
   - **Rôle** : Propose architecture AVANT génération code
   - **Pourquoi** : Valentin ne code pas → besoin validation architecture claire
   - **Output** : Document architecture.md + liste fichiers à créer
   - **Modèle** : gemini-2.5-pro (précision architecturale)

2. **CODEUR** (existant, optimisé)
   - **Rôle** : Génère code selon architecture validée
   - **Changement** : Ne génère PLUS les tests (délégué à TESTEUR)
   - **Focus** : Qualité code, respect patterns, pas de doublons
   - **Modèle** : gemini-2.5-pro (code critique)

3. **TESTEUR** (nouveau, basé sur BASE)
   - **Rôle** : Génère tests exhaustifs (unitaires, intégration, E2E)
   - **Pourquoi** : Séparation responsabilités, tests plus complets
   - **Output** : Fichiers tests + rapport couverture
   - **Modèle** : gemini-2.0-flash (tests = tâche répétitive)

4. **VALIDATEUR** (existant, renforcé)
   - **Rôle** : Contrôle qualité final (code + tests + architecture)
   - **Changement** : Valide aussi cohérence architecture/code
   - **Output** : Rapport validation VALIDE/INVALIDE + recommandations
   - **Modèle** : gemini-3.1-pro-preview (précision maximale)

5. **JARVIS_Maître** (existant, workflow étendu)
   - **Rôle** : Orchestration + détection fin mission
   - **Changement** : Gère workflow 5 agents + auto-indexation
   - **Modèle** : gemini-2.5-pro (orchestration complexe)

**BASE** : Conservé comme template (pas dans workflow actif)

**Avantages pour Valentin** :
- ✅ Architecture validée AVANT code (sécurité)
- ✅ Tests exhaustifs séparés (qualité)
- ✅ Validation multi-niveaux (fiabilité)
- ✅ Adapté non-codeur (chaque étape claire)

**Inconvénients assumés** :
- ⚠️ Workflow plus long (~5-8 min vs 3-5 min)
- ⚠️ Coût plus élevé (~$0.12/projet vs $0.07)
- ⚠️ Quotas consommés plus vite

**Verdict** : ✅ **Optimal pour besoin précision de Valentin**

---

### 3. Mapping Modèles Gemini par Rôle Agent

**Principe** : Précision > Rapidité (besoin Valentin)

| Agent | Rôle | Complexité | Modèle Optimal | RPM | Justification |
|-------|------|------------|----------------|-----|---------------|
| **JARVIS_Maître** | Orchestration | Élevée | gemini-2.5-pro | 150 | Décisions critiques, délégation complexe |
| **ARCHITECTE** | Conception | Très élevée | gemini-2.5-pro | 150 | Architecture = fondation projet |
| **CODEUR** | Génération code | Très élevée | gemini-2.5-pro | 150 | Code = cœur projet, 0 erreur |
| **TESTEUR** | Génération tests | Moyenne | gemini-2.0-flash | 2000 | Tests = patterns répétitifs |
| **VALIDATEUR** | Contrôle qualité | Maximale | gemini-3.1-pro-preview | 25 | Validation finale = sécurité |

**Quotas totaux** : 2475 RPM (vs 175 actuels = **14x plus**)

**Stratégie fallback** :
```python
FALLBACK_MODELS = {
    "gemini-2.5-pro": "gemini-2.0-flash",      # Si quota épuisé
    "gemini-3.1-pro-preview": "gemini-2.5-pro", # Si quota épuisé
    "gemini-2.0-flash": "gemini-1.5-flash"      # Si quota épuisé
}
```

**Coût estimé par projet** :
- JARVIS_Maître : $0.01 (orchestration)
- ARCHITECTE : $0.02 (architecture)
- CODEUR : $0.04 (code)
- TESTEUR : $0.01 (tests, modèle flash)
- VALIDATEUR : $0.04 (validation)
- **Total** : **$0.12/projet** (acceptable pour précision)

---

### 4. Détection Fin de Projet/Mission

#### Problème
**Comment détecter qu'un projet est terminé ?**

Cas d'usage :
1. Nouveau projet créé de zéro
2. Modification projet existant
3. Ajout fonctionnalité à projet existant
4. Correction bugs projet existant

#### Solution : Système de Missions

**Concept** : Chaque demande utilisateur = 1 mission

```python
# backend/models/mission.py
from enum import Enum
from datetime import datetime

class MissionStatus(Enum):
    PENDING = "pending"           # Mission créée, pas encore démarrée
    IN_PROGRESS = "in_progress"   # En cours d'exécution
    VALIDATING = "validating"     # En attente validation utilisateur
    COMPLETED = "completed"       # Terminée et validée
    FAILED = "failed"             # Échec (erreurs non résolues)
    CANCELLED = "cancelled"       # Annulée par utilisateur

class Mission:
    def __init__(self, mission_id: str, user_request: str, project_path: str):
        self.mission_id = mission_id
        self.user_request = user_request
        self.project_path = project_path
        self.status = MissionStatus.PENDING
        self.created_at = datetime.now()
        self.completed_at = None
        self.files_created = []
        self.files_modified = []
        self.validation_passed = False
        self.architecture_validated = False
        self.code_validated = False
        self.tests_validated = False
```

**Workflow avec missions** :

```
1. USER : "Crée une calculatrice"
   → Création Mission(id="calc_001", status=PENDING)

2. JARVIS_Maître : Analyse besoin
   → Mission.status = IN_PROGRESS

3. ARCHITECTE : Propose architecture
   → Mission.architecture_validated = False (attente validation USER)
   → Mission.status = VALIDATING

4. USER : Valide architecture
   → Mission.architecture_validated = True
   → Mission.status = IN_PROGRESS

5. CODEUR : Génère code
   → Mission.files_created = ["calculator.py", "main.py"]

6. TESTEUR : Génère tests
   → Mission.files_created += ["test_calculator.py"]

7. VALIDATEUR : Valide code + tests
   → Si VALIDE : Mission.code_validated = True
   → Si INVALIDE : Retour CODEUR (boucle correction)

8. JARVIS_Maître : Tous validés ?
   → architecture_validated = True
   → code_validated = True
   → tests_validated = True
   → Mission.status = COMPLETED
   → Mission.completed_at = datetime.now()
   → Déclenche auto-indexation RAG
```

**Critères fin de mission** :
```python
def is_mission_complete(mission: Mission) -> bool:
    """Détermine si une mission est terminée"""
    return (
        mission.architecture_validated and
        mission.code_validated and
        mission.tests_validated and
        len(mission.files_created) > 0
    )
```

---

### 5. Gestion Conflits Versions & Anti-Doublons

#### Problème 1 : Projet Existant vs Nouveau

**Scénario** :
```
USER : "Crée une calculatrice"
→ JARVIS crée projects/calculator/

USER : "Crée une calculatrice" (2 semaines plus tard)
→ Risque : Écraser projects/calculator/ existant
```

**Solution : Détection projet existant**

```python
# backend/services/project_manager.py
import os
from pathlib import Path
from datetime import datetime

class ProjectManager:
    def detect_existing_project(self, project_name: str, base_path: str) -> dict:
        """Détecte si un projet existe déjà"""
        project_path = Path(base_path) / project_name
        
        if not project_path.exists():
            return {"exists": False, "action": "create_new"}
        
        # Projet existe → Analyser contenu
        files = list(project_path.rglob("*"))
        last_modified = max(f.stat().st_mtime for f in files if f.is_file())
        
        return {
            "exists": True,
            "path": str(project_path),
            "files_count": len([f for f in files if f.is_file()]),
            "last_modified": datetime.fromtimestamp(last_modified),
            "action": "ask_user"  # Demander à l'utilisateur
        }
    
    def propose_action(self, existing_info: dict) -> str:
        """Propose action à l'utilisateur"""
        if not existing_info["exists"]:
            return "create_new"
        
        # Générer message pour utilisateur
        return f"""
⚠️ Un projet '{existing_info['path']}' existe déjà :
- {existing_info['files_count']} fichiers
- Dernière modification : {existing_info['last_modified']}

Que veux-tu faire ?
1. Modifier le projet existant (ajouter/corriger)
2. Créer un nouveau projet avec un nom différent
3. Écraser le projet existant (⚠️ perte données)
"""
```

**Workflow avec détection** :

```
1. USER : "Crée une calculatrice"
2. ProjectManager : Détecte projects/calculator/ existe
3. JARVIS_Maître : Demande à USER quelle action
4. USER : Choisit option (modifier/nouveau/écraser)
5. JARVIS_Maître : Exécute selon choix
```

#### Problème 2 : Versioning Automatique

**Solution : Versioning sémantique automatique**

```python
# backend/services/version_manager.py
import json
from pathlib import Path

class VersionManager:
    def get_project_version(self, project_path: str) -> str:
        """Récupère version actuelle du projet"""
        version_file = Path(project_path) / ".jarvis_version.json"
        
        if not version_file.exists():
            return "0.0.0"
        
        data = json.loads(version_file.read_text())
        return data["version"]
    
    def increment_version(self, current_version: str, change_type: str) -> str:
        """Incrémente version selon type de changement"""
        major, minor, patch = map(int, current_version.split("."))
        
        if change_type == "major":  # Refonte complète
            return f"{major + 1}.0.0"
        elif change_type == "minor":  # Nouvelle fonctionnalité
            return f"{major}.{minor + 1}.0"
        elif change_type == "patch":  # Correction bug
            return f"{major}.{minor}.{patch + 1}"
    
    def save_version(self, project_path: str, version: str, mission_id: str):
        """Sauvegarde version + métadonnées"""
        version_file = Path(project_path) / ".jarvis_version.json"
        
        data = {
            "version": version,
            "mission_id": mission_id,
            "updated_at": datetime.now().isoformat(),
            "files_modified": []  # Liste fichiers modifiés cette version
        }
        
        version_file.write_text(json.dumps(data, indent=2))
```

**Détection automatique type changement** :

```python
def detect_change_type(user_request: str) -> str:
    """Détecte type de changement depuis demande utilisateur"""
    request_lower = user_request.lower()
    
    # Mots-clés refonte
    if any(word in request_lower for word in ["refonte", "réécrire", "recommencer"]):
        return "major"
    
    # Mots-clés nouvelle fonctionnalité
    if any(word in request_lower for word in ["ajoute", "nouvelle", "feature"]):
        return "minor"
    
    # Mots-clés correction
    if any(word in request_lower for word in ["corrige", "bug", "erreur", "fix"]):
        return "patch"
    
    # Par défaut : minor (nouvelle fonctionnalité)
    return "minor"
```

#### Problème 3 : Anti-Doublons RAG

**Scénario** :
```
Mission 1 : Crée calculator → Indexé dans RAG
Mission 2 : Modifie calculator → Risque doublon dans RAG
```

**Solution : Indexation avec métadonnées uniques**

```python
# backend/services/rag_auto_indexer.py
from datetime import datetime

class RAGAutoIndexer:
    def index_mission(self, mission: Mission):
        """Indexe mission dans RAG avec métadonnées uniques"""
        
        # Vérifier si projet déjà indexé
        existing = self.search_project(mission.project_path)
        
        if existing:
            # Projet existe → Mise à jour
            self.update_project_index(mission)
        else:
            # Nouveau projet → Création
            self.create_project_index(mission)
    
    def search_project(self, project_path: str) -> dict | None:
        """Recherche projet dans RAG"""
        results = rag_manager.search(
            query=f"project_path:{project_path}",
            filter={"type": "project_memory"}
        )
        return results[0] if results else None
    
    def update_project_index(self, mission: Mission):
        """Met à jour index projet existant"""
        # 1. Récupérer entrée existante
        existing = self.search_project(mission.project_path)
        
        # 2. Supprimer ancienne version
        rag_manager.delete(document_id=existing["id"])
        
        # 3. Créer nouvelle version avec métadonnées mises à jour
        self.create_project_index(mission, is_update=True)
    
    def create_project_index(self, mission: Mission, is_update: bool = False):
        """Crée nouvelle entrée RAG pour projet"""
        
        # Générer documentation projet
        docs = self.generate_project_docs(mission)
        
        # Métadonnées uniques
        metadata = {
            "type": "project_memory",
            "project_path": mission.project_path,
            "mission_id": mission.mission_id,
            "version": self.get_project_version(mission.project_path),
            "indexed_at": datetime.now().isoformat(),
            "is_update": is_update
        }
        
        # Indexer chaque document
        for doc_name, content in docs.items():
            rag_manager.add_text(
                content,
                metadata={**metadata, "document": doc_name}
            )
```

**Stratégie anti-doublon** :
1. **Clé unique** : `project_path` (chemin absolu projet)
2. **Recherche avant indexation** : Vérifier si `project_path` existe
3. **Mise à jour atomique** : Supprimer ancien + créer nouveau
4. **Versioning** : Chaque index a un numéro de version

---

### 6. Workflow Actuel — Remise en Cause

#### Workflow Actuel (7 étapes)

```
1. USER → Demande projet
2. JARVIS_Maître → Analyse besoin
3. JARVIS_Maître → Demande validation USER ⚠️
4. USER → Valide
5. JARVIS_Maître → Délègue CODEUR
6. CODEUR → Génère code
7. BASE → Vérifie complétude
8. VALIDATEUR → Valide qualité
9. JARVIS_Maître → Retour USER
```

**Temps total** : ~3-5 minutes  
**Requêtes IA** : 4-6 (selon itérations)

#### Problèmes Identifiés

**Problème 1 : Validation manuelle excessive**
- Étape 3 : JARVIS_Maître demande validation AVANT génération
- **Impact** : Ralentit workflow, frustrant pour projets simples
- **Cause** : Prompt JARVIS_Maître trop prudent

**Problème 2 : BASE inutile**
- Étape 7 : BASE compte les fichiers (tâche triviale)
- **Impact** : +1 requête IA, +30s délai
- **Cause** : Héritage architecture initiale

**Problème 3 : Pas de mode "rapide"**
- Tous projets passent par workflow complet
- **Impact** : Projets simples (1-2 fichiers) prennent 3 min
- **Cause** : Pas de détection complexité

#### 🎯 Workflow Optimisé avec 5 Agents

**Mode RAPIDE (≤3 fichiers)** :
```
1. USER → "Crée une calculatrice simple"
2. JARVIS_Maître → Détecte complexité = SIMPLE
3. JARVIS_Maître → Crée Mission(status=IN_PROGRESS)
4. CODEUR → Génère code directement (pas d'ARCHITECTE)
5. TESTEUR → Génère tests
6. VALIDATEUR → Valide code + tests
   ├─ Si VALIDE → Mission.status = COMPLETED
   └─ Si INVALIDE → Retour CODEUR (max 2 corrections)
7. JARVIS_Maître → Auto-indexation RAG
8. JARVIS_Maître → Retour USER
```
**Temps** : 2-3 min  
**Coût** : ~$0.08 (pas d'ARCHITECTE)

---

**Mode COMPLET (>3 fichiers)** :
```
1. USER → "Crée une API REST complète avec auth"
2. JARVIS_Maître → Détecte complexité = COMPLEX
3. JARVIS_Maître → Vérifie projet existant
   ├─ Si existe → Demande action USER (modifier/nouveau/écraser)
   └─ Si nouveau → Continue
4. JARVIS_Maître → Crée Mission(status=IN_PROGRESS)
5. ARCHITECTE → Propose architecture
   - Génère architecture.md
   - Liste fichiers à créer
   - Propose stack technique
6. JARVIS_Maître → Demande validation USER
   → Mission.status = VALIDATING
7. USER → Valide architecture
   → Mission.architecture_validated = True
   → Mission.status = IN_PROGRESS
8. CODEUR → Génère code (itératif si >10 fichiers)
   → Mission.files_created = ["file1.py", "file2.py", ...]
9. TESTEUR → Génère tests exhaustifs
   → Mission.files_created += ["test_file1.py", ...]
10. VALIDATEUR → Valide code + tests + cohérence architecture
    ├─ Si VALIDE → Mission.code_validated = True
    └─ Si INVALIDE → Retour CODEUR (max 2 corrections)
11. JARVIS_Maître → Tous validés ?
    → Mission.status = COMPLETED
    → Incrémente version projet
    → Auto-indexation RAG (anti-doublon)
12. JARVIS_Maître → Retour USER avec résumé complet
```
**Temps** : 5-8 min  
**Coût** : ~$0.12

**Gains** :
- ⚡ Mode rapide : **1-2 min** (vs 3-5 min)
- 💰 Économie : **-1 requête IA** par projet simple
- 🎯 Pertinence : Validation uniquement si nécessaire

**Implémentation** :
```python
# orchestration.py
def detect_project_complexity(instruction: str) -> str:
    """Détecte complexité projet"""
    file_count = estimate_file_count(instruction)
    if file_count <= 3:
        return "SIMPLE"
    elif file_count <= 10:
        return "MEDIUM"
    else:
        return "COMPLEX"

def execute_delegation(instruction: str, ...):
    complexity = detect_project_complexity(instruction)
    
    if complexity == "SIMPLE":
        # Mode rapide : pas de validation
        return execute_fast_mode(instruction)
    else:
        # Mode complet : validation architecture
        return execute_complete_mode(instruction)
```

---

### 4. Library RAG — Architecture Optimale

#### Situation Actuelle
```
RAG/doc/
├── API_DOCUMENTATION.md
├── RAG_ROUTES.md
└── setup.md
```

**Problème** : Library quasi-vide, pas de templates projets

#### 🎯 Architecture Recommandée

```
RAG/
├── library/                          # Library générique (bonnes pratiques)
│   ├── templates/                    # Templates réutilisables
│   │   ├── python/
│   │   │   ├── calculator.md         # Template calculatrice
│   │   │   ├── todo_app.md           # Template TODO app
│   │   │   ├── api_rest.md           # Template API REST
│   │   │   └── cli_tool.md           # Template outil CLI
│   │   ├── javascript/
│   │   │   ├── react_app.md
│   │   │   └── express_api.md
│   │   └── flutter/
│   │       └── mobile_app.md
│   ├── patterns/                     # Patterns architecturaux
│   │   ├── storage_json.md           # Pattern Storage JSON
│   │   ├── pydantic_models.md        # Pattern Pydantic v2
│   │   ├── service_layer.md          # Pattern Service Layer
│   │   └── singleton.md              # Pattern Singleton
│   └── rules/                        # Règles de codage
│       ├── keamder_coding_rules.md   # Règles générales
│       ├── python_best_practices.md
│       └── testing_guidelines.md
│
├── projects/                         # Mémoire projets spécifiques
│   ├── index.json                    # Index projets (métadonnées)
│   ├── ultimate_frisbee_manager/
│   │   ├── metadata.json             # Nom, date, stack, statut
│   │   ├── architecture.md           # Architecture retenue
│   │   ├── decisions.md              # Décisions techniques
│   │   └── lessons_learned.md        # Leçons apprises
│   ├── terranova/
│   ├── paperclip2/
│   └── jarvis_2.0/
│
└── doc/                              # Documentation RAG (inchangé)
    ├── API_DOCUMENTATION.md
    ├── RAG_ROUTES.md
    └── setup.md
```

#### Flux d'Utilisation

**1. Nouveau projet** :
```
USER : "Crée une calculatrice Python"
    ↓
RAG : Recherche "calculator python template"
    ↓
Trouve : library/templates/python/calculator.md
    ↓
CODEUR : Reçoit template + génère code conforme
```

**2. Fin de projet** :
```
JARVIS_Maître : Projet terminé
    ↓
Auto-indexation : Crée projects/calculator_2026_03_07/
    ↓
Stocke : architecture.md, decisions.md, lessons_learned.md
    ↓
Mise à jour : projects/index.json
```

**3. Projet similaire** :
```
USER : "Crée une autre calculatrice"
    ↓
RAG : Recherche "calculator" + trouve projets précédents
    ↓
CODEUR : Reçoit template + exemple projet réel
    ↓
Génère code cohérent avec historique
```

---

### 5. Système de Mémoire Projets — Auto-Indexation

#### Problème Actuel
- Pas de mémoire entre sessions
- JARVIS oublie tout au redémarrage
- Pas de capitalisation sur projets précédents

#### 🎯 Solution : Auto-Indexation RAG

**Composant 1 : Détection fin de projet**
```python
# orchestration.py
async def on_project_complete(project_name: str, files_created: list[str]):
    """Appelé automatiquement à la fin d'un projet"""
    await auto_index_project(project_name, files_created)
```

**Composant 2 : Extraction métadonnées**
```python
# rag_auto_indexer.py
def extract_project_metadata(project_path: str) -> dict:
    """Extrait métadonnées projet"""
    return {
        "name": detect_project_name(project_path),
        "date": datetime.now().isoformat(),
        "stack": detect_stack(project_path),  # Python, FastAPI, etc.
        "files": list_files(project_path),
        "architecture": detect_architecture(project_path),
        "status": "completed"
    }
```

**Composant 3 : Génération documentation**
```python
async def generate_project_docs(project_path: str, metadata: dict):
    """Génère docs projet via JARVIS_Maître"""
    
    # 1. Architecture
    architecture_md = await ask_jarvis_maitre(
        f"Analyse l'architecture du projet {metadata['name']} et crée architecture.md"
    )
    
    # 2. Décisions techniques
    decisions_md = await ask_jarvis_maitre(
        f"Liste les décisions techniques du projet {metadata['name']}"
    )
    
    # 3. Leçons apprises
    lessons_md = await ask_jarvis_maitre(
        f"Quelles leçons tirer du projet {metadata['name']} ?"
    )
    
    # Sauvegarder
    save_to_rag(f"projects/{metadata['name']}/", {
        "metadata.json": metadata,
        "architecture.md": architecture_md,
        "decisions.md": decisions_md,
        "lessons_learned.md": lessons_md
    })
```

**Composant 4 : Indexation ChromaDB**
```python
async def index_project_to_rag(project_name: str):
    """Indexe projet dans ChromaDB"""
    rag_manager = RAGManager()
    
    # Charger docs projet
    docs = load_project_docs(f"RAG/projects/{project_name}/")
    
    # Indexer avec métadonnées
    for doc_name, content in docs.items():
        rag_manager.add_text(
            content,
            metadata={
                "type": "project_memory",
                "project": project_name,
                "document": doc_name
            }
        )
```

**Composant 5 : Mise à jour index global**
```python
def update_projects_index(metadata: dict):
    """Met à jour projects/index.json"""
    index = load_json("RAG/projects/index.json")
    index["projects"].append({
        "name": metadata["name"],
        "date": metadata["date"],
        "stack": metadata["stack"],
        "status": metadata["status"]
    })
    save_json("RAG/projects/index.json", index)
```

#### Workflow Complet

```
1. USER : "Crée une calculatrice"
2. JARVIS génère projet → Fichiers créés
3. VALIDATEUR : Code OK
4. orchestration.py : Détecte fin projet
5. Auto-indexer : Extrait métadonnées
6. JARVIS_Maître : Génère architecture.md, decisions.md, lessons_learned.md
7. RAG : Indexe docs dans ChromaDB
8. projects/index.json : Mise à jour
9. USER : "Crée une autre calculatrice"
10. RAG : Trouve projet précédent + template
11. CODEUR : Génère code cohérent
```

---

### 6. Scripts Démarrage — Optimisation

#### Scripts Existants
- ✅ `start_jarvis_complete.py` : Complet, robuste
- ✅ `start_jarvis_complete.ps1` : Complet, robuste

#### Problème
- Pas de détection doublons (peut lancer 2x le même serveur)
- Pas de gestion arrêt propre (processus orphelins)

#### 🎯 Améliorations Recommandées

**1. Détection processus existants**
```python
# start_jarvis_complete.py
import psutil

def find_jarvis_processes() -> list[psutil.Process]:
    """Trouve processus JARVIS en cours"""
    jarvis_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'start_server.py' in cmdline or 'RAG/run.py' in cmdline:
                jarvis_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return jarvis_processes

def main():
    # Vérifier processus existants
    existing = find_jarvis_processes()
    if existing:
        print_warning(f"{len(existing)} processus JARVIS déjà en cours")
        for proc in existing:
            print_info(f"  PID {proc.pid}: {proc.name()}")
        
        response = input("Arrêter les processus existants ? (o/n): ")
        if response.lower() == 'o':
            for proc in existing:
                proc.terminate()
                proc.wait(timeout=5)
            print_success("Processus arrêtés")
        else:
            print_info("Démarrage annulé")
            sys.exit(0)
```

**2. Fichier PID pour tracking**
```python
# start_jarvis_complete.py
def save_pid_file(rag_pid: int, jarvis_pid: int):
    """Sauvegarde PIDs dans fichier"""
    pid_file = Path(".jarvis_pids.json")
    pid_file.write_text(json.dumps({
        "rag_pid": rag_pid,
        "jarvis_pid": jarvis_pid,
        "started_at": datetime.now().isoformat()
    }))

def load_pid_file() -> dict | None:
    """Charge PIDs depuis fichier"""
    pid_file = Path(".jarvis_pids.json")
    if pid_file.exists():
        return json.loads(pid_file.read_text())
    return None
```

**3. Commande stop dédiée**
```python
# stop_jarvis.py
def stop_jarvis():
    """Arrête proprement JARVIS"""
    pids = load_pid_file()
    if not pids:
        print_error("Aucun processus JARVIS trouvé")
        return
    
    for name, pid in pids.items():
        if name.endswith("_pid"):
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=5)
                print_success(f"Processus {name} (PID {pid}) arrêté")
            except psutil.NoSuchProcess:
                print_warning(f"Processus {name} (PID {pid}) déjà arrêté")
    
    Path(".jarvis_pids.json").unlink()
```

---

### 7. Documentation — Nettoyage & Restructuration

#### Situation Actuelle
```
docs/
├── JARVIS CONFIG/
│   ├── Réponses IA projet/        # 7 fichiers (TerraNova, UFM, etc.)
│   ├── KEAMDER_PROFILE.md         # 556 lignes
│   ├── KEAMDER_WORKFLOW.md        # 348 lignes
│   └── ...
├── reference/
├── work/
├── history/
└── _meta/
```

**Problèmes** :
- `Réponses IA projet/` : 7 fichiers non indexés dans RAG
- Duplication : KEAMDER_PROFILE.md existe mais pas dans RAG
- Pas de distinction Library (générique) vs Projets (spécifique)

#### 🎯 Plan de Restructuration

**Étape 1 : Migrer exemples projets vers RAG**
```bash
# Créer structure
mkdir -p RAG/projects/{terranova,ultimate_frisbee_manager,paperclip,portfolio}

# Extraire métadonnées de chaque fichier
python scripts/extract_project_metadata.py \
    "docs/JARVIS CONFIG/Réponses IA projet/TerraNova.md" \
    --output "RAG/projects/terranova/"

# Résultat attendu :
RAG/projects/terranova/
├── metadata.json          # Stack, technologies, dates
├── architecture.md        # Patterns détectés
└── lessons_learned.md     # Bonnes pratiques extraites
```

**Étape 2 : Créer templates génériques**
```bash
# Depuis exemples projets, extraire patterns réutilisables
python scripts/generate_templates.py \
    --source "RAG/projects/" \
    --output "RAG/library/templates/"

# Résultat attendu :
RAG/library/templates/python/calculator.md
RAG/library/templates/flutter/mobile_app.md
RAG/library/patterns/storage_json.md
```

**Étape 3 : Indexer dans ChromaDB**
```bash
python RAG/index_jarvis_library.py
```

**Étape 4 : Archiver anciens fichiers**
```bash
# Déplacer vers history (traçabilité)
mv "docs/JARVIS CONFIG/Réponses IA projet/" \
   "docs/history/raw_project_responses_archived_2026_03_07/"
```

---

### 7. Profil Utilisateur Éditable

#### Situation Actuelle
- Profil existe : `docs/JARVIS CONFIG/KEAMDER_PROFILE.md` (556 lignes)
- **Problème** : Non indexé dans RAG, édition manuelle uniquement

#### Solution : Interface UI + Sync Library

**Composant 1 : Endpoint API**
```python
# backend/api.py
from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import json

profile_router = APIRouter(prefix="/profile", tags=["profile"])

@profile_router.get("/")
async def get_profile():
    """Récupère profil utilisateur depuis Library RAG"""
    profile_path = Path("RAG/library/rules/keamder_profile.md")
    if not profile_path.exists():
        return {"error": "Profile not found"}
    
    content = profile_path.read_text(encoding="utf-8")
    return {"content": content, "path": str(profile_path)}

@profile_router.put("/")
async def update_profile(profile_data: dict):
    """Met à jour profil utilisateur"""
    profile_path = Path("RAG/library/rules/keamder_profile.md")
    
    # Sauvegarder nouveau contenu
    profile_path.write_text(profile_data["content"], encoding="utf-8")
    
    # Ré-indexer dans RAG
    await reindex_profile()
    
    return {"success": True, "message": "Profil mis à jour"}

@profile_router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    """Upload avatar utilisateur"""
    avatar_path = Path("RAG/library/assets/avatar.png")
    avatar_path.parent.mkdir(exist_ok=True)
    
    # Sauvegarder image
    content = await file.read()
    avatar_path.write_bytes(content)
    
    return {"success": True, "avatar_url": f"/assets/avatar.png"}
```

**Composant 2 : Interface Frontend**
```html
<!-- frontend/profile.html -->
<div id="profile-editor">
    <h2>Mon Profil</h2>
    
    <!-- Avatar -->
    <div class="avatar-section">
        <img id="avatar-preview" src="/assets/avatar.png" alt="Avatar">
        <input type="file" id="avatar-upload" accept="image/*">
    </div>
    
    <!-- Formulaire -->
    <form id="profile-form">
        <label>Nom</label>
        <input type="text" name="name" value="Valentin Coutry (Keamder)">
        
        <label>Rôle</label>
        <input type="text" name="role" value="Pilote de projet assisté par IA">
        
        <label>Stack préférée</label>
        <textarea name="stack">Python + FastAPI, Angular, Flutter</textarea>
        
        <label>Règles de codage</label>
        <textarea name="rules">Pydantic v2, Storage JSON, Tests pytest...</textarea>
        
        <button type="submit">Sauvegarder</button>
    </form>
</div>
```

**Composant 3 : Synchronisation RAG**
```python
async def reindex_profile():
    """Ré-indexe profil dans RAG après modification"""
    rag_manager = RAGManager()
    
    # Supprimer ancienne version
    rag_manager.delete(filter={"type": "user_profile"})
    
    # Charger nouveau profil
    profile_path = Path("RAG/library/rules/keamder_profile.md")
    content = profile_path.read_text(encoding="utf-8")
    
    # Indexer
    rag_manager.add_text(
        content,
        metadata={
            "type": "user_profile",
            "updated_at": datetime.now().isoformat()
        }
    )
```

---

## 🚀 PLAN D'IMPLÉMENTATION COMPLET

### Phase 1 : Création Nouveaux Agents (3-4h)

**1.1 Créer agent ARCHITECTE**
- [ ] Copier `backend/agents/base_agent.py` → `architecte_agent.py`
- [ ] Créer prompt `config_agents/ARCHITECTE.md`
  - Rôle : Conception architecture AVANT code
  - Output : architecture.md + liste fichiers
  - Règles : Propose stack, patterns, structure
- [ ] Ajouter config dans `agent_config.py`
  ```python
  "ARCHITECTE": {
      "role": "Architecte Logiciel",
      "model": "gemini-2.5-pro",
      "temperature": 0.3,
      "max_tokens": 8192,
      "prompt_file": "config_agents/ARCHITECTE.md"
  }
  ```
- [ ] Tests unitaires `test_architecte.py`

**1.2 Créer agent TESTEUR**
- [ ] Copier `backend/agents/base_agent.py` → `testeur_agent.py`
- [ ] Créer prompt `config_agents/TESTEUR.md`
  - Rôle : Génération tests exhaustifs
  - Output : Fichiers tests + rapport couverture
  - Règles : Unitaires, intégration, E2E
- [ ] Ajouter config dans `agent_config.py`
  ```python
  "TESTEUR": {
      "role": "Spécialiste Tests",
      "model": "gemini-2.0-flash",
      "temperature": 0.5,
      "max_tokens": 12288,
      "prompt_file": "config_agents/TESTEUR.md"
  }
  ```
- [ ] Tests unitaires `test_testeur.py`

**1.3 Modifier agent CODEUR**
- [ ] Mettre à jour prompt `config_agents/CODEUR.md`
  - Retirer génération tests (délégué à TESTEUR)
  - Focus sur qualité code uniquement
- [ ] Tester CODEUR sans tests

**1.4 Modifier agent VALIDATEUR**
- [ ] Mettre à jour prompt `config_agents/VALIDATEUR.md`
  - Ajouter validation cohérence architecture/code
  - Vérifier tests générés par TESTEUR
- [ ] Tester VALIDATEUR avec nouveaux critères

### Phase 2 : Système Missions (2-3h)

**2.1 Créer modèle Mission**
- [ ] Créer `backend/models/mission.py`
  - Classe `Mission` avec statuts
  - Méthode `is_complete()`
- [ ] Créer `backend/services/mission_manager.py`
  - CRUD missions
  - Détection fin mission
- [ ] Tests `test_mission.py`

**2.2 Intégrer missions dans orchestration**
- [ ] Modifier `orchestration.py`
  - Créer mission au début
  - Mettre à jour statut pendant workflow
  - Déclencher auto-indexation si COMPLETED
- [ ] Tester workflow complet avec missions

### Phase 3 : Gestion Projets & Versions (2-3h)

**3.1 Créer ProjectManager**
- [ ] Créer `backend/services/project_manager.py`
  - `detect_existing_project()`
  - `propose_action()`
- [ ] Intégrer dans orchestration
- [ ] Tester détection projet existant

**3.2 Créer VersionManager**
- [ ] Créer `backend/services/version_manager.py`
  - `get_project_version()`
  - `increment_version()`
  - `detect_change_type()`
- [ ] Créer fichier `.jarvis_version.json` par projet
- [ ] Tester versioning automatique

### Phase 4 : Auto-Indexation RAG (3-4h)

**4.1 Créer RAGAutoIndexer**
- [ ] Créer `backend/services/rag_auto_indexer.py`
  - `index_mission()`
  - `search_project()` (anti-doublon)
  - `update_project_index()`
  - `generate_project_docs()` (via JARVIS_Maître)
- [ ] Tests `test_rag_auto_indexer.py`

**4.2 Hook fin de mission**
- [ ] Modifier `orchestration.py`
  - Appeler `rag_auto_indexer.index_mission()` si mission COMPLETED
- [ ] Tester auto-indexation complète

**4.3 Restructurer Library RAG**
- [ ] Créer arborescence `RAG/library/` et `RAG/projects/`
- [ ] Migrer `KEAMDER_PROFILE.md` → `RAG/library/rules/`
- [ ] Créer `RAG/projects/index.json`
- [ ] Indexer dans ChromaDB

### Phase 5 : Profil Utilisateur Éditable (1-2h)

**5.1 Backend**
- [ ] Créer endpoints `/profile` (GET, PUT, POST avatar)
- [ ] Fonction `reindex_profile()`
- [ ] Tests API profil

**5.2 Frontend**
- [ ] Créer `frontend/profile.html`
- [ ] Formulaire édition profil
- [ ] Upload avatar
- [ ] Tester interface complète

### Phase 6 : Workflow Adaptatif (2-3h)

**6.1 Détection complexité**
- [ ] Créer `detect_project_complexity()` dans orchestration
- [ ] Fonction `estimate_file_count()`
- [ ] Tests détection

**6.2 Modes workflow**
- [ ] Implémenter `execute_fast_mode()` (≤3 fichiers)
- [ ] Implémenter `execute_complete_mode()` (>3 fichiers)
- [ ] Modifier prompt JARVIS_Maître (règle mode rapide)
- [ ] Tester les 2 modes

### Phase 7 : Optimisation Modèles Gemini (1h)

**7.1 Répartition modèles**
- [ ] Modifier `.env`
  ```env
  ARCHITECTE_MODEL=gemini-2.5-pro
  CODEUR_MODEL=gemini-2.5-pro
  TESTEUR_MODEL=gemini-2.0-flash
  VALIDATEUR_MODEL=gemini-3.1-pro-preview
  ```
- [ ] Tester quotas répartis

**7.2 Fallback**
- [ ] Ajouter `FALLBACK_MODELS` dans `gemini_provider.py`
- [ ] Implémenter logique fallback
- [ ] Tester fallback si quota épuisé

### Phase 8 : Tests & Validation (2-3h)

**8.1 Tests unitaires**
- [ ] Tests nouveaux agents (ARCHITECTE, TESTEUR)
- [ ] Tests système missions
- [ ] Tests ProjectManager, VersionManager
- [ ] Tests RAGAutoIndexer
- [ ] **Objectif** : 100% tests passants

**8.2 Tests live**
- [ ] Projet simple (calculatrice) → Mode rapide
- [ ] Projet complexe (API REST) → Mode complet
- [ ] Modification projet existant → Versioning
- [ ] Vérifier auto-indexation RAG
- [ ] Vérifier profil éditable

**8.3 Validation utilisateur**
- [ ] Tester workflow complet end-to-end
- [ ] Vérifier précision code généré
- [ ] Vérifier mémoire projets fonctionne
- [ ] Ajustements selon retours

### Phase 9 : Documentation & Nettoyage (1h)

**9.1 Documentation**
- [ ] Créer `docs/reference/GUIDE_5_AGENTS.md`
- [ ] Créer `docs/reference/GUIDE_MISSIONS.md`
- [ ] Créer `docs/reference/GUIDE_AUTO_INDEXATION.md`
- [ ] Mettre à jour `README.md`

**9.2 Nettoyage**
- [ ] Archiver anciens docs work
  ```bash
  mv docs/work/EXPLICATION_COMPLETE_JARVIS_VALENTIN.md \
     docs/history/archived_2026_03_07/
  ```
- [ ] Garder uniquement `ANALYSE_CRITIQUE_JARVIS_VALENTIN.md`
- [ ] Nettoyer code inutilisé

---

## 📋 ESTIMATION TOTALE

**Temps total** : 18-25 heures

**Répartition** :
- Phase 1 (Agents) : 3-4h
- Phase 2 (Missions) : 2-3h
- Phase 3 (Projets/Versions) : 2-3h
- Phase 4 (Auto-indexation) : 3-4h
- Phase 5 (Profil UI) : 1-2h
- Phase 6 (Workflow adaptatif) : 2-3h
- Phase 7 (Modèles Gemini) : 1h
- Phase 8 (Tests) : 2-3h
- Phase 9 (Documentation) : 1h

**Planning recommandé** :
- **Semaine 1** : Phases 1-3 (agents + missions + projets)
- **Semaine 2** : Phases 4-6 (RAG + profil + workflow)
- **Semaine 3** : Phases 7-9 (optimisation + tests + doc)

---

## 🎯 CHECKLIST VALIDATION FINALE

### Configuration
- [ ] 5 agents créés (JARVIS_Maître, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR)
- [ ] BASE conservé comme template (non utilisé)
- [ ] Modèles Gemini répartis (2475 RPM total)
- [ ] Fallback configuré

### Système Missions
- [ ] Modèle Mission implémenté
- [ ] Détection fin mission fonctionne
- [ ] Statuts mission corrects (PENDING → IN_PROGRESS → VALIDATING → COMPLETED)

### Gestion Projets
- [ ] Détection projet existant fonctionne
- [ ] Versioning automatique opérationnel
- [ ] Anti-doublon RAG vérifié

### Library RAG
- [ ] Arborescence `library/` et `projects/` créée
- [ ] Templates Python, Flutter, JavaScript créés
- [ ] Profil Keamder indexé
- [ ] Index projets (`projects/index.json`) créé

### Workflow
- [ ] Mode rapide (≤3 fichiers) fonctionne
- [ ] Mode complet (>3 fichiers) fonctionne
- [ ] Auto-indexation déclenchée fin mission

### Profil Utilisateur
- [ ] Interface édition profil opérationnelle
- [ ] Upload avatar fonctionne
- [ ] Synchronisation RAG automatique

### Tests
- [ ] Tests unitaires passent (100%)
- [ ] Tests live passent (calculatrice, API REST)
- [ ] Workflow complet validé par utilisateur

---

## 💡 POINTS CLÉS À RETENIR

### Équipe 5 Agents
**Justification** : Précision > Rapidité (besoin Valentin non-codeur)
- ARCHITECTE : Validation architecture AVANT code (sécurité)
- CODEUR : Focus qualité code uniquement
- TESTEUR : Tests exhaustifs séparés
- VALIDATEUR : Contrôle multi-niveaux
- JARVIS_Maître : Orchestration + détection fin mission

### Système Missions
**Clé** : Chaque demande = 1 mission avec statuts
- Permet détection fin de projet claire
- Gère validation utilisateur (VALIDATING)
- Déclenche auto-indexation (COMPLETED)

### Anti-Doublons
**Stratégie** : Clé unique `project_path`
- Recherche avant indexation
- Mise à jour atomique (supprimer + créer)
- Versioning sémantique automatique

### Workflow Adaptatif
**Optimisation** : Mode rapide vs complet
- ≤3 fichiers : Pas d'ARCHITECTE (2-3 min)
- >3 fichiers : Workflow complet (5-8 min)

---

**Date** : 7 mars 2026  
**Statut** : ✅ DOCUMENT UNIQUE CONSOLIDÉ  
**Prochaine étape** : Validation plan → Début implémentation Phase 1

**1.1 Restructurer Library RAG**
- [ ] Créer arborescence `RAG/library/` et `RAG/projects/`
- [ ] Migrer KEAMDER_PROFILE.md → `RAG/library/rules/keamder_profile.md`
- [ ] Créer `RAG/projects/index.json`

**1.2 Extraire templates depuis exemples**
- [ ] Script `extract_project_metadata.py`
- [ ] Extraire TerraNova → `RAG/projects/terranova/`
- [ ] Extraire UFM → `RAG/projects/ultimate_frisbee_manager/`
- [ ] Générer templates Python, Flutter

**1.3 Indexer dans ChromaDB**
- [ ] Lancer `python RAG/index_jarvis_library.py`
- [ ] Vérifier indexation : `curl http://localhost:5001/search?query=calculator`

### Phase 2 : Optimisation Agents (2-3h)

**2.1 Supprimer agent BASE**
- [ ] Créer `backend/utils/verify_completeness.py`
- [ ] Modifier `orchestration.py` : remplacer appel BASE par script
- [ ] Supprimer `backend/agents/base_agent.py` (si dédié)
- [ ] Mettre à jour `agent_config.py`

**2.2 Optimiser modèles Gemini**
- [ ] Modifier `.env` : BASE_MODEL=gemini-2.0-flash
- [ ] Ajouter fallback dans `gemini_provider.py`
- [ ] Tester quotas : `python test_tier1_models.py`

**2.3 Workflow adaptatif**
- [ ] Créer `detect_project_complexity()` dans `orchestration.py`
- [ ] Implémenter `execute_fast_mode()` et `execute_complete_mode()`
- [ ] Modifier prompt JARVIS_Maître : ajouter règle mode rapide

### Phase 3 : Mémoire Projets (3-4h)

**3.1 Auto-indexation**
- [ ] Créer `backend/services/rag_auto_indexer.py`
- [ ] Implémenter `extract_project_metadata()`
- [ ] Implémenter `generate_project_docs()` (appel JARVIS_Maître)
- [ ] Implémenter `index_project_to_rag()`

**3.2 Hook fin de projet**
- [ ] Modifier `orchestration.py` : ajouter `on_project_complete()`
- [ ] Appeler auto-indexer après validation VALIDATEUR
- [ ] Tester : créer projet → vérifier `RAG/projects/` mis à jour

**3.3 Profil utilisateur éditable**
- [ ] Créer endpoint `/api/profile` (GET, PUT)
- [ ] Interface frontend : formulaire édition profil
- [ ] Avatar : upload image → stockage local
- [ ] Sauvegarder dans `RAG/library/rules/keamder_profile.md`

### Phase 4 : Scripts & DevOps (1h)

**4.1 Améliorer scripts démarrage**
- [ ] Ajouter détection processus existants
- [ ] Créer fichier PID `.jarvis_pids.json`
- [ ] Créer `stop_jarvis.py`
- [ ] Tester : lancer 2x → détecte doublon

**4.2 Documentation**
- [ ] Créer `docs/reference/GUIDE_LIBRARY_RAG.md`
- [ ] Créer `docs/reference/GUIDE_AUTO_INDEXATION.md`
- [ ] Mettre à jour `README.md`

### Phase 5 : Tests & Validation (1-2h)

**5.1 Tests unitaires**
- [ ] Test `verify_completeness.py`
- [ ] Test `detect_project_complexity()`
- [ ] Test `rag_auto_indexer.py`

**5.2 Tests live**
- [ ] Projet simple (calculatrice) → Mode rapide
- [ ] Projet complexe (API REST) → Mode complet
- [ ] Vérifier auto-indexation fonctionne
- [ ] Vérifier RAG utilise projets précédents

**5.3 Validation utilisateur**
- [ ] Tester workflow complet
- [ ] Vérifier profil éditable
- [ ] Vérifier mémoire projets

---

## 📋 CHECKLIST VALIDATION

### Configuration
- [ ] Gemini Tier 1 opérationnel (vérifier quotas)
- [ ] Modèles répartis (gemini-2.5-pro, gemini-2.0-flash, gemini-3.1-pro)
- [ ] Fallback configuré

### Library RAG
- [ ] Arborescence `library/` et `projects/` créée
- [ ] Templates Python, Flutter, JavaScript créés
- [ ] Profil Keamder indexé
- [ ] Index projets (`projects/index.json`) créé

### Agents
- [ ] BASE supprimé (remplacé par script)
- [ ] 3 agents opérationnels (JARVIS_Maître, CODEUR, VALIDATEUR)
- [ ] Workflow adaptatif implémenté

### Mémoire Projets
- [ ] Auto-indexation fonctionne
- [ ] Nouveaux projets ajoutés automatiquement à RAG
- [ ] Projets précédents utilisés comme référence

### Scripts
- [ ] Détection doublons fonctionne
- [ ] Fichier PID créé/supprimé correctement
- [ ] `stop_jarvis.py` arrête proprement

### Tests
- [ ] Tests unitaires passent (100%)
- [ ] Tests live passent (calculatrice, API REST)
- [ ] Auto-indexation testée

---

## 💰 ESTIMATION COÛTS & GAINS

### Coûts Actuels (4 agents)
- JARVIS_Maître : $0.01/projet
- CODEUR : $0.03/projet
- BASE : $0.02/projet
- VALIDATEUR : $0.03/projet
- **Total** : **$0.09/projet**

### Coûts Optimisés (3 agents)
- JARVIS_Maître : $0.01/projet
- CODEUR : $0.03/projet
- VALIDATEUR : $0.03/projet
- **Total** : **$0.07/projet**

**Économie** : **22% par projet**

### Quotas Actuels vs Optimisés

| Configuration | RPM Total | Projets/heure | Projets/jour |
|---------------|-----------|---------------|--------------|
| **Actuelle** | 175 | 35 | 840 |
| **Optimisée** | 2325 | 465 | 11160 |

**Gain** : **13x plus de capacité**

---

## 🎯 RÉSUMÉ EXÉCUTIF — ACTIONS PRIORITAIRES

### Priorité 1 : Library RAG (CRITIQUE)
**Pourquoi** : Sans Library, CODEUR génère code aléatoire
**Actions** :
1. Créer arborescence `RAG/library/` et `RAG/projects/`
2. Extraire templates depuis exemples projets
3. Indexer dans ChromaDB

**Temps** : 1-2h  
**Impact** : ⭐⭐⭐⭐⭐ (critique)

### Priorité 2 : Optimiser Agents (IMPORTANT)
**Pourquoi** : Économie coûts + quotas + workflow plus rapide
**Configuration validée : 3 agents actifs + BASE template**
- JARVIS_Maître (orchestrateur)
- CODEUR (génération code + tests)
- VALIDATEUR (contrôle qualité)
- BASE (modèle pour futurs agents, non utilisé dans workflow)
3. Workflow adaptatif (mode rapide vs complet)

**Temps** : 2-3h  
**Impact** : ⭐⭐⭐⭐ (important)

### Priorité 3 : Mémoire Projets (MOYEN)
**Pourquoi** : Capitalisation sur projets précédents
**Actions** :
1. Auto-indexation fin de projet
2. Génération docs projet (architecture, décisions, leçons)
3. Mise à jour index global

**Temps** : 3-4h  
**Impact** : ⭐⭐⭐ (moyen terme)

### Priorité 4 : Scripts & DevOps (MINEUR)
**Pourquoi** : Confort utilisation
**Actions** :
1. Détection doublons
2. Fichier PID
3. Script stop dédié

**Temps** : 1h  
**Impact** : ⭐⭐ (confort)

---

## 📞 QUESTIONS OUVERTES POUR VALENTIN

### 1. Équipe d'Agents
**Question** : Es-tu d'accord pour supprimer BASE et passer à 3 agents ?
- ✅ Oui → Économie 22% + workflow plus rapide
- ❌ Non → Garder 4 agents (justification ?)

### 2. Workflow Adaptatif
**Question** : Veux-tu un mode "rapide" sans validation pour projets simples ?
- ✅ Oui → Projets ≤3 fichiers générés directement
- ❌ Non → Toujours demander validation

### 3. Auto-Indexation
**Question** : Veux-tu que JARVIS indexe automatiquement chaque projet terminé ?
- ✅ Oui → Mémoire projets automatique
- ❌ Non → Indexation manuelle uniquement

### 4. Profil Utilisateur
**Question** : Veux-tu pouvoir éditer ton profil via interface ?
- ✅ Oui → Formulaire + avatar
- ❌ Non → Édition manuelle fichier markdown

### 5. Modèles Gemini
**Question** : Es-tu d'accord pour répartir sur plusieurs modèles (gain 13x quotas) ?
- ✅ Oui → BASE sur gemini-2.0-flash (2000 RPM)
- ❌ Non → Tout sur gemini-2.5-pro (150 RPM)

---

**Date** : 7 mars 2026  
**Statut** : ⏳ EN ATTENTE VALIDATION UTILISATEUR  
**Prochaine étape** : Réponses aux questions → Implémentation Phase 1
