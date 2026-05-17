# MISSION — Créer l'Agent Organiseur dans Jarvis 2.0

## Contexte absolu — lis tout avant de commencer

Tu travailles sur **JARVIS 2.0**, une application locale (Windows 10, localhost:8000) d'orchestration IA personnelle. Elle tourne avec :

- **Backend** : FastAPI Python, port 8000
- **Base de données** : SQLite, fichier `backend/data/jarvis.db`
- **Frontend** : HTML5 + CSS3 + JavaScript vanilla (zero framework, fetch natif)
- **Appels IA** : OpenRouter via `httpx` async

### Conventions obligatoires — ne pas déroger

1. **Chemins** : toujours `pathlib.Path`, jamais `os.path`
2. **DB** : `from backend.database import get_connection, load_config` — jamais d'import sqlite3 direct dans les services
3. **Connexion** : `conn = get_connection()` → `conn.row_factory = sqlite3.Row` est déjà activé dans get_connection()
4. **Rows** : `dict(row)` pour retourner une row SQLite
5. **Logger** : `logger = logging.getLogger("jarvis")` dans chaque fichier backend
6. **Erreurs** : `raise HTTPException(status_code=404, detail="...")` — toujours
7. **IA** : `from backend.services.model_router import get_model_id` + `await model_router.call_model(...)`
8. **Tables** : créées dans `backend/database.py` dans la fonction `init_db()`, avec `CREATE TABLE IF NOT EXISTS`
9. **Timestamps** : `datetime.now().isoformat()` ou `DEFAULT (datetime('now'))` en SQL
10. **Aucun print()** en production — uniquement `logger.info/warning/error`

### Structure d'un agent existant (référence : Sentinelle)

```
backend/routers/sentinelle.py          ← APIRouter(prefix="/sentinelle")
backend/services/sentinelle_service.py ← logique métier + appels IA
frontend/sentinelle.html               ← page HTML
frontend/assets/js/sentinelle.js       ← logique JS fetch
```

Enregistrement dans `backend/main.py` :
```python
from backend.routers import sentinelle
app.include_router(sentinelle.router, prefix="/api")
```

Bouton sidebar dans `frontend/assets/js/sidebar.js`.

### Signature de call_model (à utiliser telle quelle)

```python
from backend.services import model_router

config = load_config()
model_id = get_model_id("routing", config)   # ou "analysis" pour tâche complexe

resultat = await model_router.call_model(
    model_id=model_id,
    messages=[{"role": "user", "content": prompt}],
    api_keys=config["api_keys"],
    session_id=0,
    step_name="organiseur_classify",   # nom libre, pour les logs
    model_type="routing",
    db_conn=None
)
# resultat est une str (le texte généré)
```

---

## Mission : créer l'Agent Organiseur

### Objectif utilisateur

L'utilisateur perd le fil entre ses agendas, tâches, idées, notes et listes (courses, etc.) dispersés dans plusieurs apps. Il veut un **point de capture unique** où il tape n'importe quoi en langage naturel, et l'IA classe automatiquement. Il veut aussi voir en un coup d'œil **l'état de ses projets code** (lu depuis PROJET_CONTEXTE.md et CHANGELOG.md).

---

## Étape 1 — Tables SQLite dans `backend/database.py`

Ouvre `backend/database.py`. Trouve la fonction `init_db()`. Ajoute ces deux tables **à la fin de init_db()**, avant le `conn.commit()` final (ou juste avant la fermeture de connexion) :

```python
# ── Agent Organiseur ──────────────────────────────────────────────
cursor.execute("""
    CREATE TABLE IF NOT EXISTS organiseur_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_input TEXT NOT NULL,
        title TEXT,
        type TEXT NOT NULL DEFAULT 'inbox' CHECK(type IN ('event','task','idea','note','list_item','inbox')),
        urgency TEXT NOT NULL DEFAULT 'later' CHECK(urgency IN ('today','this_week','later','someday')),
        category TEXT NOT NULL DEFAULT 'perso' CHECK(category IN ('perso','sante','associatif','projet','courses','autre')),
        date_event TEXT,
        status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','done','archived')),
        list_id INTEGER,
        tags TEXT,
        ai_classified INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (list_id) REFERENCES organiseur_lists(id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS organiseur_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'autre',
        status TEXT DEFAULT 'active' CHECK(status IN ('active','done','archived')),
        created_at TEXT DEFAULT (datetime('now'))
    )
""")
```

---

## Étape 2 — Service `backend/services/organiseur_service.py`

Crée ce fichier. Il contient la logique métier et les deux SKILLs IA.

