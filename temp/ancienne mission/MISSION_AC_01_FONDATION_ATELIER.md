# MISSION AC_01 — Fondation données + ressources Atelier Connecté

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. backend/database.py (schéma actuel des tables)
3. backend/main.py (enregistrement des routers existants)
4. backend/services/pipeline_engine.py (execute_step — comprendre la logique)
5. backend/routers/pipelines.py (structure d'un router existant — modèle à suivre)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : AC_01 — Fondation données + ressources Atelier Connecté

OBJECTIF :
Poser les fondations backend du module Atelier Connecté.
Nouvelle table prospects, répertoire de ressources statiques, service atelier, router CRUD.
Aucun frontend dans cette mission. Aucune modification des workflows existants.

PÉRIMÈTRE :
Fichiers à modifier :
- backend/database.py         (ajout table prospects)
- backend/main.py             (enregistrement router atelier)
- backend/services/pipeline_engine.py  (gestion model_type "none")

Fichiers à créer :
- backend/routers/atelier.py
- backend/services/atelier_service.py

Dossiers à créer :
- backend/data/atelier/resources/
- backend/data/atelier/resources/tools/
- backend/data/atelier/demos/

Fichiers ressources à copier (contenu identique, nom normalisé) :
- temp/1.Ressource CLients/CADRAGE_STRATEGIQUE.md
  → backend/data/atelier/resources/CADRAGE_STRATEGIQUE.md
- temp/1.Ressource CLients/CATEGORIES_CLIENT.md  (section Restauration uniquement)
  → backend/data/atelier/resources/CATEGORIES_CLIENT_RESTAURATION.md
- temp/1.Ressource CLients/STACK_STANDARD.md
  → backend/data/atelier/resources/STACK_STANDARD.md
- temp/1.Ressource CLients/EMAILS_TEMPLATES.md
  → backend/data/atelier/resources/EMAILS_TEMPLATES.md
- temp/1.Ressource CLients/BASE/TOOL_RESERVATIONS_SPEC.md
  → backend/data/atelier/resources/tools/TOOL_RESERVATIONS_SPEC.md
- temp/1.Ressource CLients/BASE/TOOL_MENU_ARDOISE_SPEC.md
  → backend/data/atelier/resources/tools/TOOL_MENU_ARDOISE_SPEC.md
- temp/1.Ressource CLients/BASE/TOOL_EVENEMENTS_SPEC.md
  → backend/data/atelier/resources/tools/TOOL_EVENEMENTS_SPEC.md
- temp/1.Ressource CLients/BASE/TOOL_AVIS_SPEC.md
  → backend/data/atelier/resources/tools/TOOL_AVIS_SPEC.md
- temp/1.Ressource CLients/BASE/TOOL_EMPORTER_SPEC.md
  → backend/data/atelier/resources/tools/TOOL_EMPORTER_SPEC.md

Prérequis : JARVIS doit démarrer sans erreur avant de commencer.

---

INSTRUCTIONS DÉTAILLÉES :

### ÉTAPE 1 — backend/database.py : ajouter la table prospects

Dans la fonction init_db(), après le bloc de création de la table app_config,
ajouter ce bloc EXACTEMENT :

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
            nom         TEXT NOT NULL,
            categorie   TEXT NOT NULL DEFAULT 'restauration',
            url         TEXT,
            statut      TEXT NOT NULL DEFAULT 'identifié',
            score       TEXT,
            form_data   TEXT,
            fiche       TEXT,
            proposition TEXT,
            demo_path   TEXT,
            demo_url    TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)

Statuts valides du cycle de vie (ajouter en commentaire au-dessus) :
# identifié → en_analyse → proposition_ok → démo_générée → contacté → relancé → signé / perdu


### ÉTAPE 2 — Créer les dossiers et copier les ressources

Créer les dossiers :
  backend/data/atelier/resources/
  backend/data/atelier/resources/tools/
  backend/data/atelier/demos/

Copier les fichiers listés dans PÉRIMÈTRE ci-dessus.
Pour CATEGORIES_CLIENT_RESTAURATION.md : copier uniquement la section "## RESTAURATION ✅ Développée"
et tout son contenu jusqu'à la prochaine section "## COMMERCE".


### ÉTAPE 3 — Créer backend/services/atelier_service.py

Créer ce fichier avec exactement ces fonctions :

