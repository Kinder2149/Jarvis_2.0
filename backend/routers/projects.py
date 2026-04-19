from fastapi import APIRouter, HTTPException
from pathlib import Path
from backend.schemas.project import Project, ProjectCreate, ProjectUpdate
from backend.database import get_connection
from backend.services.file_service import parse_projet_contexte

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("")
def list_projects(module_type: str | None = None, parent_dossier_id: int | None = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Construire la requête avec filtres
    query = "SELECT * FROM projects WHERE 1=1"
    params = []
    
    if module_type:
        query += " AND module_type = ?"
        params.append(module_type)
    
    if parent_dossier_id is not None:
        query += " AND parent_dossier_id = ?"
        params.append(parent_dossier_id)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    conn.close()
    
    projects = []
    for row in rows:
        local_path = row["local_path"] if "local_path" in row.keys() else None
        module_type_val = row["module_type"] if "module_type" in row.keys() else "dossier"
        category_val = row["category"] if "category" in row.keys() else None
        parent_dossier_id_val = row["parent_dossier_id"] if "parent_dossier_id" in row.keys() else None
        
        projects.append({
            "id": row["id"],
            "name": row["name"],
            "path": row["path"],
            "type": row["type"],
            "local_path": local_path,
            "instructions": row["instructions"] if "instructions" in row.keys() else "",
            "module_type": module_type_val,
            "category": category_val,
            "parent_dossier_id": parent_dossier_id_val,
            "has_projet_contexte": Path(row["path"]).joinpath("PROJET_CONTEXTE.md").exists(),
            "created_at": row["created_at"]
        })
    
    return projects

@router.post("")
def create_project(project: ProjectCreate):
    import logging
    import os
    from datetime import datetime
    logger = logging.getLogger("jarvis")
    logger.info(f"Création projet - Données reçues: name={project.name}, path={project.path}, type={project.type}, local_path={project.local_path}")
    
    path = Path(project.path)
    
    # Si module_type='code', créer le dossier Windows et PROJET_CONTEXTE.md
    if project.module_type == 'code':
        if path.exists():
            logger.error(f"Le projet existe déjà: {project.path}")
            raise HTTPException(status_code=400, detail="Ce projet existe déjà")
        
        # Vérifier que le répertoire parent existe (évite erreur en tests)
        parent_dir = path.parent
        if not parent_dir.exists():
            logger.warning(f"Répertoire parent inexistant: {parent_dir}. Création du dossier ignorée (environnement de test).")
        else:
            try:
                os.makedirs(str(path), exist_ok=False)
                logger.info(f"Dossier créé: {path}")
                
                # Créer PROJET_CONTEXTE.md
                contexte_path = path / "PROJET_CONTEXTE.md"
                contexte_content = f"""# 1. IDENTIFICATION DU PROJET
- Nom : {project.name}
- Type : {project.category or 'non spécifié'}
- Chemin : {project.path}
- Créé le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# 2. STACK TECHNIQUE
(à compléter)

# 3. DÉPENDANCES
(à compléter)

# 4. ARCHITECTURE
(à compléter)

# 5. PROBLÈMES CONNUS
(à compléter)

# 6. ROADMAP
(à compléter)

# 8. DERNIÈRE SESSION
(à compléter)

# 9. BACKLOG
(à compléter)
"""
                contexte_path.write_text(contexte_content, encoding='utf-8')
                logger.info(f"PROJET_CONTEXTE.md créé: {contexte_path}")
            except Exception as e:
                logger.error(f"Erreur création dossier/fichier: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Erreur création du projet: {str(e)}")
    else:
        # Pour les dossiers normaux, vérifier que le chemin existe
        if not path.exists():
            logger.error(f"Chemin inexistant: {project.path}")
            raise HTTPException(status_code=400, detail="Le chemin spécifié n'existe pas")
    
    name = project.name
    type_project = project.type
    has_projet_contexte = path.joinpath("PROJET_CONTEXTE.md").exists()
    
    if has_projet_contexte:
        sections = parse_projet_contexte(str(path))
        if "1" in sections:
            content = sections["1"]
            for line in content.split("\n"):
                if "Nom" in line and "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        name = parts[2].strip()
                elif "Type" in line and "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        type_project = parts[2].strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        local_path = project.local_path
        instructions = project.instructions
        module_type = project.module_type
        category = project.category
        parent_dossier_id = project.parent_dossier_id
        
        cursor.execute(
            "INSERT INTO projects (name, path, type, local_path, instructions, module_type, category, parent_dossier_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, str(path), type_project, local_path, instructions, module_type, category, parent_dossier_id)
        )
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": project_id,
            "name": name,
            "path": str(path),
            "type": type_project,
            "local_path": local_path,
            "instructions": instructions,
            "module_type": module_type,
            "category": category,
            "parent_dossier_id": parent_dossier_id,
            "has_projet_contexte": has_projet_contexte,
            "created_at": ""
        }
    except Exception as e:
        logger.error(f"Erreur création projet: {str(e)}", exc_info=True)
        conn.close()
        
        # Message d'erreur clair pour l'utilisateur
        error_msg = str(e)
        if "UNIQUE constraint failed: projects.path" in error_msg:
            raise HTTPException(status_code=400, detail=f"Ce chemin existe déjà dans un autre projet")
        else:
            raise HTTPException(status_code=400, detail=f"Erreur lors de la création: {error_msg}")

