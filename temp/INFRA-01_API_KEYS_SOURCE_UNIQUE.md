# INFRA-01 — Clés API : source unique (.env → SQLite au démarrage)

> Lire PROJET_CONTEXTE.md en entier avant toute action.

---

## Problème exact

Les clés API existent en deux endroits disconnectés :
- `.env` (racine projet) : contient les vraies valeurs (ex : `OPENROUTER_KEY=sk-or-v1-...`)
- `jarvis.db > app_config` : source lue par l'interface Paramètres et par le chat

La page Paramètres lit **uniquement** SQLite. Au premier lancement, SQLite est vide → les champs s'affichent vides même si `.env` a les valeurs. L'utilisateur doit ressaisir manuellement ce qui est déjà dans `.env`.

Le fallback `.env` existe dans `backend/routers/chat.py` (fonction `load_config`) mais **pas** dans `backend/routers/models.py` (fonction `get_config`). Résultat : le chat fonctionne, l'interface Paramètres ne montre rien.

---

## Objectif

Au démarrage de JARVIS, si une clé est absente ou vide dans SQLite ET présente dans `.env` → la copier automatiquement dans SQLite. `.env` devient l'amorçage initial. SQLite devient la source unique à partir de là.

---

## Fichier à modifier : `backend/database.py`

### Ajouter une fonction `_seed_api_keys_from_env(conn)`

Placer cette fonction juste avant `init_db()`.

```python
def _seed_api_keys_from_env(conn):
    """Copie les clés API depuis .env vers SQLite si elles sont absentes en DB."""
    from pathlib import Path as _Path
    import os

    env_to_db = {
        "OPENROUTER_KEY": "openrouter_key",
        "ANTHROPIC_KEY": "anthropic_key",
        "GOOGLE_KEY": "google_key",
        "WEB_SEARCH_KEY": "web_search_key",
    }

    # Lire les valeurs candidates : .env d'abord, puis variables OS
    candidates = {}

    env_file = _Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() in env_to_db and v.strip():
                candidates[k.strip()] = v.strip()

    for env_key in env_to_db:
        if env_key not in candidates and os.environ.get(env_key):
            candidates[env_key] = os.environ[env_key]

    if not candidates:
        return

    cursor = conn.cursor()
    for env_key, db_key in env_to_db.items():
        if env_key not in candidates:
            continue
        # Lire valeur actuelle en DB
        cursor.execute("SELECT value FROM app_config WHERE key = ?", (db_key,))
        row = cursor.fetchone()
        current_value = row["value"] if row else None
        if not current_value:
            cursor.execute(
                "INSERT OR REPLACE INTO app_config (key, value, category) VALUES (?, ?, 'api_keys')",
                (db_key, candidates[env_key])
            )
    conn.commit()
```

### Appeler cette fonction dans `init_db()`

À la fin de `init_db()`, juste avant `conn.close()` :

```python
    _seed_api_keys_from_env(conn)
    conn.close()
```

---

## Fichier à modifier : `backend/routers/models.py` — fonction `get_config()`

Actuellement `get_config()` ne lit que SQLite. Après le seed automatique au démarrage ce n'est plus un problème, mais ajouter quand même le fallback .env pour les cas où la DB n'a pas encore été initialisée lors de l'appel (race condition possible) :

Dans `get_config()`, après le bloc qui construit `api_keys` depuis SQLite, ajouter :

```python
    # Fallback .env si une clé est encore vide après lecture DB
    from pathlib import Path as _Path
    _env_file = _Path(__file__).parent.parent / ".env"
    if _env_file.exists():
        _env_map = {
            "OPENROUTER_KEY": "openrouter_key",
            "ANTHROPIC_KEY": "anthropic_key",
            "GOOGLE_KEY": "google_key",
            "WEB_SEARCH_KEY": "web_search_key",
        }
        for line in _env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            env_k, env_v = line.split("=", 1)
            db_k = _env_map.get(env_k.strip())
            if db_k and env_v.strip() and not api_keys.get(db_k):
                # Masquer comme les autres valeurs
                v = env_v.strip()
                api_keys[db_k] = "..." + v[-4:] if len(v) > 4 else v
```

Placer ce bloc avant le `return` final de `get_config()`.

---

## Ce qu'on ne touche pas

- `.env` reste dans `.gitignore` — pas de modification
- Le comportement de sauvegarde via l'interface (POST `/api/models`) reste identique
- `backend/routers/chat.py` `load_config()` reste tel quel (son fallback .env est redondant après ce fix mais inoffensif)

---

## Test manuel (3 étapes)

1. Ouvrir `backend/data/jarvis.db` avec un outil SQLite, vérifier que `app_config` a les clés API vides → supprimer les lignes existantes pour simuler une DB fraîche
2. Redémarrer JARVIS (`start.bat`)
3. Ouvrir Paramètres (`http://localhost:8000/app/settings.html`) → les champs `openrouter_key` etc. doivent afficher des valeurs masquées (`...xxxx`) correspondant aux clés de `.env`

---

## FIN DE MISSION

- [ ] Build sans erreur
- [ ] Test manuel 3 étapes validé
- [ ] Aucun fichier créé hors périmètre
- [ ] Aucune dépendance ajoutée
