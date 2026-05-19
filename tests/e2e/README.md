# Tests E2E JARVIS

Tests End-to-End pour l'interface multi-agents JARVIS avec Playwright.

## Structure

```
tests/e2e/
├── conftest.py           # Fixtures pytest (base_url, API client, création conv)
├── test_jarvis_api.py    # Tests API purs (sans navigateur, sans LLM)
├── test_jarvis_ui.py     # Tests UI Playwright (avec navigateur + LLM réel)
└── README.md             # Ce fichier
```

## Prérequis

### Installation dépendances

```bash
pip install -r requirements.txt
playwright install chromium
```

### Serveur JARVIS actif

Les tests nécessitent que le serveur JARVIS tourne sur `localhost:8000` :

```bash
uvicorn backend.main:app --reload
```

### Clés API (pour tests UI uniquement)

Les tests UI (`test_jarvis_ui.py`) nécessitent des clés API configurées :
- OpenRouter ou Anthropic pour les appels LLM
- Configurer via l'interface `/app/settings.html` ou fichier `.env`

## Exécution des tests

### Tests API uniquement (rapides, sans LLM)

```bash
pytest tests/e2e/test_jarvis_api.py -v
```

**Scénarios couverts :**
- SCÉNARIO 4 : CRUD conversations JARVIS (POST, GET, DELETE)
- SCÉNARIO 5 : Sauvegarde clés API (bug 500 corrigé)
- Health check serveur

**Durée :** ~5-10 secondes

### Tests UI avec Playwright (lents, avec LLM)

```bash
pytest tests/e2e/test_jarvis_ui.py -v -m e2e_ui
```

**Scénarios couverts :**
- SCÉNARIO 1 : Conversation JARVIS basique (vérification 6 agents + réponse)
- SCÉNARIO 2 : Routing ATELIER (détection intention création prospect)
- SCÉNARIO 3 : Abandon flow ATELIER (bug corrigé — signal "non erreur")
- Bonus : Cartes agents cliquables

**Durée :** ~2-3 minutes (appels LLM réels)

**⚠️ Important :** Ces tests nécessitent :
- Serveur actif sur localhost:8000
- Clés API configurées (OpenRouter/Anthropic)
- Timeout adapté aux appels LLM (30s par step)

### Tous les tests E2E

```bash
pytest tests/e2e/ -v
```

## Détails des scénarios

### SCÉNARIO 1 — Conversation JARVIS basique

1. Ouvrir `/app/jarvis.html`
2. Vérifier que les 6 cartes agents sont visibles (JARVIS, MENTOR, FORGE, SENTINELLE, ATELIER, MEDIA)
3. Envoyer "Bonjour"
4. Attendre réponse (max 30s)
5. Vérifier badge agent = "JARVIS"
6. Vérifier contenu réponse non vide

### SCÉNARIO 2 — Routing ATELIER

1. Ouvrir `/app/jarvis.html` (nouvelle conversation)
2. Envoyer "Je veux créer un nouveau prospect"
3. Attendre réponse (max 30s)
4. Vérifier badge agent = "ATELIER"
5. Vérifier réponse contient "nom" ou "restaurant"

### SCÉNARIO 3 — Abandon flow ATELIER

1. Ouvrir `/app/jarvis.html`
2. Envoyer "Je veux créer un nouveau prospect"
3. Attendre réponse ATELIER
4. Envoyer "non erreur je veux faire un audit du projet paperclip"
5. Attendre réponse (max 30s)
6. Vérifier que la réponse NE contient PAS "URL" ni "site web"
7. Vérifier agent = "JARVIS" ou "MENTOR" (pas "ATELIER")

**Ce test valide le bug corrigé dans `atelier_handler.py` :**
- `_is_abort_signal()` détecte "non" au début du message
- Retourne `instance_ref=None` pour libérer l'état
- JARVIS reprend la main au lieu de continuer le flow ATELIER

### SCÉNARIO 4 — CRUD conversations API

Test API REST direct (sans navigateur) :
1. POST `/api/jarvis/conversations` → 201
2. GET `/api/jarvis/conversations` → liste contient la conversation
3. GET `/api/jarvis/conversations/{id}` → 200, messages vide
4. DELETE `/api/jarvis/conversations/{id}` → 204
5. GET `/api/jarvis/conversations/{id}` → 404

### SCÉNARIO 5 — Sauvegarde clés API

Test du bug corrigé dans `config.py` (500 Internal Server Error) :
1. POST `/api/config` avec clé de test
2. Vérifier réponse 200 (pas 500)
3. GET `/api/config` pour vérifier persistance

## Fixtures disponibles

### `base_url`
URL de base du serveur JARVIS (`http://localhost:8000`)

### `api_client`
Client HTTP synchrone (httpx) pour tests API

### `create_jarvis_conversation`
Fixture pour créer une conversation JARVIS et la nettoyer automatiquement :

```python
def test_example(create_jarvis_conversation):
    conv_id = create_jarvis_conversation("Titre test")
    # ... test ...
    # Cleanup automatique après le test
```

### `cleanup_test_config`
Fixture pour restaurer la config après tests paramètres

## Debugging

### Voir le navigateur (mode headed)

Modifier `conftest.py` pour ajouter :

```python
@pytest.fixture(scope="session")
def browser_context_args():
    return {"headless": False}
```

### Logs détaillés

```bash
pytest tests/e2e/ -v -s --log-cli-level=DEBUG
```

### Screenshots en cas d'échec

Playwright capture automatiquement les screenshots en cas d'échec dans :
```
test-results/
```

## Résultats attendus

### Tests API (sans LLM)
✅ **3/3 tests passent** en ~5-10 secondes

### Tests UI (avec LLM)
✅ **4/4 tests passent** en ~2-3 minutes (si clés API configurées)

⚠️ Les tests UI peuvent échouer si :
- Serveur non démarré
- Clés API manquantes ou invalides
- Timeout LLM dépassé (réseau lent)
- Réponse LLM inattendue (variabilité naturelle)

## Maintenance

### Ajouter un nouveau test UI

1. Ajouter la fonction dans `test_jarvis_ui.py`
2. Décorer avec `@pytest.mark.e2e_ui`
3. Utiliser `page.goto()` pour naviguer
4. Utiliser `expect()` pour les assertions Playwright

### Ajouter un nouveau test API

1. Ajouter la fonction dans `test_jarvis_api.py`
2. Utiliser la fixture `api_client`
3. Assertions standard pytest

## Commandes utiles

```bash
# Tests API uniquement (rapides)
pytest tests/e2e/test_jarvis_api.py -v

# Tests UI uniquement (lents)
pytest tests/e2e/test_jarvis_ui.py -v -m e2e_ui

# Tous les tests E2E
pytest tests/e2e/ -v

# Tests avec logs détaillés
pytest tests/e2e/ -v -s

# Tests en parallèle (nécessite pytest-xdist)
pytest tests/e2e/ -v -n auto
```