```python
from backend.database import get_connection, load_config
from backend.services.model_router import get_model_id
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger("jarvis")

# Chemin vers la racine du projet (pour lire PROJET_CONTEXTE.md et CHANGELOG.md)
PROJECT_ROOT = Path(__file__).parent.parent.parent


# ─── SKILL 1 : Classification IA ──────────────────────────────────

async def classify_item(item_id: int) -> dict:
    """
    SKILL 1 — Lit le raw_input d'un item et demande à l'IA de le classifier.
    Met à jour l'item en base avec type, urgency, category, title, date_event.
    Retourne l'item mis à jour.
    """
    from backend.services import model_router

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM organiseur_items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        raise ValueError(f"Item {item_id} non trouvé")

    raw_input = item["raw_input"]
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""Tu es un assistant d'organisation personnelle. Analyse ce texte et retourne un JSON structuré.

Texte saisi par l'utilisateur : "{raw_input}"

Date d'aujourd'hui : {today}

Retourne UNIQUEMENT un JSON valide (pas de markdown, pas de texte avant ou après) avec ces champs :
{{
  "title": "Titre court en 5 mots max",
  "type": "event | task | idea | note | list_item",
  "urgency": "today | this_week | later | someday",
  "category": "perso | sante | associatif | projet | courses | autre",
  "date_event": "YYYY-MM-DD ou YYYY-MM-DDTHH:MM ou null"
}}

Règles de classification :
- type=event si c'est un rendez-vous, réunion ou événement fixé dans le temps
- type=task si c'est une action à faire (verbe d'action, à faire, rappel)
- type=idea si c'est une idée, une envie, une réflexion
- type=note si c'est une information à retenir (numéro, adresse, info)
- type=list_item si c'est un ou plusieurs items pour une liste (courses, livres...)
- urgency=today si mentionné aujourd'hui ou urgent
- urgency=this_week si mentionné cette semaine, bientôt, dans les prochains jours
- urgency=later si date future mais pas urgente
- urgency=someday si pas de date, pas d'urgence
- category=courses si nourriture, supermarché, achats du quotidien
- category=sante si médecin, médicament, sport, rendez-vous médical
- category=associatif si asso, réunion asso, bénévole, projet collectif
- category=projet si lié à un projet perso ou professionnel, code, développement
- date_event : extraire la date si mentionnée, sinon null"""

    config = load_config()
    model_id = get_model_id("routing", config)

    try:
        resultat = await model_router.call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config["api_keys"],
            session_id=0,
            step_name="organiseur_classify",
            model_type="routing",
            db_conn=None
        )

        data = json.loads(resultat)
        title = data.get("title", raw_input[:50])
        item_type = data.get("type", "inbox")
        urgency = data.get("urgency", "later")
        category = data.get("category", "autre")
        date_event = data.get("date_event")

        # Valider les valeurs avant d'écrire
        valid_types = {"event", "task", "idea", "note", "list_item", "inbox"}
        valid_urgencies = {"today", "this_week", "later", "someday"}
        valid_categories = {"perso", "sante", "associatif", "projet", "courses", "autre"}

        if item_type not in valid_types:
            item_type = "inbox"
        if urgency not in valid_urgencies:
            urgency = "later"
        if category not in valid_categories:
            category = "autre"

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"[ORGANISEUR] Erreur classification item {item_id}: {e}")
        title = raw_input[:50]
        item_type = "inbox"
        urgency = "later"
        category = "autre"
        date_event = None

    cursor.execute("""
        UPDATE organiseur_items
        SET title = ?, type = ?, urgency = ?, category = ?, date_event = ?,
            ai_classified = 1, updated_at = datetime('now')
        WHERE id = ?
    """, (title, item_type, urgency, category, date_event, item_id))
    conn.commit()

    cursor.execute("SELECT * FROM organiseur_items WHERE id = ?", (item_id,))
    updated = cursor.fetchone()
    conn.close()

    logger.info(f"[ORGANISEUR] Item {item_id} classifié → type={item_type} urgency={urgency} category={category}")
    return dict(updated)


# ─── SKILL 2 : Briefing quotidien ─────────────────────────────────

async def generate_briefing() -> dict:
    """
    SKILL 2 — Génère un briefing quotidien : projets en cours + tâches urgentes + events du jour.
    """
    from backend.services import model_router

    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT title, type, urgency, category, date_event
        FROM organiseur_items
        WHERE status = 'active' AND urgency IN ('today', 'this_week')
        ORDER BY urgency ASC, created_at ASC
        LIMIT 20
    """)
    items_urgents = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Lire PROJET_CONTEXTE.md section 8
    projet_contexte = _read_section_8()

    prompt = f"""Tu es l'assistant organisateur personnel de l'utilisateur. Génère un briefing quotidien concis.

Date d'aujourd'hui : {today}

Tâches et événements urgents :
{json.dumps(items_urgents, ensure_ascii=False, indent=2) if items_urgents else "Aucune tâche urgente"}

Projet en cours (extrait de PROJET_CONTEXTE.md) :
{projet_contexte}

Génère un briefing en français, structuré en 3 parties :
1. **Aujourd'hui** — événements fixes et tâches pour aujourd'hui uniquement
2. **Cette semaine** — ce qui est à faire dans les prochains jours
3. **Projet en cours** — rappel de l'objectif actuel et prochain pas

Ton : direct, bienveillant, sans surplus de mots. Maximum 200 mots."""

    config = load_config()
    model_id = get_model_id("analysis", config)

    resultat = await model_router.call_model(
        model_id=model_id,
        messages=[{"role": "user", "content": prompt}],
        api_keys=config["api_keys"],
        session_id=0,
        step_name="organiseur_briefing",
        model_type="analysis",
        db_conn=None
    )

    return {
        "briefing": resultat,
        "date": today,
        "items_count": len(items_urgents),
        "timestamp": datetime.now().isoformat()
    }


# ─── Dashboard Projets (lecture fichiers) ─────────────────────────

def get_projects_dashboard() -> dict:
    """
    Lit PROJET_CONTEXTE.md et CHANGELOG.md pour construire un dashboard projets.
    """
    dashboard = {
        "session_en_cours": None,
        "prochain_objectif": None,
        "backlog_count": 0,
        "backlog_preview": [],
        "recent_changelog": [],
        "error": None
    }

    # ── PROJET_CONTEXTE.md
    contexte_path = PROJECT_ROOT / "PROJET_CONTEXTE.md"
    if contexte_path.exists():
        try:
            content = contexte_path.read_text(encoding="utf-8")
            dashboard["session_en_cours"] = _extract_section(content, "## 8. SESSION EN COURS")
            dashboard["backlog_preview"] = _extract_backlog_items(content)
            dashboard["backlog_count"] = len(dashboard["backlog_preview"])
            dashboard["prochain_objectif"] = _extract_next_objective(content)
        except Exception as e:
            logger.warning(f"[ORGANISEUR] Erreur lecture PROJET_CONTEXTE.md: {e}")
            dashboard["error"] = str(e)
    else:
        dashboard["error"] = "PROJET_CONTEXTE.md non trouvé"

    # ── CHANGELOG.md
    changelog_path = PROJECT_ROOT / "CHANGELOG.md"
    if changelog_path.exists():
        try:
            lines = changelog_path.read_text(encoding="utf-8").splitlines()
            # Garder les 30 dernières lignes non vides
            recent = [l for l in lines if l.strip()][-30:]
            dashboard["recent_changelog"] = recent
        except Exception as e:
            logger.warning(f"[ORGANISEUR] Erreur lecture CHANGELOG.md: {e}")

    return dashboard


def _read_section_8() -> str:
    """Extrait la section 8 de PROJET_CONTEXTE.md (session en cours)."""
    contexte_path = PROJECT_ROOT / "PROJET_CONTEXTE.md"
    if not contexte_path.exists():
        return "PROJET_CONTEXTE.md non disponible"
    try:
        content = contexte_path.read_text(encoding="utf-8")
        return _extract_section(content, "## 8. SESSION EN COURS") or "Section 8 non trouvée"
    except Exception:
        return "Erreur lecture PROJET_CONTEXTE.md"


def _extract_section(content: str, section_header: str) -> str:
    """Extrait le texte d'une section jusqu'au prochain ## header."""
    lines = content.splitlines()
    in_section = False
    result = []
    for line in lines:
        if line.strip() == section_header.strip():
            in_section = True
            continue
        if in_section:
            if line.startswith("## ") and result:
                break
            result.append(line)
    return "\n".join(result).strip()


def _extract_backlog_items(content: str) -> list:
    """Extrait les items du backlog (section 9) — lignes commençant par | ou - ou *."""
    section = _extract_section(content, "## 9. BACKLOG")
    if not section:
        return []
    items = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("|") and "---|" not in line and line != "|":
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts and parts[0] and parts[0] != "Item":
                items.append(parts[0])
        elif line.startswith(("- ", "* ", "**S")):
            items.append(line.lstrip("-*• ").strip())
    return items[:10]  # max 10 items


def _extract_next_objective(content: str) -> str:
    """Extrait 'Prochain objectif' de la section 8."""
    section = _extract_section(content, "## 8. SESSION EN COURS")
    if not section:
        return None
    for line in section.splitlines():
        if "prochain" in line.lower() or "objectif" in line.lower():
            return line.strip().lstrip("*_").strip()
    return None
```

