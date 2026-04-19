# MISSION 01 — Backend : Champ Instructions Projet

## PROMPT À COPIER-COLLER DANS CASCADE

## (produit par Claude — copier tel quel sans modifier)

```text
Lis en premier, dans cet ordre :
1. PROJET_CONTEXTE.md (source de vérité absolue)
2. temp/SPEC_FRONTEND_V2.md (spec frontend V2)

Confirme en 1 phrase que tu as bien lu PROJET_CONTEXTE.md en citant l'objectif du projet.

---

MISSION : Backend — Ajout champ instructions projet

OBJECTIF :
Ajouter un champ `instructions` (texte libre) aux projets JARVIS.
Ce champ permettra à l'utilisateur de stocker un contexte permanent par projet,
visible et éditable depuis la vue projet V2. Comme le "System prompt" d'un projet Claude.

PÉRIMÈTRE :
Fichiers à modifier :
- backend/database.py
- backend/schemas/project.py
- backend/routers/projects.py

Aucun autre fichier ne doit être touché.

---

INSTRUCTIONS DÉTAILLÉES :

### 1. backend/database.py — Migration SQLite

Dans la fonction `init_db()`, après le bloc try/except existant qui ajoute `local_path`,
ajouter un nouveau bloc try/except identique pour ajouter la colonne `instructions` :

```python
try:
    cursor.execute("ALTER TABLE projects ADD COLUMN instructions TEXT DEFAULT ''")
    conn.commit()
except sqlite3.OperationalError:
    pass
```

### 2. backend/schemas/project.py — Schemas Pydantic

Modifier les schemas existants :

- `ProjectCreate` : ajouter `instructions: str = ""`
- `Project` : ajouter `instructions: str = ""`

Ajouter un nouveau schema `ProjectUpdate` :
```python
class ProjectUpdate(BaseModel):
    local_path: str | None = None
    instructions: str | None = None
```

### 3. backend/routers/projects.py — Router

**a) Importer ProjectUpdate :**
Modifier l'import existant pour inclure `ProjectUpdate`.

**b) list_projects() — GET /**
Dans la construction de chaque dictionnaire projet, ajouter :
```python
"instructions": row["instructions"] if "instructions" in row.keys() else ""
```

**c) get_project() — GET /{project_id}**
Dans `project_data`, ajouter :
```python
"instructions": row["instructions"] if "instructions" in row.keys() else ""
```

**d) create_project() — POST /**
- Ajouter `instructions = project.instructions` dans la logique
- Modifier l'INSERT SQL : `INSERT INTO projects (name, path, type, local_path, instructions) VALUES (?, ?, ?, ?, ?)`
- Ajouter `instructions` comme 5e paramètre dans le tuple
- Ajouter `"instructions": instructions` dans le dict de retour

**e) update_project() — PATCH /{project_id}**
Remplacer la signature actuelle (qui accepte local_path en query param) par :
```python
@router.patch("/{project_id}")
def update_project(project_id: int, data: ProjectUpdate):
```

Modifier la logique pour :
- Récupérer les valeurs actuelles si le champ n'est pas fourni dans data
- Mettre à jour `local_path` si `data.local_path is not None`
- Mettre à jour `instructions` si `data.instructions is not None`
- Exécuter un seul UPDATE avec les deux champs
- Retourner `{"message": "Projet mis à jour", "local_path": ..., "instructions": ...}`

---

TESTS MANUELS (3 étapes) :

1. Redémarrer le serveur. Vérifier qu'il démarre sans erreur dans les logs.

2. Via le navigateur sur http://localhost:8000/docs :
   - POST /api/projects avec body `{"name": "Test", "path": "C:\\", "type": "test", "instructions": "Mon contexte test"}`
   - Vérifier que la réponse contient `"instructions": "Mon contexte test"`

3. GET /api/projects/{id} sur le projet créé → vérifier que `instructions` est bien retourné.
   PATCH /api/projects/{id} avec body `{"instructions": "Nouveau contexte"}` → vérifier la mise à jour.

FIN DE MISSION :
- Serveur redémarre sans erreur
- Tests manuels validés
- CHANGELOG.md mis à jour (section courante, 1 ligne)
- PROJET_CONTEXTE.md section 8 mis à jour
```
