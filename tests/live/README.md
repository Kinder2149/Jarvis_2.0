# Tests LIVE — JARVIS

Tests avec **appels API réels** (OpenRouter, Brave Search).

## Prérequis

1. **Serveur JARVIS démarré** :
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```

2. **Clés API valides dans `.env`** :
   - `OPENROUTER_KEY` (obligatoire)
   - `WEB_SEARCH_KEY` (pour test Brave Search)

3. **METHODO accessible** : `C:\DEV\METHODO\`

## Commandes

### Lancer tous les tests live
```bash
python -m pytest tests/live/ -m live -v --timeout=60
```

### Lancer un fichier spécifique
```bash
python -m pytest tests/live/test_live_modules.py -m live -v --timeout=60
```

### Lancer un test spécifique
```bash
python -m pytest tests/live/test_live_modules.py::test_live_chat_reponse_coherente -m live -v
```

## Fichiers

### `test_live_modules.py` (7 tests consolidés)
Tests rapides couvrant les fonctionnalités principales :
1. **Chat** : réponse cohérente OpenRouter
2. **Web Search** : Brave Search retourne résultats
3. **Profil utilisateur** : injection dans system prompt
4. **Pipeline orientation** : classification générée
5. **Global rules** : injection INFRA-04
6. **Atelier** : qualification génère texte
7. **Lecture dossier local** : folder_path fonctionnel

### `test_live_pipeline.py`
Tests approfondis de workflows complets avec fixtures élaborées.

### `test_live_workflows.py`
Tests de workflows spécifiques : session_end, mission_complexe, nouveau_projet, projet_existant.

## Notes

- Les tests live **ne sont PAS exécutés** dans la suite normale (`pytest tests/`)
- Marqueur pytest : `@pytest.mark.live`
- Timeout recommandé : 60s par test
- Les tests nettoient automatiquement les ressources créées