---

## Étape 3 — Router `backend/routers/organiseur.py`

Crée ce fichier :

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import get_connection
from backend.services import organiseur_service
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/organiseur", tags=["organiseur"])


# ─── Modèles Pydantic ─────────────────────────────────────────────

class ItemCreate(BaseModel):
    raw_input: str
    type: Optional[str] = "inbox"
    urgency: Optional[str] = "later"
    category: Optional[str] = "perso"
    date_event: Optional[str] = None
    list_id: Optional[int] = None
    tags: Optional[str] = None

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    urgency: Optional[str] = None
    category: Optional[str] = None
    date_event: Optional[str] = None
    status: Optional[str] = None
    list_id: Optional[int] = None
    tags: Optional[str] = None

class ListCreate(BaseModel):
    name: str
    category: Optional[str] = "autre"


# ─── Routes Items ──────────────────────────────────────────────────

@router.get("/items")
def list_items(
    status: Optional[str] = "active",
    type: Optional[str] = None,
    urgency: Optional[str] = None,
    category: Optional[str] = None,
    list_id: Optional[int] = None
):
    """Liste les items avec filtres optionnels."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM organiseur_items WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if type:
        query += " AND type = ?"
        params.append(type)
    if urgency:
        query += " AND urgency = ?"
        params.append(urgency)
    if category:
        query += " AND category = ?"
        params.append(category)
    if list_id is not None:
        query += " AND list_id = ?"
        params.append(list_id)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.get("/items/today")
def list_items_today():
    """Items urgents pour aujourd'hui (urgency=today + events date=aujourd'hui)."""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT * FROM organiseur_items
        WHERE status = 'active'
          AND (urgency = 'today' OR (type = 'event' AND date_event LIKE ?))
        ORDER BY date_event ASC, created_at ASC
    """, (f"{today}%",))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/items/week")
