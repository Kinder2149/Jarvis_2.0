# Vérification Agents + RAG + Librairie - JARVIS 2.0

**Date** : 08 mars 2026  
**Objectif** : Vérifier configuration agents, nettoyage code, correspondance Librairie/RAG

---

## ✅ 1. CONFIGURATION AGENTS

### 1.1 Agents Disponibles

**6 agents configurés** dans `backend/agents/agent_config.py` :

| Agent | Prompt File | Temperature | Max Tokens | Min Delay |
|-------|-------------|-------------|------------|-----------|
| BASE | `config_agents/BASE.md` | 0.7 | 4096 | 6.0s |
| JARVIS_Maître | `config_agents/JARVIS_MAITRE.md` | 0.3 | 4096 | 4.0s |
| ARCHITECTE | `config_agents/ARCHITECTE.md` | 0.3 | 8192 | 8.0s |
| CODEUR | `config_agents/CODEUR.md` | 0.3 | 16384 | 10.0s |
| TESTEUR | `config_agents/TESTEUR.md` | 0.5 | 8192 | 8.0s |
| VALIDATEUR | `config_agents/VALIDATEUR.md` | 0.5 | 4096 | 6.0s |

### 1.2 Fichiers Prompts Existants

✅ **Tous les fichiers prompts existent** :
- `config_agents/BASE.md`
- `config_agents/JARVIS_MAITRE.md`
- `config_agents/ARCHITECTE.md`
- `config_agents/CODEUR.md`
- `config_agents/TESTEUR.md`
- `config_agents/VALIDATEUR.md`

### 1.3 Vérification System Prompts

**Mécanisme de chargement** (`base_agent.py` L55-85) :
- Charge le prompt depuis le fichier `.md`
- Extrait le contenu après les métadonnées
- Injecte automatiquement dans `conversation_messages` (L231-232)

**✅ Tous les agents utilisent leur prompt local** :
- Pas de référence à Mistral Cloud
- Pas de `agent_id` externe
- Prompts locaux chargés depuis `config_agents/`

### 1.4 Provider Utilisé

**✅ GeminiProvider uniquement** :
- Aucune référence à `MistralProvider` dans le code
- `backend/ia/providers/gemini_provider.py` utilisé
- Configuration dans `.env` : `JARVIS_MAITRE_MODEL=gemini-2.5-pro`

---

## ✅ 2. NETTOYAGE CODE

### 2.1 Imports Obsolètes

**Vérification** : Aucun import Mistral trouvé
```bash
grep -r "import.*mistral\|from.*mistral\|MistralProvider" backend/
# Résultat : No results found
```

**✅ Code propre** : Pas d'imports obsolètes

### 2.2 Fichiers Obsolètes Backend

**Vérification providers** :
- ✅ `backend/ia/providers/gemini_provider.py` (utilisé)
- ✅ `backend/ia/providers/base_provider.py` (utilisé)
- ❌ Pas de `mistral_provider.py` ou fichiers obsolètes

### 2.3 Documentation Archivée

**✅ Nettoyage effectué** (08/03/2026) :
- 8 fichiers archivés → `docs/history/20260308_mission_tests/`
- 1 fichier conservé : `PLAN_CORRECTION_COMPLET_JARVIS_20260308.md`
- 3 rapports créés dans `docs/work/`

### 2.4 Structure Propre

**Backend** :
```
backend/
├── agents/          ✅ (agent_config.py, agent_factory.py, base_agent.py)
├── api.py           ✅ (routes FastAPI)
├── db/              ✅ (database.py)
├── ia/providers/    ✅ (gemini_provider.py, base_provider.py)
├── models/          ✅ (mission.py, mission_context.py, etc.)
└── services/        ✅ (orchestration.py, rag_client.py, parsers, etc.)
```

**Pas de fichiers obsolètes détectés**

---

## ⚠️ 3. CORRESPONDANCE LIBRAIRIE / RAG

### 3.1 RAG Library (Serveur RAG)

**Structure actuelle** (`RAG/library/`) :
```
RAG/library/
├── assets/          (0 items)
├── patterns/        (6 items)
│   ├── api_rest_fastapi.md      (8.5 Ko)
│   ├── crud_complete.md         (6.7 Ko)
│   ├── pydantic_models.md       (6.7 Ko)
│   ├── storage_json.md          (4.3 Ko)
│   ├── tests_pytest.md          (6.3 Ko)
│   └── todo_app_example.md      (17.5 Ko)
├── rules/           (1 item)
└── templates/       (1 item)
```

**Total** : 6 patterns (50.0 Ko)

### 3.2 Onglet Librairie (Frontend)

**Catégories définies** (`frontend/js/views/library.js` L10-36) :