@router.get("/{project_id}")
def get_project(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    cursor.execute(
        "SELECT * FROM sessions WHERE project_id = ? AND status NOT IN ('COMPLETED', 'ABORTED') ORDER BY created_at DESC LIMIT 1",
        (project_id,)
    )
    session_row = cursor.fetchone()
    conn.close()
    
    local_path = row["local_path"] if "local_path" in row.keys() else None
    module_type_val = row["module_type"] if "module_type" in row.keys() else "dossier"
    category_val = row["category"] if "category" in row.keys() else None
    parent_dossier_id_val = row["parent_dossier_id"] if "parent_dossier_id" in row.keys() else None
    
    project_data = {
        "id": row["id"],
        "name": row["name"],
        "path": row["path"],
        "type": row["type"],
        "local_path": local_path,
        "instructions": row["instructions"] if "instructions" in row.keys() else "",
        "module_type": module_type_val,
        "category": category_val,
        "parent_dossier_id": parent_dossier_id_val,
        "has_projet_contexte": Path(row["path"]).joinpath("PROJET_CONTEXTE.md").exists(),
        "created_at": row["created_at"]
    }
    
    if session_row:
        project_data["active_session"] = {
            "id": session_row["id"],
            "workflow_type": session_row["workflow_type"],
            "status": session_row["status"],
            "current_step_index": session_row["current_step_index"]
        }
    
    return project_data

@router.delete("/{project_id}")
def delete_project(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Projet supprimé"}

@router.get("/{project_id}/active-session")
def get_active_session(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sessions WHERE project_id = ? AND status NOT IN ('COMPLETED', 'ABORTED') ORDER BY created_at DESC LIMIT 1",
        (project_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "workflow_type": row["workflow_type"],
        "status": row["status"],
        "current_step_index": row["current_step_index"],
        "created_at": row["created_at"]
    }

@router.get("/{project_id}/sessions")
def get_project_sessions(project_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT s.*, COUNT(ps.id) as total_steps FROM sessions s LEFT JOIN pipeline_steps ps ON s.id = ps.session_id WHERE s.project_id = ? GROUP BY s.id ORDER BY s.created_at DESC",
        (project_id,)
    )
    rows = cursor.fetchall()
    
    # Table de prix modèles ($/M tokens)
    model_prices = {
        "google/gemini-2.0-flash-001": 0.10,
        "google/gemini-flash-2.0": 0.10,
        "anthropic/claude-haiku-4.5": 1.00,
        "anthropic/claude-haiku-4-5": 1.00,
        "anthropic/claude-sonnet-4.5": 3.00,
        "anthropic/claude-sonnet-4-5": 3.00,
        "anthropic/claude-opus-4": 5.00,
        "anthropic/claude-opus-4.5": 5.00
    }
    
    sessions = []
    for row in rows:
        session_id = row["id"]
        
        # Calculer coût total pour cette session
        cursor.execute(
            "SELECT model_id_chosen, input_tokens, output_tokens FROM model_decision_log WHERE session_id = ?",
            (session_id,)
        )
        log_rows = cursor.fetchall()
        
        total_cost_usd = 0.0
        for log_row in log_rows:
            model_id = log_row["model_id_chosen"]
            price = model_prices.get(model_id, 1.00)
            input_tokens = log_row["input_tokens"] or 0
            output_tokens = log_row["output_tokens"] or 0
            total_cost_usd += (input_tokens + output_tokens) / 1_000_000 * price
        
        sessions.append({
            "id": row["id"],
            "project_id": row["project_id"],
            "workflow_type": row["workflow_type"],
            "status": row["status"],
            "current_step_index": row["current_step_index"],
            "total_steps": row["total_steps"],
            "created_at": row["created_at"],
            "total_cost_usd": round(total_cost_usd, 4)
        })
    
    conn.close()
    return sessions

@router.patch("/{project_id}")
def update_project(project_id: int, data: ProjectUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Récupérer valeurs actuelles si non fournies
    local_path = data.local_path if data.local_path is not None else (row["local_path"] if "local_path" in row.keys() else None)
    instructions = data.instructions if data.instructions is not None else (row["instructions"] if "instructions" in row.keys() else "")
    parent_dossier_id = data.parent_dossier_id if hasattr(data, 'parent_dossier_id') and data.parent_dossier_id is not None else (row["parent_dossier_id"] if "parent_dossier_id" in row.keys() else None)
    
    cursor.execute(
        "UPDATE projects SET local_path = ?, instructions = ?, parent_dossier_id = ? WHERE id = ?",
        (local_path, instructions, parent_dossier_id, project_id)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Projet mis à jour", "local_path": local_path, "instructions": instructions, "parent_dossier_id": parent_dossier_id}

@router.post("/{project_id}/route-mission")
async def route_mission(project_id: int, body: dict):
    """Analyse une description de mission et retourne le workflow_type approprié."""
    import json as _json
    from backend.services.model_router import get_model_id, call_model
    from backend.services.file_service import get_sections
    import re
    
    mission = body.get("mission", "")
    if not mission:
        raise HTTPException(status_code=400, detail="Le champ 'mission' est requis")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ? AND module_type = 'code'", (project_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Projet code non trouvé")
    
    project_path = row["path"]
    
    # Récupérer global_context
    try:
        cursor.execute("SELECT value FROM app_config WHERE key = 'global_context'")
        gc_row = cursor.fetchone()
        global_context = gc_row["value"] if gc_row else ""
    except Exception:
        global_context = ""
    
    # Récupérer api_keys
    cursor.execute("SELECT key, value FROM app_config WHERE category = 'api_keys'")
    api_keys = {r["key"]: r["value"] for r in cursor.fetchall()}
    
    conn.close()
    
    # Charger le prompt
    prompts_path = Path(__file__).parent.parent / "data" / "prompts.json"
    with open(prompts_path, encoding="utf-8") as f:
        prompts = _json.load(f)
    template = prompts.get("code_mission_router", "")
    
    # Charger contexte projet (sections 1+2)
    try:
        projet_contexte = get_sections(project_path, [1, 2])
    except Exception:
        projet_contexte = ""
    
    # Injecter dans le template
    prompt = template.replace("{{global_context}}", global_context)
    prompt = prompt.replace("{{user_input}}", mission)
    prompt = prompt.replace("{{projet_contexte}}", projet_contexte)
    
    # Nettoyer séparateur si global_context vide
    if not global_context.strip():
        prompt = re.sub(r'^\s*---\s*\n', '', prompt, flags=re.MULTILINE)
    
    # Charger config
    config_path = Path(__file__).parent.parent / "data" / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            config = _json.load(f)
    except Exception:
        config = {}
    
    config["api_keys"] = api_keys
    
    try:
        model_id = get_model_id("routing", config)
        messages = [{"role": "user", "content": prompt}]
        result_text = await call_model(model_id, messages, api_keys, None, "route_mission", "routing", None)
        
        # Parser JSON
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = re.sub(r'^```[a-z]*\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)
        result = _json.loads(result_text)
    except Exception as e:
        result = {
            "workflow_type": "mission_complexe",
            "confidence": "low",
            "reasoning": f"Routing automatique indisponible ({str(e)[:50]})",
            "mission_structured": mission
        }
    
    return result

@router.get("/{project_id}/scan")
async def scan_project(project_id: int):
    """
    Scan l'état d'un projet code :
    - Vérifie les fichiers de configuration (PROJET_CONTEXTE.md, graphify, etc.)
    - Détermine le workflow suggéré selon l'état du dossier
    - Retourne un résumé de session (avec cache 24h)
    """
    import json as _json
    from datetime import datetime, timedelta
    from pathlib import Path as _Path
    from backend.services.model_router import get_model_id, call_model
    from backend.services.file_service import get_sections

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM projects WHERE id = ? AND module_type = 'code'", (project_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Projet code non trouvé")

    project_path = row["path"]
    path = _Path(project_path)

    # --- Vérification des fichiers de configuration ---
    has_projet_contexte = (path / "PROJET_CONTEXTE.md").exists()
    has_stack_standard = (path / "STACK_STANDARD.md").exists()
    has_graphify = (path / "graphify-out" / "GRAPH_REPORT.md").exists()
    has_changelog = (path / "CHANGELOG.md").exists()

    # --- Workflow suggéré (logique sans LLM) ---
    suggested_workflow = None
    if not path.exists():
        suggested_workflow = "nouveau_projet"
    elif not has_projet_contexte:
        try:
            root_files = [f for f in path.iterdir()
                          if f.is_file() and not f.name.startswith('.')]
            suggested_workflow = "nouveau_projet" if len(root_files) < 3 else "projet_existant"
        except Exception:
            suggested_workflow = "projet_existant"
    # Si has_projet_contexte → suggested_workflow reste None (utilisateur décrit sa mission)

    # --- Session summary avec cache 24h ---
    session_summary = None
    if has_projet_contexte:
        cache_key = f"session_summary_{project_id}"
        try:
            cursor.execute("SELECT value FROM app_config WHERE key = ?", (cache_key,))
            cache_row = cursor.fetchone()

            use_cache = False
            if cache_row and cache_row["value"]:
                try:
                    cached = _json.loads(cache_row["value"])
                    cached_time = datetime.fromisoformat(cached.get("generated_at", "2000-01-01"))
                    if datetime.now() - cached_time < timedelta(hours=24):
                        use_cache = True
                        session_summary = cached.get("summary", "")
                except Exception:
                    pass

            if not use_cache:
                # Générer le résumé via LLM
                try:
                    projet_contexte = get_sections(project_path, [1, 8, 9])

                    prompts_path = _Path(__file__).parent.parent / "data" / "prompts.json"
                    with open(prompts_path, encoding="utf-8") as f:
                        prompts = _json.load(f)
                    template = prompts.get("orientation", "")
                    prompt = template.replace("{{projet_contexte}}", projet_contexte)

                    cursor.execute("SELECT key, value FROM app_config WHERE category = 'api_keys'")
                    api_keys = {r["key"]: r["value"] or "" for r in cursor.fetchall()}

                    config_path = _Path(__file__).parent.parent / "data" / "config.json"
                    try:
                        with open(config_path, encoding="utf-8") as f:
                            config = _json.load(f)
                    except Exception:
                        config = {}
                    config["api_keys"] = api_keys

                    model_id = get_model_id("routing", config)
                    if model_id and api_keys.get("openrouter_key"):
                        messages = [{"role": "user", "content": prompt}]
                        summary = await call_model(
                            model_id, messages, api_keys,
                            None, "scan_summary", "routing", None
                        )
                        session_summary = summary

                        # Stocker en cache (JSON avec timestamp)
                        cache_data = _json.dumps({
                            "summary": summary,
                            "generated_at": datetime.now().isoformat()
                        })
                        cursor.execute(
                            "INSERT OR REPLACE INTO app_config (key, value, category) VALUES (?, ?, ?)",
                            (cache_key, cache_data, "cache")
                        )
                        conn.commit()

                except Exception as e:
                    import logging
                    logging.getLogger("jarvis").warning(f"[SCAN] Erreur génération summary: {e}")

        except Exception as e:
            import logging
            logging.getLogger("jarvis").warning(f"[SCAN] Erreur cache: {e}")

    conn.close()

    return {
        "project_id": project_id,
        "project_path": project_path,
        "has_projet_contexte": has_projet_contexte,
        "has_stack_standard": has_stack_standard,
        "has_graphify": has_graphify,
        "has_changelog": has_changelog,
        "suggested_workflow": suggested_workflow,
        "session_summary": session_summary
    }

@router.post("/{project_id}/init-graphify")
def init_graphify(project_id: int):
    """
    Lance l'initialisation de graphify dans le dossier projet.
    Non-bloquant : retourne immédiatement, graphify tourne en arrière-plan.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT path FROM projects WHERE id = ? AND module_type = 'code'", (project_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    project_path = row["path"]

    if not Path(project_path).exists():
        raise HTTPException(status_code=400, detail="Le dossier projet n'existe pas")

    try:
        import subprocess
        subprocess.Popen(
            ["graphify", "."],
            cwd=project_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "started", "message": "Initialisation graphify lancée en arrière-plan"}
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="graphify non trouvé. Installer avec : pip install graphifyy"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lancement graphify: {str(e)}")
