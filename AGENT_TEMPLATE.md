# Checklist : Ajouter un agent à JARVIS Orchestrateur

Temps estimé : 60 min pour un agent simple, 2h pour un agent avec travail de fond.

---

## Backend (30 min)

- [ ] `backend/services/{nom}_handler.py` — logique métier
  - Copier `backend/services/_agent_template.py` comme point de départ
  - Remplacer `AGENT_NAME = "MON_AGENT"` par le nom en majuscules (ex: `"MEDIA"`)
  - Implémenter `handle()` — signature fixe : `(conversation_id, message, current_instance_ref, db, config) → tuple`
  - Le retour est toujours un 5-tuple : `(content, agent_used, instance_ref, suggest_freeze, freeze_reason)`
  - `suggest_freeze = True` réservé à MENTOR uniquement

- [ ] `backend/routers/{nom}.py` — endpoints REST
  - `router = APIRouter(prefix="/{nom}", tags=["{nom}"])`
  - Ajouter au minimum : `GET /api/{nom}/stats` → `{"total": int, "last_at": str|None}`
  - Conventions : `from backend.database import get_connection, load_config`
  - Erreurs : `raise HTTPException(status_code=404, detail="...")`
  - Pas de `print()` — `logger = logging.getLogger("jarvis")`

- [ ] `backend/main.py` — enregistrer le router
  ```python
  from backend.routers import ..., {nom}
  app.include_router({nom}.router, prefix="/api")
  ```

- [ ] `backend/database.py` — créer les tables si nécessaire
  - Ajouter une fonction `_migrate_vN_{nom}(conn)` avec `CREATE TABLE IF NOT EXISTS`
  - L'appeler dans `init_db()` après les migrations existantes
  - Seeder l'agent dans `agent_registry` via `INSERT OR IGNORE`

---

## Routing JARVIS (15 min)

- [ ] `backend/services/jarvis_service.py` — 4 points à modifier :

  1. **force_agent** (ligne ~65) — ajouter le nom à la liste :
     ```python
     if force_agent and force_agent in ("JARVIS", ..., "NOM_AGENT"):
     ```

  2. **_dispatch** (après le bloc ATELIER) — ajouter :
     ```python
     if agent == "NOM_AGENT":
         from backend.services.{nom}_handler import handle as {nom}_handle
         return await {nom}_handle(conversation_id, message, current_instance_ref, db, config)
     ```

  3. **system prompt** (ligne ~397) — mentionner l'agent dans la description JARVIS

  4. **_get_agent_actif / _find_current_instance_ref** — ajouter les types d'instance_ref :
     ```python
     "{nom}_confirm": "NOM_AGENT",
     "{nom}_running": "NOM_AGENT",
     ```
     et dans `_agent_to_types` :
     ```python
     "NOM_AGENT": ["{nom}_confirm", "{nom}_running"],
     ```

---

## Frontend Orchestrateur (20 min)

- [ ] `frontend/jarvis.html` — ajouter la carte agent dans `#jagents-grid` :
  ```html
  <!-- NOM_AGENT -->
  <div class="jagent-card" id="jcard-NOM_AGENT"
       style="--ac:#COULEUR;--ac-dim:rgba(R,G,B,0.2)"
       onclick="selectAgent('NOM_AGENT')">
    <div class="jagent-card-img">
      <img src="assets/agents/NomAgent1.png" alt="NOM_AGENT">
      <!-- ou placeholder SVG si pas d'image encore -->
    </div>
    <span class="jagent-card-label">Nom affiché</span>
    <span class="jagent-card-role">Rôle fonctionnel</span>
    <div class="jagent-card-stat">
      <span class="jstat-dot idle" id="dot-NOM_AGENT"></span>
      <span id="stat-NOM_AGENT">Chargement…</span>
    </div>
    <!-- optionnel : lien vers page dédiée -->
    <a href="{nom}.html" class="jagent-card-link" onclick="event.stopPropagation()">→ Accès</a>
  </div>
  ```

- [ ] CSS badge (dans le `<style>` de jarvis.html) :
  ```css
  .badge-NOM_AGENT { background: rgba(R,G,B,0.13); color: #COULEUR; }
  ```

- [ ] `loadStats()` — ajouter le bloc stats de l'agent :
  ```javascript
  try {
    const stats = await fetch('/api/{nom}/stats').then(r => r.json());
    setEl('stat-NOM_AGENT', stats.total + ' éléments');
    toggleDot('dot-NOM_AGENT', stats.total > 0);
  } catch (_) { setEl('stat-NOM_AGENT', '—'); }
  ```

- [ ] Image agent : `frontend/assets/agents/NomAgent1.png` — 300×300px recommandé

---

## Clé API (si nécessaire)

- [ ] `backend/services/jarvis_service.py` — ajouter dans le contexte config si la clé est lue via `load_config()`
- [ ] `backend/database.py` — vérifier que la clé est migrée dans `app_config`
- [ ] `frontend/assets/js/settings.js` — ajouter `'{nom}'` dans les 3 listes `providers`
- [ ] `frontend/settings.html` — ajouter le bloc `key-display-{nom}` dans l'onglet Clés API

---

## Validation

- [ ] Redémarrer le serveur (`uvicorn backend.main:app --reload`)
- [ ] La carte agent apparaît dans le board Orchestrateur
- [ ] Cliquer la carte → badge dans le chat change vers `NOM_AGENT`
- [ ] Envoyer un message → l'agent répond avec `[NOM_AGENT]` en préfixe
- [ ] `GET /api/{nom}/stats` retourne `{"total": 0, "last_at": null}` minimum
- [ ] La page Paramètres affiche le champ de la clé API si applicable

---

## Conventions rappel

| Règle | Détail |
|---|---|
| Chemins | `pathlib.Path`, jamais `os.path` |
| DB | `from backend.database import get_connection, load_config` |
| Logger | `logger = logging.getLogger("jarvis")` |
| Erreurs HTTP | `raise HTTPException(status_code=404, detail="...")` |
| IA | `from backend.services.model_router import get_model_id, call_model` |
| Tables | `CREATE TABLE IF NOT EXISTS` dans `init_db()` via migration |
| Logs | `logger.info/warning/error` — jamais `print()` |
| JS | Vanilla uniquement, `fetch` natif — zéro framework |
| Badge | `agent_used = "NOM_AGENT"` pour TOUS les messages de l'agent |