def list_items_week():
    """Items pour cette semaine (urgency IN today, this_week)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM organiseur_items
        WHERE status = 'active' AND urgency IN ('today', 'this_week')
        ORDER BY urgency ASC, date_event ASC, created_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/items", status_code=201)
def create_item(data: ItemCreate):
    """Créer un item (capture rapide)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO organiseur_items (raw_input, type, urgency, category, date_event, list_id, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.raw_input,
        data.type or "inbox",
        data.urgency or "later",
        data.category or "perso",
        data.date_event,
        data.list_id,
        data.tags
    ))
    conn.commit()
    item_id = cursor.lastrowid

    cursor.execute("SELECT * FROM organiseur_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)


@router.patch("/items/{item_id}")
def update_item(item_id: int, data: ItemUpdate):
    """Modifier un item (type, urgency, statut, etc.)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM organiseur_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item non trouvé")

    fields = []
    params = []

    for field in ["title", "type", "urgency", "category", "date_event", "status", "list_id", "tags"]:
        val = getattr(data, field)
        if val is not None:
            fields.append(f"{field} = ?")
            params.append(val)

    if not fields:
        conn.close()
        return dict(row)

    fields.append("updated_at = datetime('now')")
    params.append(item_id)

    cursor.execute(
        f"UPDATE organiseur_items SET {', '.join(fields)} WHERE id = ?",
        params
    )
    conn.commit()

    cursor.execute("SELECT * FROM organiseur_items WHERE id = ?", (item_id,))
    updated = cursor.fetchone()
    conn.close()

    return dict(updated)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    """Supprimer un item."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM organiseur_items WHERE id = ?", (item_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Item non trouvé")

    cursor.execute("DELETE FROM organiseur_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return None


# ─── Routes SKILLs IA ─────────────────────────────────────────────

@router.post("/items/{item_id}/classify")
async def classify_item(item_id: int):
    """SKILL 1 — Classifie un item via IA (type, urgency, category, title, date)."""
    try:
        result = await organiseur_service.classify_item(item_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur classification: {str(e)}")


@router.get("/briefing")
async def get_briefing():
    """SKILL 2 — Génère le briefing quotidien IA."""
    try:
        result = await organiseur_service.generate_briefing()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur briefing: {str(e)}")


# ─── Dashboard Projets ─────────────────────────────────────────────

@router.get("/projects/dashboard")
def get_projects_dashboard():
    """Lit PROJET_CONTEXTE.md + CHANGELOG.md et retourne un dashboard structuré."""
    return organiseur_service.get_projects_dashboard()


# ─── Routes Listes ────────────────────────────────────────────────

@router.get("/lists")
def list_lists():
    """Liste toutes les listes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organiseur_lists WHERE status = 'active' ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/lists", status_code=201)
def create_list(data: ListCreate):
    """Créer une liste (ex: Courses, Livres à lire)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO organiseur_lists (name, category)
        VALUES (?, ?)
    """, (data.name, data.category or "autre"))
    conn.commit()
    list_id = cursor.lastrowid

    cursor.execute("SELECT * FROM organiseur_lists WHERE id = ?", (list_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@router.delete("/lists/{list_id}", status_code=204)
def delete_list(list_id: int):
    """Supprimer une liste (et ses items)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM organiseur_lists WHERE id = ?", (list_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Liste non trouvée")

    cursor.execute("DELETE FROM organiseur_items WHERE list_id = ?", (list_id,))
    cursor.execute("DELETE FROM organiseur_lists WHERE id = ?", (list_id,))
    conn.commit()
    conn.close()
    return None
```

---

## Étape 4 — Enregistrement dans `backend/main.py`

Ouvre `backend/main.py`. Ajoute l'import et l'enregistrement du router :

**Ligne import** (ajoute `organiseur` à l'import existant) :
```python
from backend.routers import projects, pipelines, files, chat, atelier, config, reflexions, sentinelle, organiseur
```

**Ligne include_router** (ajoute après `sentinelle`) :
```python
app.include_router(organiseur.router, prefix="/api")
```

---

## Étape 5 — Frontend `frontend/organiseur.html`

Crée ce fichier HTML complet :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Organiseur — JARVIS</title>
  <link rel="stylesheet" href="assets/style.css">
  <style>
    /* ── Layout Organiseur ── */
    .org-layout {
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    .org-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .org-right {
      width: 300px;
      background: var(--bg-secondary, #1a1a2e);
      border-left: 1px solid var(--border, #2a2a3e);
      overflow-y: auto;
      padding: 16px;
      flex-shrink: 0;
    }

    /* ── Capture Zone ── */
    .capture-zone {
      padding: 16px 20px;
      background: var(--bg-secondary, #1a1a2e);
      border-bottom: 1px solid var(--border, #2a2a3e);
      display: flex;
      gap: 10px;
      align-items: flex-end;
    }
    .capture-zone textarea {
      flex: 1;
      min-height: 50px;
      max-height: 120px;
      resize: vertical;
      background: var(--bg-input, #0d0d1a);
      border: 1px solid var(--border, #2a2a3e);
      color: var(--text-primary, #e0e0ff);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 14px;
      font-family: inherit;
    }
    .capture-zone textarea:focus {
      outline: none;
      border-color: var(--accent, #6c63ff);
    }
    .capture-zone textarea::placeholder {
      color: var(--text-muted, #666);
    }
    .btn-capture {
      padding: 10px 20px;
      background: var(--accent, #6c63ff);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 14px;
      cursor: pointer;
      white-space: nowrap;
      height: 50px;
    }
    .btn-capture:hover { opacity: 0.85; }
    .btn-capture:disabled { opacity: 0.5; cursor: default; }

    /* ── Tabs ── */
    .org-tabs {
      display: flex;
      gap: 4px;
      padding: 12px 20px 0;
      border-bottom: 1px solid var(--border, #2a2a3e);
      background: var(--bg-primary, #0d0d1a);
    }
    .org-tab {
      padding: 8px 16px;
      border: none;
      background: none;
      color: var(--text-secondary, #999);
      cursor: pointer;
      border-bottom: 2px solid transparent;
      font-size: 13px;
      font-family: inherit;
    }
    .org-tab.active {
      color: var(--accent, #6c63ff);
      border-bottom-color: var(--accent, #6c63ff);
    }
    .org-tab:hover:not(.active) { color: var(--text-primary, #e0e0ff); }

    /* ── Items List ── */
    .org-content {
      flex: 1;
      overflow-y: auto;
      padding: 16px 20px;
    }
    .items-list { display: flex; flex-direction: column; gap: 8px; }
    .item-card {
      background: var(--bg-secondary, #1a1a2e);
      border: 1px solid var(--border, #2a2a3e);
      border-radius: 8px;
      padding: 12px 14px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      transition: border-color 0.15s;
    }
    .item-card:hover { border-color: var(--accent, #6c63ff); }
    .item-card.done { opacity: 0.5; }
    .item-check {
      width: 18px;
      height: 18px;
      border: 2px solid var(--border, #2a2a3e);
      border-radius: 50%;
      cursor: pointer;
      flex-shrink: 0;
      margin-top: 2px;
      transition: all 0.15s;
    }
    .item-check:hover { border-color: var(--accent, #6c63ff); }
    .item-body { flex: 1; min-width: 0; }
    .item-title {
      font-size: 14px;
      color: var(--text-primary, #e0e0ff);
      font-weight: 500;
      margin-bottom: 4px;
    }
    .item-meta {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      align-items: center;
    }
    .item-raw {
      font-size: 12px;
      color: var(--text-muted, #666);
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 500;
    }
    .badge-type-event     { background: #1a3a5c; color: #5cb8ff; }
    .badge-type-task      { background: #1a3a1a; color: #5cff8a; }
    .badge-type-idea      { background: #3a1a5c; color: #c45cff; }
    .badge-type-note      { background: #3a3a1a; color: #ffdf5c; }
    .badge-type-list_item { background: #3a1a1a; color: #ff8a5c; }
    .badge-type-inbox     { background: #2a2a2a; color: #999; }
    .badge-urgency-today       { background: #5c1a1a; color: #ff5c5c; }
    .badge-urgency-this_week   { background: #5c3a1a; color: #ffaa5c; }
    .badge-urgency-later       { background: #1a2a1a; color: #888; }
    .badge-urgency-someday     { background: #1a1a2a; color: #666; }
    .badge-category {
      background: #1a1a1a;
      color: #888;
      font-size: 10px;
    }
    .badge-date { background: #1a2a3a; color: #5c99ff; font-size: 10px; }
    .btn-classify {
      padding: 3px 10px;
      background: none;
      border: 1px solid var(--border, #2a2a3e);
      color: var(--text-muted, #666);
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
    }
    .btn-classify:hover { border-color: var(--accent, #6c63ff); color: var(--accent, #6c63ff); }
    .btn-delete-item {
      background: none;
      border: none;
      color: var(--text-muted, #666);
      cursor: pointer;
      font-size: 16px;
      padding: 0 4px;
      flex-shrink: 0;
    }
    .btn-delete-item:hover { color: #ff5c5c; }
    .empty-state {
      text-align: center;
      color: var(--text-muted, #666);
      padding: 60px 20px;
      font-size: 14px;
    }

    /* ── Briefing ── */
    .briefing-box {
      background: var(--bg-secondary, #1a1a2e);
      border: 1px solid var(--border, #2a2a3e);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 16px;
    }
    .briefing-box h3 {
      font-size: 13px;
      color: var(--text-muted, #666);
      margin: 0 0 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .briefing-content {
      font-size: 13px;
      color: var(--text-primary, #e0e0ff);
      line-height: 1.6;
      white-space: pre-wrap;
    }
    .btn-briefing {
      width: 100%;
      padding: 10px;
      background: var(--bg-primary, #0d0d1a);
      border: 1px solid var(--border, #2a2a3e);
      color: var(--text-secondary, #999);
      border-radius: 8px;
      font-size: 13px;
      cursor: pointer;
      margin-bottom: 16px;
    }
    .btn-briefing:hover { border-color: var(--accent, #6c63ff); color: var(--accent, #6c63ff); }

    /* ── Panneau droit — Projets ── */
    .right-section-title {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted, #666);
      margin: 0 0 10px;
    }
    .project-dashboard {
      background: var(--bg-primary, #0d0d1a);
      border: 1px solid var(--border, #2a2a3e);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 16px;
    }
    .project-dashboard h4 {
      font-size: 12px;
      color: var(--accent, #6c63ff);
      margin: 0 0 8px;
    }
    .project-session {
      font-size: 12px;
      color: var(--text-secondary, #999);
      line-height: 1.5;
      white-space: pre-wrap;
      max-height: 120px;
      overflow-y: auto;
    }
    .backlog-list {
      list-style: none;
      padding: 0;
      margin: 8px 0 0;
    }
    .backlog-list li {
      font-size: 12px;
      color: var(--text-secondary, #999);
      padding: 3px 0;
      border-bottom: 1px solid var(--border, #2a2a3e);
    }
    .backlog-list li:last-child { border-bottom: none; }

    /* ── Listes (panneau droit) ── */
    .lists-section { margin-top: 16px; }
    .list-item-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
    }
    .list-name-link {
      font-size: 13px;
      color: var(--text-primary, #e0e0ff);
      cursor: pointer;
      flex: 1;
    }
    .list-name-link:hover { color: var(--accent, #6c63ff); }
    .btn-new-list {
      width: 100%;
      padding: 8px;
      background: none;
      border: 1px dashed var(--border, #2a2a3e);
      color: var(--text-muted, #666);
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      margin-top: 8px;
    }
    .btn-new-list:hover { border-color: var(--accent, #6c63ff); color: var(--accent, #6c63ff); }

    /* ── Spinner ── */
    .spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid var(--border, #2a2a3e);
      border-top-color: var(--accent, #6c63ff);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      vertical-align: middle;
      margin-right: 6px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
<div class="org-layout">
  <!-- Sidebar partagée -->
  <div id="sidebar-container"></div>

  <!-- Zone principale -->
  <div class="org-main">
    <!-- Zone de capture -->
    <div class="capture-zone">
      <textarea
        id="capture-input"
        placeholder="Capture libre... RDV dentiste mardi 14h · Acheter du pain · Idée pour l'asso · Appeler Marie cette semaine"
        rows="2"
      ></textarea>
      <button class="btn-capture" id="btn-capture">Capturer</button>
    </div>

    <!-- Tabs de navigation -->
    <div class="org-tabs">
      <button class="org-tab active" data-tab="inbox">Inbox</button>
      <button class="org-tab" data-tab="today">Aujourd'hui</button>
      <button class="org-tab" data-tab="week">Cette semaine</button>
      <button class="org-tab" data-tab="all">Tout</button>
    </div>

    <!-- Contenu des tabs -->
    <div class="org-content">
      <!-- Briefing (affiché seulement dans today) -->
      <div id="briefing-section" style="display:none;">
        <button class="btn-briefing" id="btn-briefing">✨ Générer mon briefing du jour</button>
        <div id="briefing-box" class="briefing-box" style="display:none;">
          <h3>Briefing IA</h3>
          <div class="briefing-content" id="briefing-content"></div>
        </div>
      </div>

      <!-- Liste des items -->
      <div class="items-list" id="items-list">
        <div class="empty-state">Chargement...</div>
      </div>
    </div>
  </div>

  <!-- Panneau droit — Projets + Listes -->
  <div class="org-right">
    <!-- Dashboard projets -->
    <p class="right-section-title">Projet en cours</p>
    <div class="project-dashboard" id="project-dashboard">
      <div style="color:var(--text-muted,#666);font-size:12px;">Chargement...</div>
    </div>

    <!-- Listes -->
    <div class="lists-section">
      <p class="right-section-title">Mes listes</p>
      <div id="lists-container"></div>
      <button class="btn-new-list" id="btn-new-list">+ Nouvelle liste</button>
    </div>
  </div>
</div>

<script src="assets/js/api.js"></script>
<script src="assets/js/shared.js"></script>
<script src="assets/js/sidebar.js"></script>
<script src="assets/js/ui.js"></script>
<script src="assets/js/organiseur.js"></script>
</body>
</html>
```

---

## Étape 6 — JavaScript `frontend/assets/js/organiseur.js`

Crée ce fichier :

```javascript
const BASE = window.location.origin;
let currentTab = 'inbox';
let allLists = [];

// ── Init ───────────────────────────────────────────────────────────

async function init() {
  setupTabs();
  setupCapture();
  setupBriefing();
  setupNewList();
  await Promise.all([loadItems(), loadLists(), loadProjectDashboard()]);
}

// ── Tabs ───────────────────────────────────────────────────────────

function setupTabs() {
  document.querySelectorAll('.org-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.org-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTab = btn.dataset.tab;
      const briefingSection = document.getElementById('briefing-section');
      briefingSection.style.display = (currentTab === 'today') ? 'block' : 'none';
      loadItems();
    });
  });
}

// ── Capture ────────────────────────────────────────────────────────

function setupCapture() {
  const input = document.getElementById('capture-input');
  const btn = document.getElementById('btn-capture');

  btn.addEventListener('click', captureItem);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      captureItem();
    }
  });
}

async function captureItem() {
  const input = document.getElementById('capture-input');
  const btn = document.getElementById('btn-capture');
  const text = input.value.trim();
  if (!text) return;

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  try {
    // 1. Créer l'item
    const res = await fetch(`${BASE}/api/organiseur/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_input: text })
    });
    if (!res.ok) throw new Error('Erreur création');
    const item = await res.json();

    // 2. Classifier via IA en arrière-plan
    classifyItem(item.id);

    input.value = '';
    input.style.height = 'auto';

    // Afficher l'item immédiatement dans inbox
    if (currentTab === 'inbox') {
      await loadItems();
    }
  } catch (err) {
    console.error(err);
    if (typeof showToast === 'function') showToast('Erreur lors de la capture', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Capturer';
    input.focus();
  }
}

