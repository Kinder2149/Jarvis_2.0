# Architecture Multi-Providers JARVIS 2.0

**Date** : 14 mars 2026  
**Statut** : Configuration actuelle 100% Gemini validée, évolution future planifiée

---

## Configuration Actuelle : 100% Gemini (Tier 1)

### Décision Architecturale (8 mars 2026)

**Choix** : Utilisation exclusive de Google Gemini avec clés API multiples par agent

**Raison** :
- ✅ Gratuit (Tier 1)
- ✅ Quotas multipliés avec clés distinctes (75 RPM total)
- ✅ Qualité acceptable pour prototypage et usage modéré
- ✅ Architecture déjà implémentée et testée

### Implémentation Technique

**Fichiers clés** :
- `backend/ia/providers/provider_factory.py` : Gestion clés API multiples
- `backend/ia/providers/gemini_provider.py` : Rate limiting par clé API
- `backend/ia/providers/base_provider.py` : Interface abstraite pour extensibilité

**Système de clés multiples** :
```python
# Ordre de priorité dans provider_factory.py
1. GEMINI_API_KEY_{AGENT_NAME}  # Ex: GEMINI_API_KEY_CODEUR
2. GEMINI_API_KEY                # Fallback global
```

**Avantage** : Chaque clé API a son propre quota RPM indépendant
- Avec 5 clés distinctes : 5 × 15 RPM = 75 RPM total
- Rate limiting géré par dictionnaire `_last_request_times` par clé

### Configuration .env

```env
# Clé globale (fallback)
GEMINI_API_KEY=votre_cle_globale

# Clés spécifiques par agent (recommandé)
GEMINI_API_KEY_JARVIS_MAITRE=cle_agent_1
GEMINI_API_KEY_ARCHITECTE=cle_agent_2
GEMINI_API_KEY_CODEUR=cle_agent_3
GEMINI_API_KEY_TESTEUR=cle_agent_4
GEMINI_API_KEY_VALIDATEUR=cle_agent_5
GEMINI_API_KEY_BASE=cle_agent_6

# Modèles par agent
JARVIS_MAITRE_MODEL=gemini-2.5-pro
ARCHITECTE_MODEL=gemini-2.5-pro
CODEUR_MODEL=gemini-2.5-pro
TESTEUR_MODEL=gemini-2.5-flash
VALIDATEUR_MODEL=gemini-3.1-pro-preview
BASE_MODEL=gemini-2.5-pro
```

---

## Évolution Future : Architecture Hybride

### Option Envisagée : Gemini + OpenRouter

**Objectif** : Maximiser qualité code tout en conservant orchestration gratuite

**Configuration hybride** :
```env
# Orchestrateur : Gemini (gratuit)
JARVIS_MAITRE_PROVIDER=gemini
JARVIS_MAITRE_MODEL=gemini-2.5-pro

# Workers : Claude 3.5 Sonnet via OpenRouter (qualité maximale)
CODEUR_PROVIDER=openrouter
CODEUR_MODEL=anthropic/claude-3.5-sonnet

BASE_PROVIDER=openrouter
BASE_MODEL=anthropic/claude-3.5-sonnet

VALIDATEUR_PROVIDER=openrouter
VALIDATEUR_MODEL=anthropic/claude-3.5-sonnet

# Clés API
GEMINI_API_KEY=votre_cle_gemini
OPENROUTER_API_KEY=votre_cle_openrouter
```

**Avantages** :
- Qualité code maximale (Claude 3.5 Sonnet)
- Pas de limite RPM stricte sur OpenRouter
- JARVIS_Maître gratuit (économie)
- Scalable pour production

**Coût estimé** : $5-10/mois pour 50-100 projets

### Providers Supportés (Planifiés)

**Architecture prête** :
- ✅ `BaseProvider` : Interface abstraite commune
- ✅ `GeminiProvider` : Implémenté et fonctionnel
- 📋 `OpenRouterProvider` : Planifié, non implémenté
- 📋 Support Claude, GPT-4, etc. via OpenRouter

