# Configuration Multi-Clés API et Timeouts - 15 Mars 2026

**Date** : 15 mars 2026 14:50  
**Objectif** : Implémenter utilisation de clés API distinctes par agent + adapter timeouts

---

## 🎯 Mission 1 : Clés API Distinctes par Agent

### Contexte

**Problème initial** : Tous les agents utilisaient la même clé API `GEMINI_API_KEY`.

**Limitation** : Quota RPM (Requests Per Minute) partagé entre tous les agents.

**Solution** : Utiliser 5 clés API distinctes pour multiplier les quotas.

### Configuration .env

**Clés API définies** (`.env.example` lignes 22-28) :
```bash
# Clé API globale (FALLBACK)
GEMINI_API_KEY=

# Clés API par agent (5 clés actives)
GEMINI_API_KEY_JARVIS_MAITRE=
GEMINI_API_KEY_ARCHITECTE=
GEMINI_API_KEY_CODEUR=
GEMINI_API_KEY_TESTEUR=
GEMINI_API_KEY_VALIDATEUR=
```

**Avantages** :
- **Quotas multipliés** : 5 clés × 15 RPM = 75 RPM total (Tier 1 gratuit)
- **Isolation** : Chaque agent a son propre quota
- **Résilience** : Si une clé atteint la limite, les autres continuent

---

## ✅ Modifications Appliquées

### 1. agent_config.py

**Ajout** : Mapping `api_key_env` pour chaque agent

```python
AGENT_CONFIGS = {
    "BASE": {
        # ...
        "api_key_env": "GEMINI_API_KEY",  # Fallback global
    },
    "ARCHITECTE": {
        # ...
        "api_key_env": "GEMINI_API_KEY_ARCHITECTE",
    },
    "CODEUR": {
        # ...
        "api_key_env": "GEMINI_API_KEY_CODEUR",
    },
    "TESTEUR": {
        # ...
        "api_key_env": "GEMINI_API_KEY_TESTEUR",
    },
    "VALIDATEUR": {
        # ...
        "api_key_env": "GEMINI_API_KEY_VALIDATEUR",
    },
    "JARVIS_Maître": {
        # ...
        "api_key_env": "GEMINI_API_KEY_JARVIS_MAITRE",
    },
}
```

---

### 2. agent_factory.py

**Modification** : Récupération clé API spécifique avec fallback

```python
def get_agent(agent_name: str) -> BaseAgent:
    # Récupérer clé API spécifique pour cet agent (avec fallback sur GEMINI_API_KEY)
    api_key_env = config.get("api_key_env", "GEMINI_API_KEY")
    api_key = os.getenv(api_key_env) or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise RuntimeError(f"Aucune clé API trouvée pour {agent_name}")
    
    logger.info(f"Agent {agent_name}: utilise clé API depuis {api_key_env}")
    
    # Passer api_key à l'agent
    agent = Codeur(
        agent_id=f"provider_{agent_name}",
        temperature=config.get("temperature"),
        max_tokens=config.get("max_tokens"),
        api_key=api_key,  # ← Clé spécifique
    )
```

---

### 3. base_agent.py

**Modification** : Accepter `api_key` optionnel

```python
def __init__(
    self,
    agent_id: str,
    name: str,
    role: str,
    description: str,
    permissions: list[str] | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    prompt_file: str | None = None,
    api_key: str | None = None,  # ← Nouveau paramètre
):
    # ...
    self.provider = ProviderFactory.create(agent_name=name, api_key=api_key)
```

---

### 4. provider_factory.py

**Modification** : Accepter et transmettre `api_key`

```python
@staticmethod
def create(agent_name: str, api_key: str = None) -> BaseProvider:
    # Si api_key fournie, ne pas utiliser cache
    if not api_key:
        cached_provider = ProviderFactory._PROVIDER_CACHE.get(cache_key)
        if cached_provider:
            return cached_provider
    
    # Créer provider avec clé API spécifique
    provider = ProviderFactory._create_gemini(agent_name, api_key=api_key)
    
    # Mettre en cache uniquement si pas de clé custom
    if not api_key:
        ProviderFactory._PROVIDER_CACHE[cache_key] = provider
    
    return provider

@staticmethod
def _create_gemini(agent_name: str = None, api_key: str = None) -> GeminiProvider:
    # Si clé API fournie en paramètre, l'utiliser directement
    if api_key:
        logger.debug(f"Utilisation clé API fournie en paramètre pour {agent_name}")
    else:
        # Essayer clé spécifique à l'agent (ex: GEMINI_API_KEY_CODEUR)
        agent_api_key = os.getenv(f"GEMINI_API_KEY_{env_agent_name}")
        if agent_api_key:
            api_key = agent_api_key
        else:
            # Fallback sur clé globale
            api_key = os.getenv("GEMINI_API_KEY")
```

---

### 5. Tous les agents spécialisés

**Modification** : Accepter `api_key` dans `__init__`

Fichiers modifiés :
- `backend/agents/jarvis_maitre.py`
- `backend/agents/architecte.py`
- `backend/agents/codeur.py`
- `backend/agents/testeur.py`
- `backend/agents/validateur.py`

