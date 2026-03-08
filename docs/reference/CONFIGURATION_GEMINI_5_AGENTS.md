# Configuration Gemini 5 Agents — JARVIS 2.0

**Date** : 7 mars 2026  
**Version** : 1.0  
**Tier** : Tier 1 (gratuit avec facturation activée)

---

## 🎯 Objectif

Optimiser la répartition des modèles Gemini pour maximiser :
- **Performance** : Qualité code et architecture
- **Vitesse** : Temps de réponse adapté par agent
- **Quotas** : Répartition 2475 RPM (vs 175 RPM avant = 14x plus)
- **Coût** : 100% gratuit (Tier 1)

---

## 📊 Configuration Optimale Validée

### Mapping Agent → Modèle

| Agent | Modèle | RPM | TPM | RPD | Raison |
|-------|--------|-----|-----|-----|--------|
| **JARVIS_Maître** | `gemini-2.5-pro` | 150 | 2M | 1K | Orchestration précise, cycle ARRF complet |
| **ARCHITECTE** | `gemini-2.5-pro` | 150 | 2M | 1K | Conception architecture critique, clarté non-codeur |
| **CODEUR** | `gemini-2.5-pro` | 150 | 2M | 1K | Qualité code maximale, patterns complexes |
| **TESTEUR** | `gemini-2.0-flash` | 2K | 4M | Illimité | Génération tests rapide, volume élevé |
| **VALIDATEUR** | `gemini-3.1-pro-preview` | 25 | 5M | 255 | Contrôle qualité précis, détection bugs |
| **BASE** | `gemini-2.5-pro` | 150 | 2M | 1K | Template (non utilisé workflow) |

**Total RPM** : 2475 RPM (150×4 + 2000 + 25)

---

## 🔧 Configuration .env

### Variables Obligatoires

```env
# Clé API Gemini (obtenir sur https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=votre_cle_api_ici

# Modèle par défaut
GEMINI_MODEL=gemini-2.5-pro

# JARVIS_Maître : Orchestrateur
JARVIS_MAITRE_PROVIDER=gemini
JARVIS_MAITRE_MODEL=gemini-2.5-pro

# ARCHITECTE : Conception architecture
ARCHITECTE_PROVIDER=gemini
ARCHITECTE_MODEL=gemini-2.5-pro

# CODEUR : Génération code
CODEUR_PROVIDER=gemini
CODEUR_MODEL=gemini-2.5-pro

# TESTEUR : Génération tests
TESTEUR_PROVIDER=gemini
TESTEUR_MODEL=gemini-2.0-flash

# VALIDATEUR : Contrôle qualité
VALIDATEUR_PROVIDER=gemini
VALIDATEUR_MODEL=gemini-3.1-pro-preview

# BASE : Template
BASE_PROVIDER=gemini
BASE_MODEL=gemini-2.5-pro
```

---

## 📈 Justification Choix Modèles

### JARVIS_Maître : gemini-2.5-pro
**Pourquoi Pro ?**
- Orchestration complexe (détection phases ARRF, gestion workflow)
- Communication claire avec non-codeur (Valentin)
- Décisions critiques (délégation, validation)

**Pourquoi pas Flash ?**
- Besoin précision > vitesse
- Erreur orchestration = cascade d'erreurs

---

### ARCHITECTE : gemini-2.5-pro
**Pourquoi Pro ?**
- Conception architecture = décision critique
- Clarté pour non-codeur (explications simples)
- Justification choix architecturaux
- Anticipation extensions futures

**Pourquoi pas Flash ?**
- Architecture mal conçue = refonte complète
- Coût erreur très élevé

---

### CODEUR : gemini-2.5-pro
**Pourquoi Pro ?**
- Qualité code maximale
- Patterns complexes (Pydantic v2, Storage JSON, etc.)
- Respect strict conventions
- Pas de doublons, pas de bugs

**Pourquoi pas Flash ?**
- Code = livrable final
- Bugs = perte temps validation/correction

---

