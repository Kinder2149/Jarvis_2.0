# Guide Utilisateur — JARVIS 2.0 Optimisé

**Version** : 2.0  
**Date** : 7 mars 2026  
**Destinataire** : Valentin (Chef de projet IA, non-codeur)

---

## 🎯 Vue d'Ensemble

JARVIS 2.0 est votre assistant IA personnel optimisé avec **5 agents spécialisés** travaillant en équipe pour transformer vos idées en code fonctionnel.

### Équipe 5 Agents

| Agent | Rôle | Responsabilité |
|-------|------|----------------|
| **JARVIS_Maître** | Orchestrateur | Analyse votre demande, coordonne les agents |
| **ARCHITECTE** | Concepteur | Conçoit l'architecture AVANT le code |
| **CODEUR** | Développeur | Génère le code propre et fonctionnel |
| **TESTEUR** | Testeur | Crée les tests exhaustifs (80%+ couverture) |
| **VALIDATEUR** | Contrôleur qualité | Vérifie la qualité et détecte les bugs |

---

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Cloner le projet
cd "d:\Coding\AppWindows\Jarvis 2.0"

# Installer dépendances
pip install -r requirements.txt

# Configurer .env
cp .env.example .env
# Éditer .env et ajouter votre GEMINI_API_KEY
```

### 2. Obtenir Clé API Gemini

1. Aller sur https://aistudio.google.com/app/apikey
2. Créer une nouvelle clé API
3. Activer Cloud Billing (Tier 1 gratuit)
4. Copier la clé dans `.env`

### 3. Lancer JARVIS

```bash
# Démarrer le backend
python -m backend.app

# Ouvrir le frontend
# http://localhost:8000
```

### 4. Tester la Configuration

```bash
# Tester les modèles Gemini
python scripts/test_gemini_config.py

# Résultat attendu : 5/5 agents OK
```

---

## 💡 Comment Utiliser JARVIS

### Workflow Automatique

JARVIS détecte automatiquement la complexité de votre projet et choisit le workflow adapté :

**Projet Simple (≤3 fichiers)** → Mode RAPIDE
- CODEUR génère le code
- TESTEUR crée les tests
- VALIDATEUR vérifie la qualité
- **Temps** : 2-3 minutes

**Projet Complexe (>3 fichiers)** → Mode COMPLET
- ARCHITECTE conçoit l'architecture
- **Vous validez** l'architecture
- CODEUR génère le code selon l'architecture
- TESTEUR crée les tests
- VALIDATEUR vérifie tout
- **Temps** : 5-8 minutes

---

## 📝 Exemples d'Utilisation

### Exemple 1 : Calculatrice Simple (Mode RAPIDE)

**Votre demande** :
```
Crée une calculatrice Python simple avec addition, soustraction, 
multiplication et division.
```

**JARVIS fait** :
1. Détecte : Projet simple (1-2 fichiers)
2. CODEUR génère `calculator.py`
3. TESTEUR génère `test_calculator.py`
4. VALIDATEUR vérifie
5. Vous livre le code prêt à l'emploi

**Résultat** : Code + tests en 2-3 minutes

---

### Exemple 2 : API REST (Mode COMPLET)

**Votre demande** :
```
Crée une API REST avec FastAPI pour gérer une liste de tâches.
Fonctionnalités : créer, lire, modifier, supprimer des tâches.
Stockage JSON.
```

**JARVIS fait** :
1. Détecte : Projet complexe (>3 fichiers)
2. ARCHITECTE propose :
   ```
   - models/task.py (modèle Pydantic)
   - storage/json_storage.py (persistance)
   - api/routes.py (endpoints FastAPI)
   - tests/test_api.py (tests)
   ```
3. **Vous validez** l'architecture
4. CODEUR génère tous les fichiers
5. TESTEUR crée les tests
6. VALIDATEUR vérifie cohérence
7. Vous livre le projet complet

**Résultat** : API complète + tests en 5-8 minutes

---

## 🔧 Configuration Avancée

### Modèles Gemini par Agent

**Configuration optimale** (déjà dans `.env.example`) :

```env
# JARVIS_Maître : Orchestration précise
JARVIS_MAITRE_MODEL=gemini-2.5-pro

# ARCHITECTE : Conception critique
ARCHITECTE_MODEL=gemini-2.5-pro

# CODEUR : Qualité code maximale
CODEUR_MODEL=gemini-2.5-pro

# TESTEUR : Tests rapides
TESTEUR_MODEL=gemini-2.0-flash