**Extensibilité** :
- Tout nouveau provider doit implémenter `BaseProvider`
- Méthodes requises : `send_message()`, `format_functions()`, `extract_tool_calls()`, `format_tool_result()`
- Format messages standardisé JARVIS

---

## Décisions Techniques

### Pourquoi Gemini Actuellement ?

1. **Coût** : Gratuit (Tier 1) vs payant (OpenRouter)
2. **Quotas** : Suffisants avec clés multiples (75 RPM)
3. **Qualité** : Acceptable pour prototypage
4. **Simplicité** : Un seul provider à gérer

### Quand Migrer vers Hybride ?

**Critères de migration** :
- Usage intensif (>75 projets/mois)
- Besoin qualité code production
- Budget disponible ($5-10/mois)
- Projets critiques nécessitant Claude 3.5 Sonnet

### Architecture Multi-Providers

**Design Pattern** : Factory Pattern
- `ProviderFactory.create(agent_name)` : Crée provider selon config .env
- Variables `{AGENT}_PROVIDER` : Sélection du provider
- Variables `{AGENT}_MODEL` : Sélection du modèle

**Exemple** :
```python
# Dans provider_factory.py
provider_type = os.getenv(f"{agent_name}_PROVIDER", "gemini")
if provider_type == "gemini":
    return GeminiProvider(...)
elif provider_type == "openrouter":
    return OpenRouterProvider(...)  # À implémenter
```

---

## Comparaison Providers

| Provider | Coût | Quotas | Qualité Code | Tool Calling | Contexte |
|----------|------|--------|--------------|--------------|----------|
| **Gemini** | Gratuit | 15 RPM/clé | Bonne | Natif | 1-2M tokens |
| **OpenRouter (Claude)** | $5-10/mois | Illimité | Excellente | Natif | 200K tokens |
| **OpenRouter (GPT-4)** | $10-20/mois | Illimité | Excellente | Natif | 128K tokens |

---

## Documentation Associée

**Références** :
- `docs/reference/RAPPORT_VALIDATION_FINALE.md` : Validation config Gemini
- `docs/reference/CONFIGURATION_OPTIMALE_API.md` : Options de configuration
- `docs/reference/GUIDE_MIGRATION_TIER1_GEMINI.md` : Migration Gemini
- `docs/_meta/INDEX.md` : Historique des modifications (8 mars 2026)

**Code** :
- `backend/ia/providers/provider_factory.py` : Implémentation clés multiples
- `backend/ia/providers/gemini_provider.py` : Rate limiting par clé
- `backend/ia/providers/base_provider.py` : Interface abstraite

---

## Prochaines Étapes (Si Migration Hybride)

### Phase 1 : Implémentation OpenRouterProvider

1. Créer `backend/ia/providers/openrouter_provider.py`
2. Implémenter interface `BaseProvider`
3. Gérer format messages OpenRouter
4. Tester tool calling avec Claude 3.5 Sonnet

### Phase 2 : Configuration Hybride

1. Ajouter variables `.env` pour OpenRouter
2. Modifier `provider_factory.py` pour supporter `openrouter`
3. Tester configuration hybride
4. Documenter coûts réels

### Phase 3 : Validation Production

1. Comparer qualité code Gemini vs Claude
2. Mesurer coûts réels sur 1 mois
3. Évaluer ROI (coût vs gain qualité)
4. Décision finale : rester Gemini ou migrer hybride

---

## Conclusion

**Configuration actuelle** : ✅ 100% Gemini validée et opérationnelle

**Architecture** : ✅ Prête pour extension multi-providers

**Évolution** : 📋 Hybride Gemini + OpenRouter planifiée si besoin qualité maximale

**Décision** : Rester en Gemini tant que qualité suffisante, migrer si besoin production critique