async function classifyItem(itemId) {
  try {
    await fetch(`${BASE}/api/organiseur/items/${itemId}/classify`, { method: 'POST' });
    // Rafraîchir silencieusement après classification
    setTimeout(() => loadItems(), 500);
  } catch (err) {
    console.error('Erreur classification:', err);
  }
}

// ── Charger Items ──────────────────────────────────────────────────

async function loadItems() {
  const list = document.getElementById('items-list');

  let url;
  if (currentTab === 'inbox') {
    url = `${BASE}/api/organiseur/items?status=active&type=inbox`;
  } else if (currentTab === 'today') {
    url = `${BASE}/api/organiseur/items/today`;
  } else if (currentTab === 'week') {
    url = `${BASE}/api/organiseur/items/week`;
  } else {
    url = `${BASE}/api/organiseur/items?status=active`;
  }

  try {
    const res = await fetch(url);
    const items = await res.json();
    renderItems(items, list);
  } catch (err) {
    list.innerHTML = '<div class="empty-state">Erreur de chargement</div>';
  }
}

function renderItems(items, container) {
  if (!items.length) {
    const labels = { inbox: 'Inbox vide', today: "Rien pour aujourd'hui ✓", week: 'Semaine libre', all: 'Aucun item' };
    container.innerHTML = `<div class="empty-state">${labels[currentTab] || 'Vide'}</div>`;
    return;
  }

  container.innerHTML = items.map(item => `
    <div class="item-card ${item.status === 'done' ? 'done' : ''}" data-id="${item.id}">
      <div class="item-check" title="Marquer comme fait" onclick="toggleDone(${item.id}, this)"></div>
      <div class="item-body">
        <div class="item-title">${escapeHtml(item.title || item.raw_input)}</div>
        <div class="item-meta">
          ${badgeType(item.type)}
          ${badgeUrgency(item.urgency)}
          ${item.category && item.category !== 'autre' ? `<span class="badge badge-category">${item.category}</span>` : ''}
          ${item.date_event ? `<span class="badge badge-date">📅 ${formatDateShort(item.date_event)}</span>` : ''}
          ${!item.ai_classified ? `<button class="btn-classify" onclick="classifyItem(${item.id})">Classer IA</button>` : ''}
        </div>
        ${item.title && item.raw_input !== item.title ? `<div class="item-raw">${escapeHtml(item.raw_input)}</div>` : ''}
      </div>
      <button class="btn-delete-item" onclick="deleteItem(${item.id})" title="Supprimer">×</button>
    </div>
  `).join('');
}