| Catégorie | Nom | Documents Attendus |
|-----------|-----|-------------------|
| `personal` | Personnel | 11 docs (profil, workflow, architecture, règles, etc.) |
| `libraries` | Librairies & Frameworks | 10 docs (FastAPI, Pytest, Pydantic, etc.) |
| `methodologies` | Méthodologies | 9 docs (Audit, Gouvernance, Revue code, etc.) |
| `prompts` | Prompts & Templates | 6 docs (Délégation CODEUR, Vérification BASE, etc.) |
| `tools` | Outils & Productivité | 4 docs (VS Code, PowerShell, Debugging, Gemini) |

**Total attendu** : 40 documents

### 3.3 ❌ PROBLÈME : Désynchronisation

**RAG Library** : 6 patterns techniques (CRUD, API REST, tests, etc.)
**Onglet Librairie** : 40 documents personnels (profil, workflow, conventions, etc.)

**Constat** :
- L'onglet Librairie affiche des catégories qui **ne correspondent PAS** au RAG actuel
- Le RAG contient uniquement des **patterns de code** (créés aujourd'hui)
- L'onglet Librairie attend des **documents personnels** (profil Keamder, workflow, etc.)

**Origine** :
- L'onglet Librairie a été conçu pour une **Knowledge Base personnelle**
- Le RAG actuel est une **librairie de patterns de code**
- Ce sont **deux systèmes différents** qui ne devraient pas être confondus

---

## 🔧 4. RECOMMANDATIONS

### 4.1 Clarifier la Séparation

**Option A : Renommer l'onglet Librairie**
- Renommer "Librairie" → "Knowledge Base" ou "Documents Personnels"
- Créer un nouvel onglet "Patterns RAG" pour les patterns de code
- Séparer clairement les deux systèmes

**Option B : Fusionner les systèmes**
- Migrer les patterns RAG vers la Knowledge Base
- Ajouter catégorie "patterns" dans la Knowledge Base
- Utiliser un seul système unifié

**Option C : Conserver séparation actuelle**
- Onglet Librairie = Knowledge Base personnelle (40 docs)
- RAG = Patterns de code (6 patterns)
- Clarifier dans l'UI que ce sont deux systèmes distincts

### 4.2 Vérifier Documents Knowledge Base

**Action** : Vérifier si les 40 documents attendus existent dans la base de données
```sql
SELECT category, COUNT(*) FROM library_documents GROUP BY category;
```

Si les documents n'existent pas, deux options :
1. Créer les documents manquants
2. Mettre à jour `CATEGORY_METADATA` pour refléter la réalité

### 4.3 Intégration RAG dans l'UI

**Actuellement** :
- RAG utilisé par CODEUR (backend)
- Pas d'interface utilisateur pour voir les patterns RAG

**Proposition** :
- Ajouter onglet "Patterns RAG" dans l'UI
- Afficher les 6 patterns disponibles
- Permettre consultation des patterns

---

## ✅ 5. RÉSUMÉ VÉRIFICATION

### Configuration Agents

| Élément | Statut | Détails |
|---------|--------|---------|
| Prompts locaux | ✅ OK | 6 fichiers `.md` dans `config_agents/` |
| System prompts chargés | ✅ OK | Mécanisme `_load_system_prompt()` fonctionnel |
| Provider Gemini | ✅ OK | Aucune référence Mistral |
| Imports propres | ✅ OK | Pas d'imports obsolètes |

### Nettoyage Code

| Élément | Statut | Détails |
|---------|--------|---------|
| Imports Mistral | ✅ OK | Aucun trouvé |
| Fichiers obsolètes | ✅ OK | Aucun détecté |
| Documentation archivée | ✅ OK | 8 fichiers dans `history/` |
| Structure backend | ✅ OK | Propre et organisée |

### Librairie / RAG

| Élément | Statut | Détails |
|---------|--------|---------|
| RAG Library | ✅ OK | 6 patterns de code (50 Ko) |
| Onglet Librairie | ⚠️ ATTENTION | Attend 40 docs personnels |
| Correspondance | ❌ NON | Deux systèmes différents |
| Action requise | ⏳ DÉCISION | Clarifier séparation ou fusionner |

---

## 🎯 ACTIONS RECOMMANDÉES

### Immédiat

1. **Vérifier base de données** : Compter documents dans `library_documents`
2. **Décider architecture** : Knowledge Base séparée du RAG ou fusionnée ?
3. **Mettre à jour UI** : Clarifier onglet Librairie vs Patterns RAG

### Court terme

4. **Créer onglet Patterns RAG** (si séparation)
5. **Documenter différence** : KB personnelle vs Patterns code
6. **Tester intégration** : Vérifier que RAG fonctionne avec CODEUR

---

**Conclusion** : Configuration agents ✅ propre, code ✅ nettoyé, mais **désynchronisation Librairie/RAG** à clarifier.