# VALIDATEUR : Contrôle précis
VALIDATEUR_MODEL=gemini-3.1-pro-preview
```

**Quotas** : 2475 RPM total (14x plus qu'avant)

---

### Personnalisation Agents

**Modifier les prompts** :
- Fichiers dans `config_agents/`
- `ARCHITECTE.md` : Instructions ARCHITECTE
- `CODEUR.md` : Instructions CODEUR
- `TESTEUR.md` : Instructions TESTEUR
- `VALIDATEUR.md` : Instructions VALIDATEUR

**Modifier les paramètres** :
- Fichier `backend/agents/agent_config.py`
- `temperature` : Créativité (0.0-1.0)
- `max_tokens` : Longueur réponse max

---

## 📊 Suivi des Missions

### Logs Détaillés

**Fichier** : `backend/logs/jarvis_audit.log`

**Contenu** :
```json
{
  "timestamp": "2026-03-07T18:45:00",
  "agent": "CODEUR",
  "action": "handle_request",
  "session_id": "mission_abc123",
  "details": {"message_count": 2}
}
```

### Missions Sauvegardées

**Fichier** : `backend/data/missions.json`

**Contenu** :
```json
{
  "mission_abc123": {
    "mission_id": "mission_abc123",
    "user_request": "Crée une calculatrice...",
    "status": "completed",
    "files_created": ["calculator.py", "test_calculator.py"],
    "created_at": "2026-03-07T18:45:00"
  }
}
```

---

## ⚠️ Résolution Problèmes

### Erreur : "Quota épuisé"

**Cause** : Trop de requêtes en peu de temps

**Solution** :
1. Attendre 1 minute (reset RPM)
2. Vérifier quotas : https://aistudio.google.com/app/apikey
3. Si RPD épuisé : attendre minuit (Pacific Time)

---

### Erreur : "GEMINI_API_KEY non configurée"

**Cause** : Clé API manquante dans `.env`

**Solution** :
1. Vérifier fichier `.env` existe
2. Ajouter `GEMINI_API_KEY=votre_cle_ici`
3. Redémarrer backend

---

### Erreur : "Architecture non validée"

**Cause** : Mode COMPLET en attente validation

**Solution** :
1. Consulter l'architecture proposée
2. Valider ou rejeter via interface
3. Si validé, workflow continue automatiquement

---

### Code généré mais fichiers non créés

**Cause** : Système écriture fichiers non implémenté (TODO)

**Solution temporaire** :
1. Copier le code depuis la réponse
2. Créer les fichiers manuellement
3. Coller le code

**Solution future** : Implémentation parser + écriture automatique

---

## 📈 Bonnes Pratiques

### 1. Soyez Précis dans vos Demandes

**❌ Mauvais** :
```
Fais-moi une app
```

**✅ Bon** :
```
Crée une API REST avec FastAPI pour gérer des utilisateurs.
Fonctionnalités : inscription, connexion, profil.
Stockage : SQLite avec Pydantic.
```

---

### 2. Indiquez la Stack si Nécessaire

**Par défaut** : Python + FastAPI + SQLite

**Si différent** :
```
Crée une API REST en Node.js avec Express et MongoDB
pour gérer des articles de blog.
```

---

### 3. Validez l'Architecture (Mode COMPLET)

**Pourquoi** : Évite refonte complète si architecture inadaptée

**Comment** :
1. Lisez la proposition ARCHITECTE
2. Vérifiez structure fichiers cohérente
3. Validez si OK, rejetez si modifications nécessaires

---

### 4. Consultez les Logs en Cas de Problème

**Fichier** : `backend/logs/jarvis_audit.log`

**Cherchez** :
- Erreurs (action: "handle_error")
- Temps de réponse longs
- Quotas épuisés

---

## 🎓 Concepts Clés

### Cycle ARRF

**Phases** :
- **Analyse** : JARVIS_Maître + ARCHITECTE
- **Réflexion** : ARCHITECTE + TESTEUR
- **Remise en Question** : VALIDATEUR
- **Fixation** : CODEUR + TESTEUR

**Bénéfice** : Qualité maximale, bugs minimaux

---

### Boucle Correction

**Fonctionnement** :
1. VALIDATEUR détecte problème
2. CODEUR corrige (max 2 fois)
3. VALIDATEUR re-vérifie

**Bénéfice** : Code validé automatiquement

---

### Versioning Automatique

**Format** : MAJOR.MINOR.PATCH

**Détection automatique** :
- "refonte", "breaking" → MAJOR (1.0.0 → 2.0.0)
- "ajoute", "nouvelle fonctionnalité" → MINOR (1.0.0 → 1.1.0)
- "corrige", "bug" → PATCH (1.0.0 → 1.0.1)

**Fichier** : `.jarvis_version.json` dans chaque projet

---

## 📚 Ressources

### Documentation Technique

- `docs/reference/CONFIGURATION_GEMINI_5_AGENTS.md` : Configuration Gemini
- `docs/work/PHASE_6_RAPPORT_FINAL.md` : Workflow adaptatif
- `docs/work/VERIFICATION_PHASE_6_COMPLETE.md` : Validation technique

### Scripts Utiles

- `scripts/test_gemini_config.py` : Tester configuration
- `scripts/list_gemini_models.py` : Lister modèles disponibles

### Support

- Logs : `backend/logs/jarvis_audit.log`
- Missions : `backend/data/missions.json`
- GitHub Issues : (si applicable)

---

## 🚀 Prochaines Étapes

### Utilisation Immédiate

1. ✅ Configuration terminée
2. ✅ Agents opérationnels
3. ✅ Workflow adaptatif fonctionnel

**Vous pouvez** : Créer vos premiers projets !

---

### Améliorations Futures (TODO)

1. **Écriture fichiers automatique** : Parser réponses agents → créer fichiers
2. **Interface web** : Dashboard missions, validation architecture
3. **Tests automatisés** : Exécution tests générés
4. **Déploiement** : Scripts déploiement projets

---

## 💬 FAQ

**Q : Combien de projets puis-je créer par jour ?**  
R : ~10-20 projets complexes, ~50-100 projets simples (quotas Gemini)

**Q : JARVIS peut-il modifier du code existant ?**  
R : Oui, indiquez le chemin du projet dans votre demande

**Q : Les tests sont-ils exécutés automatiquement ?**  
R : Non (TODO), vous devez les exécuter manuellement

**Q : Puis-je utiliser d'autres modèles que Gemini ?**  
R : Non, JARVIS 2.0 est optimisé pour Gemini uniquement

**Q : Comment archiver un projet ?**  
R : Les projets complétés sont auto-indexés dans `RAG/projects/`

---

**JARVIS 2.0 est prêt à transformer vos idées en code. Bonne création !** 🚀