function badgeType(type) {
  const labels = { event: '📅 Événement', task: '✓ Tâche', idea: '💡 Idée', note: '📝 Note', list_item: '📋 Liste', inbox: '📥 Inbox' };
  return `<span class="badge badge-type-${type}">${labels[type] || type}</span>`;
}

function badgeUrgency(urgency) {
  const labels = { today: '🔴 Aujourd\'hui', this_week: '🟠 Cette semaine', later: '🔵 Plus tard', someday: '⚪ Un jour' };
  return `<span class="badge badge-urgency-${urgency}">${labels[urgency] || urgency}</span>`;
}

function formatDateShort(dateStr) {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: dateStr.includes('T') ? '2-digit' : undefined, minute: dateStr.includes('T') ? '2-digit' : undefined });
  } catch { return dateStr; }
}

// ── Actions Items ──────────────────────────────────────────────────

async function toggleDone(itemId, checkEl) {
  const card = checkEl.closest('.item-card');
  const isDone = card.classList.contains('done');
  const newStatus = isDone ? 'active' : 'done';

  try {
    await fetch(`${BASE}/api/organiseur/items/${itemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    card.classList.toggle('done', !isDone);
    if (!isDone) {
      setTimeout(() => loadItems(), 600);
    }
  } catch (err) {
    console.error(err);
  }
}

async function deleteItem(itemId) {
  if (!confirm('Supprimer cet item ?')) return;
  try {
    await fetch(`${BASE}/api/organiseur/items/${itemId}`, { method: 'DELETE' });
    loadItems();
  } catch (err) {
    console.error(err);
  }
}

// ── Briefing ───────────────────────────────────────────────────────

function setupBriefing() {
  document.getElementById('btn-briefing').addEventListener('click', async () => {
    const btn = document.getElementById('btn-briefing');
    const box = document.getElementById('briefing-box');
    const content = document.getElementById('briefing-content');

    btn.innerHTML = '<span class="spinner"></span> Génération en cours...';
    btn.disabled = true;

    try {
      const res = await fetch(`${BASE}/api/organiseur/briefing`);
      const data = await res.json();
      content.textContent = data.briefing;
      box.style.display = 'block';
    } catch (err) {
      content.textContent = 'Erreur lors de la génération du briefing.';
      box.style.display = 'block';
    } finally {
      btn.innerHTML = '✨ Régénérer le briefing';
      btn.disabled = false;
    }
  });
}

// ── Dashboard Projets ──────────────────────────────────────────────

async function loadProjectDashboard() {
  const container = document.getElementById('project-dashboard');
  try {
    const res = await fetch(`${BASE}/api/organiseur/projects/dashboard`);
    const data = await res.json();

    if (data.error && !data.session_en_cours) {
      container.innerHTML = `<div style="font-size:12px;color:var(--text-muted,#666);">PROJET_CONTEXTE.md non trouvé</div>`;
      return;
    }

    let html = '';

    if (data.prochain_objectif) {
      html += `<h4>Prochain objectif</h4><div class="project-session">${escapeHtml(data.prochain_objectif)}</div>`;
    }

    if (data.backlog_preview && data.backlog_preview.length) {
      html += `<h4 style="margin-top:12px;">Backlog (${data.backlog_count})</h4><ul class="backlog-list">`;
      data.backlog_preview.slice(0, 5).forEach(item => {
        html += `<li>${escapeHtml(item)}</li>`;
      });
      html += '</ul>';
    }

    if (!html) {
      html = '<div style="font-size:12px;color:var(--text-muted,#666);">Aucune session en cours</div>';
    }

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div style="font-size:12px;color:var(--text-muted,#666);">Erreur chargement projet</div>`;
  }
}

// ── Listes ─────────────────────────────────────────────────────────

async function loadLists() {
  try {
    const res = await fetch(`${BASE}/api/organiseur/lists`);
    allLists = await res.json();
    renderLists();
  } catch (err) {
    console.error(err);
  }
}

function renderLists() {
  const container = document.getElementById('lists-container');
  if (!allLists.length) {
    container.innerHTML = '<div style="font-size:12px;color:var(--text-muted,#666);padding:4px 0;">Aucune liste</div>';
    return;
  }
  container.innerHTML = allLists.map(list => `
    <div class="list-item-row">
      <span class="list-name-link" onclick="filterByList(${list.id}, '${escapeHtml(list.name)}')">${escapeHtml(list.name)}</span>
      <button onclick="deleteList(${list.id})" style="background:none;border:none;color:var(--text-muted,#666);cursor:pointer;font-size:14px;" title="Supprimer">×</button>
    </div>
  `).join('');
}

function setupNewList() {
  document.getElementById('btn-new-list').addEventListener('click', async () => {
    const name = prompt('Nom de la liste (ex: Courses, Livres à lire) :');
    if (!name || !name.trim()) return;
    try {
      await fetch(`${BASE}/api/organiseur/lists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() })
      });
      loadLists();
    } catch (err) {
      console.error(err);
    }
  });
}

async function deleteList(listId) {
  if (!confirm('Supprimer cette liste et tous ses items ?')) return;
  try {
    await fetch(`${BASE}/api/organiseur/lists/${listId}`, { method: 'DELETE' });
    loadLists();
    loadItems();
  } catch (err) { console.error(err); }
}

function filterByList(listId, listName) {
  // Basculer vers tab "all" filtré par liste
  document.querySelectorAll('.org-tab').forEach(b => b.classList.remove('active'));
  document.querySelector('[data-tab="all"]').classList.add('active');
  currentTab = 'all';
  document.getElementById('briefing-section').style.display = 'none';

  fetch(`${BASE}/api/organiseur/items?status=active&list_id=${listId}`)
    .then(r => r.json())
    .then(items => renderItems(items, document.getElementById('items-list')))
    .catch(console.error);
}

// ── Utilitaires ────────────────────────────────────────────────────

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Démarrage ──────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', init);
```

---

## Étape 7 — Ajouter le bouton dans la sidebar

Ouvre `frontend/assets/js/sidebar.js`. Trouve la section qui liste les boutons de navigation vers les agents (là où sont les boutons Sentinelle, Atelier, etc.). Ajoute un bouton Organiseur dans la liste.

Cherche le pattern du bouton Sentinelle (quelque chose comme `href="sentinelle.html"` ou `data-page="sentinelle"`). Ajoute juste avant ou après :

```html
<a href="organiseur.html" class="nav-link" id="nav-organiseur">
  📋 Organiseur
</a>
```

Si la sidebar génère ses boutons en JS (par ex. un tableau de liens), ajoute l'entrée `{ href: 'organiseur.html', label: '📋 Organiseur' }` dans ce tableau, à la même position logique.

Adapte exactement au pattern existant dans sidebar.js — ne modifie pas le style, juste ajoute l'entrée.

---

## Étape 8 — Routes API dans `frontend/assets/js/api.js`

Ouvre `frontend/assets/js/api.js`. Ajoute les routes Organiseur à la suite des routes existantes :

```javascript
// ── Organiseur ─────────────────────────────────────────────────────
const organiseurAPI = {
  listItems: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return fetch(`${BASE_URL}/api/organiseur/items${q ? '?' + q : ''}`).then(r => r.json());
  },
  listItemsToday: () => fetch(`${BASE_URL}/api/organiseur/items/today`).then(r => r.json()),
  listItemsWeek: () => fetch(`${BASE_URL}/api/organiseur/items/week`).then(r => r.json()),
  createItem: (data) => fetch(`${BASE_URL}/api/organiseur/items`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  }).then(r => r.json()),
  updateItem: (id, data) => fetch(`${BASE_URL}/api/organiseur/items/${id}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  }).then(r => r.json()),
  deleteItem: (id) => fetch(`${BASE_URL}/api/organiseur/items/${id}`, { method: 'DELETE' }),
  classifyItem: (id) => fetch(`${BASE_URL}/api/organiseur/items/${id}/classify`, { method: 'POST' }).then(r => r.json()),
  getBriefing: () => fetch(`${BASE_URL}/api/organiseur/briefing`).then(r => r.json()),
  getProjectsDashboard: () => fetch(`${BASE_URL}/api/organiseur/projects/dashboard`).then(r => r.json()),
  listLists: () => fetch(`${BASE_URL}/api/organiseur/lists`).then(r => r.json()),
  createList: (data) => fetch(`${BASE_URL}/api/organiseur/lists`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  }).then(r => r.json()),
  deleteList: (id) => fetch(`${BASE_URL}/api/organiseur/lists/${id}`, { method: 'DELETE' }),
};
```

---

## Étape 9 — Vérification finale

Après avoir tout créé, effectue ces vérifications dans l'ordre :

1. **Redémarre le serveur** : `python -m uvicorn backend.main:app --reload --port 8000`
2. **Vérifie l'absence d'erreurs** dans la console uvicorn au démarrage (les tables doivent être créées sans erreur)
3. **Teste l'API** : ouvre `http://localhost:8000/api/docs` → vérifie que les routes `/organiseur/*` apparaissent
4. **Teste la capture** : ouvre `http://localhost:8000/app/organiseur.html` → tape "RDV médecin jeudi 10h" → Capturer → l'item apparaît dans Inbox
5. **Teste la classification IA** : clique sur "Classer IA" → l'item doit recevoir type=event, urgency=this_week, category=sante
6. **Teste le dashboard** : panneau droit → "Projet en cours" doit afficher le contenu de PROJET_CONTEXTE.md section 8
7. **Teste le briefing** : onglet "Aujourd'hui" → "Générer mon briefing" → texte IA généré

---

## Résumé des fichiers créés/modifiés

| Fichier | Action |
|---|---|
| `backend/database.py` | Modifier — ajouter tables `organiseur_items` + `organiseur_lists` dans `init_db()` |
| `backend/services/organiseur_service.py` | Créer |
| `backend/routers/organiseur.py` | Créer |
| `backend/main.py` | Modifier — import + include_router |
| `frontend/organiseur.html` | Créer |
| `frontend/assets/js/organiseur.js` | Créer |
| `frontend/assets/js/sidebar.js` | Modifier — ajouter bouton Organiseur |
| `frontend/assets/js/api.js` | Modifier — ajouter `organiseurAPI` |

---

## Note sur les thèses Sentinelle (hors scope de cette mission)

Le service Sentinelle référence une table `sentinelle_theses` (ligne 421 de sentinelle_service.py) mais **aucune route API ni interface** n'existe pour les gérer. Une thèse d'investissement est une conviction long terme sur un actif ("Je mise sur les ETF énergie propre sur 5 ans"). À traiter dans une mission séparée si besoin.