```python
from pathlib import Path
import json
import zipfile
import io
import re
import httpx

RESOURCES_PATH = Path(__file__).parent.parent / "data" / "atelier" / "resources"
DEMOS_PATH = Path(__file__).parent.parent / "data" / "atelier" / "demos"


def load_resource(filename: str) -> str:
    """Charge un fichier de ressource. Ex: load_resource('CADRAGE_STRATEGIQUE.md')"""
    path = RESOURCES_PATH / filename
    if not path.exists():
        return f"[RESSOURCE MANQUANTE: {filename}]"
    return path.read_text(encoding="utf-8")


def load_tool_spec(tool_name: str) -> str:
    """Charge la spec d'un outil. Ex: load_tool_spec('reservations')"""
    filename = f"TOOL_{tool_name.upper()}_SPEC.md"
    path = RESOURCES_PATH / "tools" / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def get_activated_tools(saisie_data: dict) -> list:
    """Retourne la liste des outils activés depuis les données du formulaire SAISIE."""
    outils = saisie_data.get("outils", {})
    activated = ["reservations", "menu_ardoise"]  # toujours obligatoires
    for tool in ["evenements", "avis", "emporter"]:
        if outils.get(tool, False):
            activated.append(tool)
    return activated


async def fetch_url(url: str) -> dict:
    """Fetch HTTP d'une URL prospect, retourne le texte nettoyé."""
    if not url or url.strip() in ("aucun site", "", "null"):
        return {"text": "", "title": "", "images": []}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
        # Nettoyage simple sans dépendance BS4 : supprimer les balises HTML
        text = re.sub(r'<script[^>]*>.*?</script>', '', response.text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text[:15000]  # limiter le contexte injecté au LLM

        # Extraire le titre
        title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        # Extraire les URLs d'images
        images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', response.text)[:10]

        return {
            "text": text,
            "title": title,
            "images": images,
            "raw_html": response.text[:30000]
        }
    except Exception as e:
        return {"text": f"[Erreur fetch URL: {str(e)}]", "title": "", "images": []}


def save_demo_files(prospect_slug: str, raw_outputs: dict) -> Path:
    """
    Parse les outputs LLM des steps génération et écrit les 5 fichiers démo.
    raw_outputs = {
        "generation_css": "...",
        "generation_index": "...",
        "generation_admin": "..."
    }
    Format attendu pour generation_index et generation_admin :
    <<<FILE: index.html>>>
    [contenu]
    <<<FILE: script.js>>>
    [contenu]
    """
    demo_dir = DEMOS_PATH / prospect_slug
    demo_dir.mkdir(parents=True, exist_ok=True)

    # styles.css — extraire entre ```css et ```
    css_raw = raw_outputs.get("generation_css", "")
    css_content = _extract_code_block(css_raw, "css")
    (demo_dir / "styles.css").write_text(css_content, encoding="utf-8")

    # index.html + script.js
    index_files = _parse_file_delimiters(raw_outputs.get("generation_index", ""))
    for filename, content in index_files.items():
        (demo_dir / filename).write_text(content, encoding="utf-8")

    # admin.html + admin.js
    admin_files = _parse_file_delimiters(raw_outputs.get("generation_admin", ""))
    for filename, content in admin_files.items():
        (demo_dir / filename).write_text(content, encoding="utf-8")

    return demo_dir


def export_as_zip(prospect_slug: str) -> bytes:
    """Compresse le dossier demo/{slug}/ en ZIP et retourne les bytes."""
    demo_dir = DEMOS_PATH / prospect_slug
    if not demo_dir.exists():
        raise FileNotFoundError(f"Dossier démo introuvable : {demo_dir}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in demo_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(demo_dir))
    return buf.getvalue()


def _extract_code_block(text: str, lang: str) -> str:
    pattern = rf"```{lang}\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def _parse_file_delimiters(text: str) -> dict:
    """Parse les blocs <<<FILE: nom.ext>>> ... du texte LLM."""
    files = {}
    parts = re.split(r'<<<FILE:\s*(.+?)>>>', text)
    for i in range(1, len(parts), 2):
        filename = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        files[filename] = content
    return files