### TESTEUR : gemini-2.0-flash
**Pourquoi Flash ?**
- Génération tests = tâche répétitive
- Volume élevé (80%+ couverture)
- Vitesse importante (pas de blocage workflow)
- 2000 RPM = pas de limite pratique

**Pourquoi pas Pro ?**
- Tests suivent patterns standards (AAA)
- Pas de décision architecturale
- Coût/bénéfice défavorable

---

### VALIDATEUR : gemini-3.1-pro-preview
**Pourquoi 3.1 Pro ?**
- Contrôle qualité multi-niveaux (architecture + code + tests)
- Détection bugs subtils
- Validation cohérence globale
- Modèle le plus récent et précis

**Pourquoi pas 2.5 Pro ?**
- 3.1 Pro = meilleure détection erreurs
- 25 RPM suffisant (1 validation par mission)

---

## ⚡ Optimisations Quotas

### Répartition RPM par Workflow

**Mode RAPIDE (≤3 fichiers)** :
```
JARVIS_Maître : 1 appel (analyse)
CODEUR : 1-2 appels (génération + correction si nécessaire)
TESTEUR : 1 appel (tests)
VALIDATEUR : 1-2 appels (validation + re-validation)

Total : 4-6 appels
Temps : 2-3 min
RPM utilisé : ~6 RPM
```

**Mode COMPLET (>3 fichiers)** :
```
JARVIS_Maître : 1 appel (analyse)
ARCHITECTE : 1 appel (architecture)
[PAUSE validation USER]
CODEUR : 2-3 appels (génération itérative)
TESTEUR : 1 appel (tests)
VALIDATEUR : 1-2 appels (validation + re-validation)

Total : 6-8 appels
Temps : 5-8 min
RPM utilisé : ~8 RPM
```

**Capacité théorique** :
- Mode RAPIDE : 2475 RPM / 6 = **412 projets/min**
- Mode COMPLET : 2475 RPM / 8 = **309 projets/min**

**Capacité pratique (mono-utilisateur)** :
- ~10-20 projets/jour
- Aucun risque dépassement quotas

---

## 🔄 Système Fallback

### Stratégie Fallback par Agent

**Si quota épuisé** :

| Agent | Modèle Principal | Fallback 1 | Fallback 2 |
|-------|------------------|------------|------------|
| JARVIS_Maître | gemini-2.5-pro | gemini-2.0-flash | gemini-3-flash-preview |
| ARCHITECTE | gemini-2.5-pro | gemini-2.0-flash | gemini-3-flash-preview |
| CODEUR | gemini-2.5-pro | gemini-2.0-flash | gemini-3-flash-preview |
| TESTEUR | gemini-2.0-flash | gemini-2.0-flash-lite | gemini-3-flash-preview |
| VALIDATEUR | gemini-3.1-pro-preview | gemini-2.5-pro | gemini-2.0-flash |

### Implémentation Fallback

```python
# backend/ia/providers/gemini_provider.py

FALLBACK_MODELS = {
    "gemini-2.5-pro": ["gemini-2.0-flash", "gemini-3-flash-preview"],
    "gemini-2.0-flash": ["gemini-2.0-flash-lite", "gemini-3-flash-preview"],
    "gemini-3.1-pro-preview": ["gemini-2.5-pro", "gemini-2.0-flash"],
}

async def generate_with_fallback(model: str, messages: list):
    """Génère réponse avec fallback automatique si quota épuisé"""
    try:
        return await generate(model, messages)
    except QuotaExceededError:
        fallbacks = FALLBACK_MODELS.get(model, [])
        for fallback_model in fallbacks:
            try:
                logger.warning(f"Quota épuisé pour {model}, fallback vers {fallback_model}")
                return await generate(fallback_model, messages)
            except QuotaExceededError:
                continue
        raise QuotaExceededError("Tous les modèles épuisés")
```

---

## 🧪 Validation Configuration

### Script de Test