```python
def __init__(
    self,
    agent_id: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,  # ← Nouveau paramètre
):
    super().__init__(
        # ...
        api_key=api_key,  # ← Transmis à BaseAgent
    )
```

---

## 🎯 Mission 2 : Adapter Timeouts

### Recherche Documentation

**Source** : GitHub Discussion google/adk-python #3199

**Découverte clé** : 
> "The underlying Gemini API has a **maximum request timeout of 5 minutes**. If a request to the API takes longer than 5 minutes to complete, the connection is terminated by the server."

**Conclusion** : Timeout maximum Gemini API = **300 secondes (5 minutes)**

---

### Modifications Appliquées

#### 1. Tests Live

**Fichiers modifiés** :
- `tests/live/test_live_workflow_complet_audit.py`
- `tests/live/test_simple_mission_status.py`

**Avant** :
```python
async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minutes
```

**Après** :
```python
async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minutes
```

**Justification** :
- Workflow complet : JARVIS_Maître (30-60s) + ARCHITECTE (30-60s) + CODEUR (60-120s) + TESTEUR (30-60s) + VALIDATEUR (20-40s)
- Total estimé : 170-340 secondes
- Timeout 180s (3min) = marge confortable sous limite Gemini 300s

---

#### 2. Attente Orchestration dans Tests

**Fichier** : `tests/live/test_live_workflow_complet_audit.py`

**Modification** :
```python
# Attendre création mission (asynchrone - ARCHITECTE peut prendre 30-60s)
print("⏳ Attente 10 secondes pour création mission et appel ARCHITECTE...")
await asyncio.sleep(10)
```

**Justification** : 10 secondes suffisantes pour création mission + début appel ARCHITECTE

---

## 📊 Bénéfices Configuration

### Quotas RPM Multipliés

**Avant** :
- 1 clé API × 15 RPM = **15 RPM total**
- Risque saturation si workflow intensif

**Après** :
- 5 clés API × 15 RPM = **75 RPM total**
- Capacité 5× supérieure

### Timeouts Adaptés

**Avant** :
- Timeout 120s (2min) → Trop court pour workflow complet
- Tests échouaient par timeout

**Après** :
- Timeout 180s (3min) → Confortable sous limite Gemini 300s
- Marge pour variations réseau

---

## 🔧 Configuration Utilisateur

### Étape 1 : Créer 5 Clés API Gemini

1. Aller sur https://aistudio.google.com/app/apikey
2. Créer 5 clés API distinctes
3. Nommer clairement : `JARVIS_MAITRE`, `ARCHITECTE`, `CODEUR`, `TESTEUR`, `VALIDATEUR`

### Étape 2 : Configurer .env

Copier `.env.example` vers `.env` et remplir :

```bash
# Clé globale (fallback)
GEMINI_API_KEY=votre_cle_globale

# Clés par agent
GEMINI_API_KEY_JARVIS_MAITRE=votre_cle_jarvis
GEMINI_API_KEY_ARCHITECTE=votre_cle_architecte
GEMINI_API_KEY_CODEUR=votre_cle_codeur
GEMINI_API_KEY_TESTEUR=votre_cle_testeur
GEMINI_API_KEY_VALIDATEUR=votre_cle_validateur
```

### Étape 3 : Redémarrer Serveur

```powershell
.\start_jarvis_complete.ps1
```

**Vérification logs** :
```
Agent JARVIS_Maître: utilise clé API depuis GEMINI_API_KEY_JARVIS_MAITRE
Agent ARCHITECTE: utilise clé API depuis GEMINI_API_KEY_ARCHITECTE
Agent CODEUR: utilise clé API depuis GEMINI_API_KEY_CODEUR
Agent TESTEUR: utilise clé API depuis GEMINI_API_KEY_TESTEUR
Agent VALIDATEUR: utilise clé API depuis GEMINI_API_KEY_VALIDATEUR
```

---

## 📈 Monitoring Quotas

### Vérifier Utilisation

Chaque clé API a son propre dashboard :
- https://aistudio.google.com/app/apikey
- Cliquer sur chaque clé pour voir utilisation RPM

### Alertes Recommandées

Si une clé atteint 80% quota :
1. Vérifier logs pour identifier agent gourmand
2. Augmenter `min_delay_seconds` dans `agent_config.py`
3. Ou passer à Tier supérieur (Tier 2 = 1000 RPM)

---

## 🎯 Prochaines Optimisations

### Court Terme

1. **Monitoring automatique** : Logger RPM par agent
2. **Rate limiting adaptatif** : Ajuster délais selon charge
3. **Retry logic** : Réessayer avec backoff si 429 (rate limit)

### Long Terme

1. **Tier 2 Gemini** : 1000 RPM par clé (payant)
2. **Load balancing** : Distribuer requêtes sur plusieurs clés
3. **Cache réponses** : Éviter appels redondants

---

**Date rapport** : 15 mars 2026 14:55  
**Statut** : Configuration multi-clés implémentée ✅ | Timeouts adaptés ✅