```


### ÉTAPE 4 — Créer backend/routers/atelier.py

Créer ce router en suivant le même pattern que les routers existants (imports, get_connection, etc.) :

Endpoints à implémenter :

GET /prospects
  SELECT * FROM prospects ORDER BY updated_at DESC
  Retourne liste JSON de tous les prospects.

POST /prospects
  Body JSON : {nom: str, categorie: str = "restauration", url: str = null}
  INSERT INTO prospects (nom, categorie, url)
  Retourne le prospect créé avec son id.

GET /prospects/{id}
  SELECT prospect + si session_id non null : session avec ses steps
  404 si prospect introuvable.
  Retourne {prospect, session} — session peut être null.

PATCH /prospects/{id}
  Body JSON (tous les champs sont optionnels) :
  {statut, demo_url, notes, score, proposition, fiche, form_data}
  UPDATE prospects SET [champs fournis], updated_at=datetime('now') WHERE id=?
  404 si non trouvé. Retourne le prospect mis à jour.

DELETE /prospects/{id}
  DELETE FROM prospects WHERE id=?
  Si session_id existait : ne pas supprimer la session (garder l'historique).
  Retourne 204.

POST /prospects/{id}/start
  1. Vérifier que le prospect existe et n'a pas déjà de session active
  2. Récupérer ou créer le projet système Atelier :
     SELECT id FROM projects WHERE path='__atelier__'
     Si absent : INSERT INTO projects (name, path, type) VALUES ('Atelier Connecté', '__atelier__', 'atelier')
  3. Appeler pipeline_engine.create_session(project_id, 'atelier_restauration', form_data_json, db)
     où form_data_json = prospect.form_data ou "{}"
  4. UPDATE prospects SET session_id=?, statut='en_analyse', updated_at=datetime('now') WHERE id=?
  Retourne {session_id, prospect_id}.

GET /prospects/{id}/files
  Lire backend/data/atelier/demos/{slug}/ si demo_path est défini
  Retourne [{name, size_kb}] ou [] si démo pas encore générée.
  Le slug est extrait de demo_path.

GET /prospects/{id}/export
  Appeler atelier_service.export_as_zip(slug)
  Retourne FileResponse avec Content-Type: application/zip
  Nom du fichier téléchargé : demo-{slug}.zip
  404 si demo_path non défini.


### ÉTAPE 5 — backend/main.py : enregistrer le router

Ajouter après les autres imports de routers :
  from backend.routers import atelier

Ajouter après les autres include_router :
  app.include_router(atelier.router, prefix="/api/atelier", tags=["atelier"])


### ÉTAPE 6 — backend/services/pipeline_engine.py : gérer model_type "none"

Dans la fonction execute_step(), avant l'appel au model_router (avant la ligne qui
appelle call_model ou get_model_id), ajouter ce bloc :

    # Étapes sans appel LLM (model_type = "none")
    if step.get("model_type") == "none":
        if step.get("requires_validation"):
            # Récupérer l'output du step précédent comme contenu à afficher
            prev_output = ""
            if step["step_index"] > 0:
                prev_row = cursor.execute(
                    """SELECT output_data FROM pipeline_steps
                       WHERE session_id=? AND step_index=? AND status='COMPLETED'""",
                    (session_id, step["step_index"] - 1)
                ).fetchone()
                if prev_row and prev_row["output_data"]:
                    prev_output = prev_row["output_data"]
            cursor.execute(
                "UPDATE pipeline_steps SET status='WAITING_VALIDATION', output_data=? WHERE id=?",
                (prev_output, step["id"])
            )
            cursor.execute(
                "UPDATE sessions SET status='WAITING_VALIDATION', updated_at=datetime('now') WHERE id=?",
                (session_id,)
            )
            db.commit()
            return {"status": "waiting_validation", "step_id": step["id"]}
        else:
            # Step export : assembler et écrire les fichiers démo
            if step.get("step_name") == "export":
                _handle_atelier_export(session_id, step["id"], db)
            else:
                cursor.execute(
                    "UPDATE pipeline_steps SET status='COMPLETED' WHERE id=?",
                    (step["id"],)
                )
                db.commit()
            return {"status": "auto_completed"}

Ajouter ensuite la fonction helper (en dehors de execute_step) :

def _handle_atelier_export(session_id: int, step_id: int, db):
    """Écrit les 5 fichiers démo depuis les outputs des steps génération."""
    from backend.services.atelier_service import save_demo_files
    cursor = db.cursor()

    # Récupérer les outputs des 3 steps génération
    raw_outputs = {}
    for step_name in ["generation_css", "generation_index", "generation_admin"]:
        row = cursor.execute(
            """SELECT output_data FROM pipeline_steps
               WHERE session_id=? AND step_name=? AND status='COMPLETED'""",
            (session_id, step_name)
        ).fetchone()
        if row and row["output_data"]:
            raw_outputs[step_name] = row["output_data"]

    # Récupérer le slug depuis l'output du step analyse_site
    slug_row = cursor.execute(
        """SELECT output_data FROM pipeline_steps
           WHERE session_id=? AND step_name='analyse_site' AND status='COMPLETED'""",
        (session_id,)
    ).fetchone()
    slug = "demo-inconnue"
    if slug_row and slug_row["output_data"]:
        try:
            analyse = json.loads(slug_row["output_data"])
            slug = analyse.get("slug", "demo-inconnue")
        except Exception:
            pass

    demo_path = save_demo_files(slug, raw_outputs)

    # Mettre à jour demo_path dans la table prospects
    cursor.execute(
        "UPDATE prospects SET demo_path=?, updated_at=datetime('now') WHERE session_id=?",
        (str(demo_path), session_id)
    )
    cursor.execute(
        "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE id=?",
        (f"Démo générée dans {demo_path}", step_id)
    )
    db.commit()

Ajouter import json en tête de pipeline_engine.py si non présent.

---

TESTS À EFFECTUER (dans l'ordre, s'arrêter au premier échec) :

Test 1 — Démarrage propre
Redémarrer JARVIS. Aucune erreur au démarrage.
Vérifier dans jarvis.log qu'aucune exception n'apparaît.

Test 2 — Table créée
GET http://localhost:8000/api/atelier/prospects → réponse 200 avec []

Test 3 — Création prospect
POST http://localhost:8000/api/atelier/prospects
Body: {"nom": "Test Restaurant", "categorie": "restauration", "url": "https://example.com"}
→ réponse 201 avec id, nom, statut="identifié"

Test 4 — Lecture prospect
GET http://localhost:8000/api/atelier/prospects/{id du test 3}
→ réponse 200 avec le prospect

Test 5 — Mise à jour statut
PATCH http://localhost:8000/api/atelier/prospects/{id}
Body: {"statut": "contacté"}
→ réponse 200 avec statut="contacté"

Test 6 — Lancement pipeline
POST http://localhost:8000/api/atelier/prospects/{id}/start
→ réponse 200 avec session_id
→ GET http://localhost:8000/api/pipelines/{session_id}
  → session avec 9 steps, step 0 en statut WAITING_VALIDATION

Test 7 — Workflows existants non impactés
Créer un projet JARVIS normal, lancer un workflow bug_simple existant
→ fonctionne normalement, aucune régression

Test 8 — Suppression prospect
DELETE http://localhost:8000/api/atelier/prospects/{id}
→ réponse 204

---

RAPPORT DE FIN DE MISSION :

Créer le fichier temp/RAPPORT_AC_01.md avec :

# RAPPORT AC_01 — Fondation données + ressources

## Statut global : ✅ Terminé / ❌ Bloqué

## Fichiers créés
- [ ] backend/data/atelier/resources/ (+ 4 fichiers .md)
- [ ] backend/data/atelier/resources/tools/ (+ 5 fichiers TOOL_*_SPEC.md)
- [ ] backend/data/atelier/demos/
- [ ] backend/services/atelier_service.py
- [ ] backend/routers/atelier.py

## Fichiers modifiés
- [ ] backend/database.py (table prospects)
- [ ] backend/main.py (router atelier)
- [ ] backend/services/pipeline_engine.py (model_type none + _handle_atelier_export)

## Résultats des tests
- [ ] Test 1 — Démarrage propre
- [ ] Test 2 — GET /prospects → []
- [ ] Test 3 — POST /prospects → prospect créé
- [ ] Test 4 — GET /prospects/{id} → prospect trouvé
- [ ] Test 5 — PATCH statut → mis à jour
- [ ] Test 6 — POST /start → session créée avec 9 steps
- [ ] Test 7 — Workflows existants non impactés
- [ ] Test 8 — DELETE → 204

## Problèmes rencontrés
[Décrire si applicable]
```