```python
# scripts/test_gemini_config.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

AGENTS = {
    "JARVIS_Maître": os.getenv("JARVIS_MAITRE_MODEL"),
    "ARCHITECTE": os.getenv("ARCHITECTE_MODEL"),
    "CODEUR": os.getenv("CODEUR_MODEL"),
    "TESTEUR": os.getenv("TESTEUR_MODEL"),
    "VALIDATEUR": os.getenv("VALIDATEUR_MODEL"),
}

def test_agent_model(agent_name: str, model_name: str):
    """Teste si modèle est accessible"""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Test")
        print(f"✅ {agent_name}: {model_name} - OK")
        return True
    except Exception as e:
        print(f"❌ {agent_name}: {model_name} - ERREUR: {e}")
        return False

def main():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    print("🔍 Test Configuration Gemini 5 Agents\n")
    
    results = {}
    for agent, model in AGENTS.items():
        results[agent] = test_agent_model(agent, model)
    
    print(f"\n📊 Résultats: {sum(results.values())}/{len(results)} agents OK")
    
    if all(results.values()):
        print("✅ Configuration validée")
    else:
        print("❌ Configuration incomplète")

if __name__ == "__main__":
    main()
```

---

## 📝 Checklist Installation

### Étape 1 : Obtenir Clé API
- [ ] Aller sur https://aistudio.google.com/app/apikey
- [ ] Créer nouvelle clé API
- [ ] Activer Cloud Billing (Tier 1)

### Étape 2 : Configurer .env
- [ ] Copier `.env.example` vers `.env`
- [ ] Renseigner `GEMINI_API_KEY`
- [ ] Vérifier variables agents (déjà configurées)

### Étape 3 : Valider Configuration
- [ ] Exécuter `python scripts/test_gemini_config.py`
- [ ] Vérifier 5/5 agents OK

### Étape 4 : Test Live
- [ ] Lancer backend : `python -m backend.app`
- [ ] Tester endpoint `/api/agents`
- [ ] Vérifier mapping modèles correct

---

## ⚠️ Points d'Attention

### 1. Quotas RPD Limités
**gemini-2.5-pro** : 1000 RPD (Requests Per Day)
**gemini-3.1-pro-preview** : 255 RPD

**Impact** :
- ~10-20 projets/jour max (mode COMPLET)
- ~50-100 projets/jour max (mode RAPIDE)

**Mitigation** :
- Workflow adaptatif (RAPIDE par défaut)
- Fallback automatique si quota épuisé

---

### 2. Modèle 3.1 Pro Preview
**Statut** : Preview (peut changer)

**Risques** :
- Nom API peut changer
- Quotas peuvent changer
- Disponibilité non garantie

**Mitigation** :
- Fallback vers gemini-2.5-pro
- Monitoring quotas

---

### 3. Coût Tier 1
**Statut** : Gratuit avec facturation activée

**Attention** :
- Tier 1 = gratuit MAIS nécessite carte bancaire
- Pas de dépassement automatique (quotas stricts)
- Surveiller usage via AI Studio

---

## 📊 Monitoring Quotas

### AI Studio Dashboard
**URL** : https://aistudio.google.com/app/apikey

**Métriques à surveiller** :
- RPM utilisé / RPM max
- RPD utilisé / RPD max
- Erreurs quota (429)

### Logs Application
```python
# Logs à surveiller
"Quota épuisé pour {model}, fallback vers {fallback_model}"
"Tous les modèles épuisés"
```

---

## 🎯 Résumé Configuration

**Équipe 5 agents** : JARVIS_Maître, ARCHITECTE, CODEUR, TESTEUR, VALIDATEUR

**Modèles utilisés** :
- gemini-2.5-pro : 4 agents (orchestration, architecture, code)
- gemini-2.0-flash : 1 agent (tests rapides)
- gemini-3.1-pro-preview : 1 agent (validation précise)

**Quotas totaux** : 2475 RPM, suffisant pour usage mono-utilisateur

**Coût** : 100% gratuit (Tier 1)

**Fallback** : Automatique si quota épuisé

**Validation** : Script test inclus

---

**Configuration validée le 7 mars 2026**  
**Prêt pour production**
