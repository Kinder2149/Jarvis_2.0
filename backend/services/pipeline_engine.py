from pathlib import Path
import json
from datetime import datetime
from backend.database import get_connection
from backend.services.context_manager import build_context_envelope, inject_into_template, write_cloture_docs
from backend.services.model_router import get_model_id, call_model

PIPELINES_PATH = Path(__file__).parent.parent / "data" / "pipelines.json"
PROMPTS_PATH = Path(__file__).parent.parent / "data" / "prompts.json"

def apply_code_blocks_to_project(code_output: str, project_path: str) -> list:
    """
    Parse les blocs de code de l'output LLM et écrit les fichiers dans le projet.
    Format attendu : ```lang\n# chemin/relatif/fichier.ext\ncontenu\n```
    Retourne la liste des fichiers écrits (chemins relatifs).
    """
    import re as _re
    import logging
    logger = logging.getLogger("jarvis")
    
    written = []
    blocks = _re.findall(r'```[a-zA-Z]*\n(.*?)```', code_output, _re.DOTALL)
    
    logger.info(f"📄 [FILE_WRITE] {len(blocks)} blocs de code trouvés dans l'output")
    
    for idx, block in enumerate(blocks, 1):
        lines = block.strip().split('\n')
        if not lines:
            continue
        
        first = lines[0].strip()
        
        file_path = None
        for prefix in ('#', '//', '<!--', '/*'):
            if first.startswith(prefix):
                candidate = first[len(prefix):].strip()
                # Nettoyer les suffixes de commentaires HTML/CSS
                candidate = candidate.rstrip('->').rstrip('*/').strip()
                parts = candidate.replace('\\', '/').split('/')
                if parts and '.' in parts[-1]:
                    file_path = candidate
                    break
        
        if not file_path:
            logger.warning(f"❌ [FILE_WRITE] Bloc {idx}: aucun chemin détecté, ignoré")
            continue
        
        content = '\n'.join(lines[1:])
        try:
            full_path = Path(project_path) / file_path.lstrip('/').lstrip('\\')
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            written.append(file_path)
            logger.info(f"✅ [FILE_WRITE] Bloc {idx}: fichier écrit = '{full_path}'")
        except Exception as e:
            logger.warning(f"❌ [FILE_WRITE] Bloc {idx}: échec écriture {file_path}: {e}")
    
    logger.info(f"📊 [FILE_WRITE] Résultat: {len(written)}/{len(blocks)} fichiers écrits")
    return written


def _trigger_graphify_update(project_path: str):
    """Lance graphify . --update en arrière-plan si graphify-out/GRAPH_REPORT.md existe."""
    try:
        import subprocess as _sp
        if (Path(project_path) / "graphify-out" / "GRAPH_REPORT.md").exists():
            _sp.Popen(
                ["graphify", ".", "--update"],
                cwd=project_path,
                stdout=_sp.DEVNULL,
                stderr=_sp.DEVNULL
            )
    except Exception:
        pass

def load_pipeline_definition(workflow_type: str) -> dict:
    if not PIPELINES_PATH.exists():
        return {}
    
    with open(PIPELINES_PATH, "r", encoding="utf-8") as f:
        pipelines = json.load(f)
    
    return pipelines.get(workflow_type, {})

def load_prompt_template(prompt_key: str) -> str:
    if not PROMPTS_PATH.exists():
        return ""
    
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    return prompts.get(prompt_key, "")

def create_session(project_id: int, workflow_type: str, initial_input: str, db,
                   modele_override: str | None = None,
                   source_mission_prompt_id: int | None = None) -> dict:
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO sessions (project_id, workflow_type, status, current_step_index, modele_override, source_mission_prompt_id) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, workflow_type, "CREATED", 0, modele_override, source_mission_prompt_id)
    )
    session_id = cursor.lastrowid
    
    pipeline_def = load_pipeline_definition(workflow_type)
    steps = pipeline_def.get("steps", [])
    
    for step in steps:
        cursor.execute(
            """INSERT INTO pipeline_steps 
            (session_id, step_index, step_name, step_display_name, model_type, status, requires_validation, input_data, output_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                step["index"],
                step["name"],
                step["display_name"],
                step["model_type"],
                "PENDING",
                1 if step.get("requires_validation", False) else 0,
                initial_input if step["index"] == 0 else None,
                step.get("output_type", "text")
            )
        )
    
    db.commit()
    
    return {
        "id": session_id,
        "project_id": project_id,
        "workflow_type": workflow_type,
        "status": "CREATED",
        "current_step_index": 0
    }

def get_session_with_steps(session_id: int, db) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    
    if not session_row:
        return None
    
    cursor.execute(
        "SELECT * FROM pipeline_steps WHERE session_id = ? ORDER BY step_index",
        (session_id,)
    )
    steps_rows = cursor.fetchall()
    
    session = {
        "id": session_row["id"],
        "project_id": session_row["project_id"],
        "workflow_type": session_row["workflow_type"],
        "status": session_row["status"],
        "current_step_index": session_row["current_step_index"],
        "created_at": session_row["created_at"],
        "steps": []
    }
    
    for step_row in steps_rows:
        session["steps"].append({
            "id": step_row["id"],
            "session_id": step_row["session_id"],
            "step_index": step_row["step_index"],
            "step_name": step_row["step_name"],
            "step_display_name": step_row["step_display_name"],
            "model_type": step_row["model_type"],
            "model_used": step_row["model_used"],
            "status": step_row["status"],
            "input_data": step_row["input_data"],
            "output_data": step_row["output_data"],
            "requires_validation": bool(step_row["requires_validation"]),
            "validated_at": step_row["validated_at"],
            "created_at": step_row["created_at"],
            "output_type": dict(step_row).get("output_type", "text"),
            "sub_step_index": dict(step_row).get("sub_step_index", None),
        })
    
    return session

def _extract_json_safe(text: str) -> dict:
    """Extrait un JSON même entouré de markdown (```json ... ```)."""
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        return json.loads(text[start:end])
    except Exception:
        return {}


async def execute_step(session_id: int, step_index: int, project_path: str, db, config: dict) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    
    if not session_row:
        return {"status": "error", "error": "Session not found"}
    
    cursor.execute(
        "SELECT * FROM pipeline_steps WHERE session_id = ? AND step_index = ?",
        (session_id, step_index)
    )
    step_row = cursor.fetchone()
    
    if not step_row:
        return {"status": "error", "error": "Step not found"}
    
    cursor.execute(
        "UPDATE pipeline_steps SET status = ? WHERE id = ?",
        ("RUNNING", step_row["id"])
    )
    cursor.execute(
        "UPDATE sessions SET status = ?, current_step_index = ? WHERE id = ?",
        ("RUNNING", step_index, session_id)
    )
    db.commit()
    
    try:
        import logging
        logger = logging.getLogger("jarvis")

        pipeline_def = load_pipeline_definition(session_row["workflow_type"])
        steps_config = pipeline_def.get("steps", [])
        step_config = next((s for s in steps_config if s["index"] == step_index), None)
        
        if not step_config:
            raise Exception("Step configuration not found")
        
        cursor.execute(
            "SELECT step_name, output_data FROM pipeline_steps WHERE session_id = ? AND step_index < ? AND status = 'COMPLETED' AND (sub_step_index IS NULL OR sub_step_index = -1)",
            (session_id, step_index)
        )
        previous_rows = cursor.fetchall()
        previous_outputs = {row["step_name"]: row["output_data"] for row in previous_rows}
        
        cursor.execute(
            "SELECT input_data FROM pipeline_steps WHERE session_id = ? AND step_index = 0",
            (session_id,)
        )
        initial_input_row = cursor.fetchone()
        user_input = initial_input_row["input_data"] if initial_input_row else ""
        
        # Étapes sans appel LLM (model_type = "none")
        if step_config.get("model_type") == "none":
            import logging
            logger = logging.getLogger("jarvis")
            logger.info(f"🔧 [PIPELINE] Step {step_index} ({step_config.get('name')}) - model_type=none, requires_validation={step_config.get('requires_validation')}")
            
            if step_config.get("requires_validation"):
                # Récupérer l'output du step précédent comme contenu à afficher
                prev_output = ""
                if step_index > 0:
                    prev_row = cursor.execute(
                        """SELECT output_data FROM pipeline_steps
                           WHERE session_id=? AND step_index=? AND status='COMPLETED'""",
                        (session_id, step_index - 1)
                    ).fetchone()
                    if prev_row and prev_row["output_data"]:
                        prev_output = prev_row["output_data"]
                cursor.execute(
                    "UPDATE pipeline_steps SET status='WAITING_VALIDATION', output_data=? WHERE id=?",
                    (prev_output, step_row["id"])
                )
                cursor.execute(
                    "UPDATE sessions SET status='WAITING_VALIDATION', updated_at=datetime('now') WHERE id=?",
                    (session_id,)
                )
                db.commit()
                logger.info(f"⏸️ [PIPELINE] Step {step_index} en attente de validation")
                return {"status": "waiting_validation", "step_id": step_row["id"]}
            else:
                # Step export : assembler et écrire les fichiers démo
                if step_config.get("name") == "export":
                    logger.debug(f"DEBUG [PIPELINE] Détection step export, appel _handle_atelier_export...")
                    logger.info(f"📦 [PIPELINE] Détection step export, appel _handle_atelier_export...")
                    _handle_atelier_export(session_id, step_row["id"], db)
                    logger.debug(f"DEBUG [PIPELINE] _handle_atelier_export terminé")
                    logger.info(f"✅ [PIPELINE] _handle_atelier_export terminé")
                # Step sante_cadrage : vérifier la santé du cadrage et stocker le rapport
                elif step_config.get("name") == "sante_cadrage":
                    from backend.services.cadrage import check_cadrage_health
                    logger.info(f"🏥 [PIPELINE] Exécution check_cadrage_health pour session {session_id}")
                    
                    # Récupérer le project_id depuis la session
                    cursor.execute("SELECT project_id FROM sessions WHERE id = ?", (session_id,))
                    sess_row = cursor.fetchone()
                    if sess_row:
                        health_report = check_cadrage_health(sess_row["project_id"], db)
                        # Stocker le rapport en JSON dans output_data
                        import json
                        output_json = json.dumps(health_report, ensure_ascii=False, indent=2)
                        cursor.execute(
                            "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE id=?",
                            (output_json, step_row["id"])
                        )
                        db.commit()
                        logger.info(f"✅ [PIPELINE] Santé cadrage: {health_report['verdict_global']} ({len(health_report['checks'])} checks)")
                    else:
                        logger.error(f"❌ [PIPELINE] Session {session_id} introuvable pour sante_cadrage")
                        cursor.execute(
                            "UPDATE pipeline_steps SET status='COMPLETED' WHERE id=?",
                            (step_row["id"],)
                        )
                        db.commit()
                else:
                    logger.info(f"✅ [PIPELINE] Step {step_index} ({step_config.get('name')}) marqué COMPLETED")
                    cursor.execute(
                        "UPDATE pipeline_steps SET status='COMPLETED' WHERE id=?",
                        (step_row["id"],)
                    )
                    db.commit()
                
                # Vérifier si c'est le dernier step
                total_steps = len(steps_config)
                if step_index == total_steps - 1:
                    logger.info(f"🏁 [PIPELINE] Dernier step atteint, session COMPLETED")
                    cursor.execute(
                        "UPDATE sessions SET status='COMPLETED' WHERE id=?",
                        (session_id,)
                    )
                    # Si workflow atelier, mettre à jour le statut du prospect
                    if session_row["workflow_type"].startswith("atelier_"):
                        cursor.execute(
                            "UPDATE prospects SET statut='demo_generee', updated_at=datetime('now') WHERE session_id=?",
                            (session_id,)
                        )
                    db.commit()
                    return {"status": "completed"}
                else:
                    logger.info(f"🔄 [PIPELINE] Step {step_index} auto-complété, next_step={step_index + 1}")
                    cursor.execute(
                        "UPDATE sessions SET current_step_index=? WHERE id=?",
                        (step_index + 1, session_id)
                    )
                    db.commit()
                    return {"status": "auto_completed", "next_step": step_index + 1}
        
        # Récupérer global_context depuis le fichier
        from pathlib import Path as _Path
        _ctx_file = _Path(__file__).parent.parent / "data" / "contexts" / "global_context.md"
        global_context = _ctx_file.read_text(encoding="utf-8") if _ctx_file.exists() else ""
        
        try:
            cursor.execute("SELECT instructions FROM projects WHERE path = ?", (project_path,))
            proj_row = cursor.fetchone()
            project_instructions = proj_row["instructions"] if proj_row and proj_row["instructions"] else ""
        except Exception:
            project_instructions = ""
        
        envelope = await build_context_envelope(step_config, project_path, previous_outputs, user_input, session_row["workflow_type"], project_instructions)
        
        # Injecter global_context dans l'envelope
        envelope["global_context"] = global_context
        
        prompt_template = load_prompt_template(step_config["prompt_key"])
        prompt = inject_into_template(prompt_template, envelope)
        
        # Lire modele_override depuis la session
        modele_override = dict(session_row).get("modele_override", None)

        actual_model_type = step_config.get("model_type", "routing")
        model_id = get_model_id(actual_model_type, config, override=modele_override)
        
        messages = [{"role": "user", "content": prompt}]

        # === CHUNKING — découpage automatique si supports_chunking=True ===
        output = None
        if step_config.get("supports_chunking", False):
            import time as _time
            from backend.services import chunking as _chunking
            from backend.services.mission_parser import parse_mission_prompt as _parse_mission

            targeted_files_content = {}
            mission_data_for_chunking = {
                "objectif": user_input or "",
                "contexte": "",
                "contraintes": [],
                "criteres_reussite": [],
            }
            try:
                parsed_mission = _parse_mission(user_input or "")
                mission_data_for_chunking = parsed_mission
                for fi in parsed_mission.get("fichiers_concernes", []):
                    fp = fi.get("path", "")
                    if not fp:
                        continue
                    full_fp = Path(project_path) / fp.lstrip("/").lstrip("\\")
                    content = ""
                    if full_fp.exists():
                        try:
                            content = full_fp.read_text(encoding="utf-8", errors="ignore")
                        except Exception:
                            content = ""
                    targeted_files_content[fp] = content
            except Exception:
                targeted_files_content = {}

            budget = _chunking.estimate_tokens_budget(prompt, targeted_files_content, model_id)
            strategy = budget["recommended_strategy"]
            logger.info(
                f"[CHUNKING] strategy={strategy} files={len(targeted_files_content)} "
                f"model={model_id} total_tokens={budget['total_input_estimated']}"
            )

            if strategy == "chunk_by_file" and len(targeted_files_content) > 0:
                try:
                    sub_tasks = _chunking.split_mission_by_files(
                        mission_data_for_chunking, targeted_files_content, model_id
                    )
                    sub_outputs = []
                    for sub_task in sub_tasks:
                        t_start = _time.time()
                        sub_output = await call_model(
                            model_id,
                            [{"role": "user", "content": sub_task["prompt"]}],
                            config.get("api_keys", {}),
                            session_id,
                            step_config["name"],
                            step_config["model_type"],
                            db,
                        )
                        t_elapsed = _time.time() - t_start
                        cursor.execute(
                            """INSERT INTO pipeline_steps
                            (session_id, step_index, step_name, step_display_name, model_type,
                             status, requires_validation, output_data, output_type, model_used, sub_step_index)
                            VALUES (?, ?, ?, ?, ?, 'COMPLETED', 0, ?, ?, ?, ?)""",
                            (
                                session_id,
                                step_index,
                                step_config["name"],
                                f"{step_config['display_name']} ({sub_task['sub_step_index'] + 1}/{len(sub_tasks)})",
                                step_config["model_type"],
                                sub_output,
                                step_config.get("output_type", "text"),
                                model_id,
                                sub_task["sub_step_index"],
                            ),
                        )
                        db.commit()
                        logger.info(
                            f"[CHUNKING] sub_step_index={sub_task['sub_step_index']} "
                            f"file={sub_task['file_path']} "
                            f"input_tokens={sub_task['tokens_estimated']} "
                            f"output_tokens={_chunking.estimate_tokens(sub_output)} "
                            f"duration={t_elapsed:.1f}s"
                        )
                        sub_outputs.append(sub_output)
                    output = _chunking.merge_code_outputs(sub_outputs)
                except ValueError:
                    raise
                except Exception as _chunk_err:
                    logger.exception(f"[CHUNKING] Erreur découpage, fallback single_call: {_chunk_err}")
                    output = None

        if output is None:
            output = await call_model(
                model_id,
                messages,
                config.get("api_keys", {}),
                session_id,
                step_config["name"],
                step_config["model_type"],
                db,
            )
        
        cursor.execute(
            "UPDATE pipeline_steps SET output_data = ?, model_used = ? WHERE id = ?",
            (output, model_id, step_row["id"])
        )
        db.commit()
        
        # Si step cloture : écrire automatiquement les docs projet
        if step_config.get("name") == "cloture" and project_path:
            cloture_data = _extract_json_safe(output)
            if cloture_data:
                write_cloture_docs(cloture_data, project_path)
                logger.info(
                    "📊 [GRAPHIFY] Session terminée. Si des fichiers ont été modifiés, "
                    "lancer : graphify . --update (changement mineur) ou graphify . (refactor/nouvelle feature)"
                )
        
        if step_config.get("name") == "cloture":
            try:
                cursor.execute("SELECT project_id FROM sessions WHERE id = ?", (session_id,))
                sess_proj = cursor.fetchone()
                if sess_proj:
                    cursor.execute(
                        "DELETE FROM app_config WHERE key = ?",
                        (f"session_summary_{sess_proj['project_id']}",)
                    )
                    db.commit()
            except Exception:
                pass
        
        if step_config.get("requires_validation", False):
            cursor.execute(
                "UPDATE pipeline_steps SET status = ? WHERE id = ?",
                ("WAITING_VALIDATION", step_row["id"])
            )
            cursor.execute(
                "UPDATE sessions SET status = ? WHERE id = ?",
                ("WAITING_VALIDATION", session_id)
            )
            db.commit()
            
            return {"status": "waiting_validation", "step_id": step_row["id"], "output": output}
        
        else:
            cursor.execute(
                "UPDATE pipeline_steps SET status = ? WHERE id = ?",
                ("COMPLETED", step_row["id"])
            )
            
            total_steps = len(steps_config)
            if step_index == total_steps - 1:
                cursor.execute(
                    "UPDATE sessions SET status = ? WHERE id = ?",
                    ("COMPLETED", session_id)
                )
                # Si workflow atelier, mettre à jour le statut du prospect
                if session_row["workflow_type"].startswith("atelier_"):
                    cursor.execute(
                        "UPDATE prospects SET statut='demo_generee', updated_at=datetime('now') WHERE session_id=?",
                        (session_id,)
                    )
                db.commit()
                return {"status": "completed", "output": output}
            else:
                if step_config.get("write_files_on_complete", False) and output:
                    written = apply_code_blocks_to_project(output, project_path)
                    if written:
                        _trigger_graphify_update(project_path)
                
                cursor.execute(
                    "UPDATE sessions SET current_step_index = ? WHERE id = ?",
                    (step_index + 1, session_id)
                )
                db.commit()
                return {"status": "auto_completed", "next_step": step_index + 1, "output": output}
    
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger("jarvis")
        logger.error(
            f"[PIPELINE] Session {session_id} step {step_index} FAILED: {e}\n{traceback.format_exc()}"
        )
        
        cursor.execute(
            "UPDATE pipeline_steps SET status = ?, error_message = ? WHERE id = ?",
            ("FAILED", str(e), step_row["id"])
        )
        cursor.execute(
            "UPDATE sessions SET status = ? WHERE id = ?",
            ("FAILED", session_id)
        )
        db.commit()
        
        return {"status": "failed", "error": str(e)}

def validate_step(session_id: int, step_id: int, validation: dict, db, project_path: str = None) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM pipeline_steps WHERE id = ?", (step_id,))
    step_row = cursor.fetchone()
    
    if not step_row:
        return {"status": "error", "error": "Step not found"}
    
    if not validation.get("approved", False):
        # Rejet : marquer l'étape FAILED avec le feedback utilisateur
        feedback = validation.get("feedback", "Rejeté par l'utilisateur")
        cursor.execute(
            "UPDATE pipeline_steps SET status = ?, error_message = ? WHERE id = ?",
            ("FAILED", feedback, step_id)
        )
        # Laisser la session en WAITING_VALIDATION pour permettre le retry
        cursor.execute(
            "UPDATE sessions SET status = ? WHERE id = ?",
            ("WAITING_VALIDATION", session_id)
        )
        db.commit()
        return {"status": "rejected", "step_id": step_id, "feedback": feedback}
    
    edited_output = validation.get("edited_output")
    if edited_output:
        cursor.execute(
            "UPDATE pipeline_steps SET output_data = ? WHERE id = ?",
            (edited_output, step_id)
        )
    
    cursor.execute(
        "UPDATE pipeline_steps SET status = ?, validated_at = ? WHERE id = ?",
        ("COMPLETED", datetime.now().isoformat(), step_id)
    )
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session_row = cursor.fetchone()
    
    written_files = []
    pipeline_def_v = load_pipeline_definition(session_row["workflow_type"])
    steps_config_v = pipeline_def_v.get("steps", [])
    current_step_cfg = next((s for s in steps_config_v if s["name"] == step_row["step_name"]), None)

    logger.debug(f"\n[VALIDATE_DEBUG] step_name={step_row['step_name']}, workflow={session_row['workflow_type']}, project_path={project_path}")
    logger.debug(f"[VALIDATE_DEBUG] current_step_cfg={current_step_cfg}")

    if current_step_cfg and current_step_cfg.get("write_files_from_step") and project_path:
        source_name = current_step_cfg["write_files_from_step"]
        source_row = cursor.execute(
            "SELECT output_data FROM pipeline_steps WHERE session_id = ? AND step_name = ? AND status = 'COMPLETED' AND (sub_step_index IS NULL OR sub_step_index = -1)",
            (session_id, source_name)
        ).fetchone()
        if not source_row:
            source_row = cursor.execute(
                "SELECT output_data FROM pipeline_steps WHERE session_id = ? AND step_name = ? AND status = 'COMPLETED' ORDER BY id ASC",
                (session_id, source_name)
            ).fetchone()
        # Fallback : si output_data vide sur la row principale, merger les sub-steps
        if source_row and not source_row["output_data"]:
            sub_rows = cursor.execute(
                "SELECT output_data FROM pipeline_steps WHERE session_id = ? AND step_name = ? AND status = 'COMPLETED' AND sub_step_index IS NOT NULL ORDER BY sub_step_index ASC",
                (session_id, source_name)
            ).fetchall()
            if sub_rows:
                merged = "\n\n".join(r["output_data"] for r in sub_rows if r["output_data"])
                source_row = {"output_data": merged}
        if source_row and source_row["output_data"]:
            od = source_row["output_data"]
            written_files = apply_code_blocks_to_project(od, project_path)
            if written_files:
                _trigger_graphify_update(project_path)
    
    pipeline_def = load_pipeline_definition(session_row["workflow_type"])
    total_steps = len(pipeline_def.get("steps", []))
    
    if step_row["step_name"] == "cloture" and project_path:
        raw_cloture = edited_output or step_row["output_data"]
        cloture_json = _extract_json_safe(raw_cloture)
        if cloture_json:
            write_cloture_docs(cloture_json, project_path)
    
    if step_row["step_index"] == total_steps - 1:
        cursor.execute(
            "UPDATE sessions SET status = ? WHERE id = ?",
            ("COMPLETED", session_id)
        )
        db.commit()
        return {"status": "completed", "written_files": written_files}
    else:
        cursor.execute(
            "UPDATE sessions SET status = ?, current_step_index = ? WHERE id = ?",
            ("RUNNING", step_row["step_index"] + 1, session_id)
        )
        db.commit()
        return {"status": "validated", "next_step": step_row["step_index"] + 1, "written_files": written_files}

def retry_step(session_id: int, step_id: int, db) -> dict:
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM pipeline_steps WHERE id = ?", (step_id,))
    step_row = cursor.fetchone()
    
    if not step_row:
        return {"status": "error", "error": "Step not found"}
    
    cursor.execute(
        "UPDATE pipeline_steps SET status = ?, output_data = NULL, error_message = NULL WHERE id = ?",
        ("PENDING", step_id)
    )
    cursor.execute(
        "UPDATE sessions SET status = ?, current_step_index = ? WHERE id = ?",
        ("RUNNING", step_row["step_index"], session_id)
    )
    db.commit()
    
    return {"status": "ready_for_retry", "step_index": step_row["step_index"]}


def _handle_atelier_export(session_id: int, step_id: int, db):
    """Écrit les 5 fichiers démo depuis les outputs des steps génération."""
    import logging
    logger = logging.getLogger("jarvis")
    
    logger.debug(f"\n{'='*80}")
    logger.debug(f"DEBUG [ATELIER_EXPORT] ENTRÉE FONCTION - session_id={session_id}, step_id={step_id}")
    logger.debug(f"{'='*80}\n")
    
    try:
        logger.debug("DEBUG [ATELIER_EXPORT] Import save_demo_files...")
        from backend.services.atelier_service import save_demo_files
        cursor = db.cursor()
        
        logger.debug(f"DEBUG [ATELIER_EXPORT] Démarrage export pour session {session_id}")
        logger.info(f"🚀 [ATELIER_EXPORT] Démarrage export pour session {session_id}")

        # Récupérer les outputs des 5 steps génération
        raw_outputs = {}
        for step_name in ["generation_css", "generation_html", "generation_script", "generation_admin_html", "generation_admin_js"]:
            row = cursor.execute(
                """SELECT output_data FROM pipeline_steps
                   WHERE session_id=? AND step_name=? AND status='COMPLETED'""",
                (session_id, step_name)
            ).fetchone()
            if row and row["output_data"]:
                raw_outputs[step_name] = row["output_data"]
                logger.info(f"✅ [ATELIER_EXPORT] {step_name}: {len(row['output_data'])} chars")
            else:
                logger.error(f"❌ [ATELIER_EXPORT] {step_name}: MANQUANT ou VIDE")

        # Vérifier que tous les outputs sont présents
        required_steps = ["generation_css", "generation_html", "generation_script", "generation_admin_html", "generation_admin_js"]
        missing = [s for s in required_steps if s not in raw_outputs]
        if missing:
            error_msg = f"Outputs manquants pour l'export: {', '.join(missing)}"
            logger.error(f"❌ [ATELIER_EXPORT] {error_msg}")
            cursor.execute(
                "UPDATE pipeline_steps SET status='FAILED', output_data=? WHERE id=?",
                (error_msg, step_id)
            )
            db.commit()
            raise ValueError(error_msg)

        # Récupérer le slug depuis l'output du step analyse_site
        slug_row = cursor.execute(
            """SELECT output_data FROM pipeline_steps
               WHERE session_id=? AND step_name='analyse_site' AND status='COMPLETED'""",
            (session_id,)
        ).fetchone()
        slug = "demo-inconnue"
        if slug_row and slug_row["output_data"]:
            try:
                analyse = _extract_json_safe(slug_row["output_data"])
                slug = analyse.get("slug", "demo-inconnue")
                logger.info(f"📌 [ATELIER_EXPORT] Slug extrait: {slug}")
            except Exception as e:
                logger.warning(f"⚠️ [ATELIER_EXPORT] Erreur extraction slug: {e}")

        # Récupérer le nom du prospect pour nommer le dossier client
        prospect_row = cursor.execute(
            "SELECT nom FROM prospects WHERE session_id=?", (session_id,)
        ).fetchone()
        client_nom = prospect_row["nom"] if prospect_row else slug
        logger.info(f"👤 [ATELIER_EXPORT] Nom client: {client_nom}")

        # Appeler save_demo_files
        logger.info(f"💾 [ATELIER_EXPORT] Appel save_demo_files...")
        demo_path = save_demo_files(slug, raw_outputs, client_nom=client_nom)
        logger.info(f"✅ [ATELIER_EXPORT] Démo créée dans: {demo_path}")

        # Mettre à jour demo_path et statut dans la table prospects
        cursor.execute(
            "UPDATE prospects SET demo_path=?, statut='demo_generee', updated_at=datetime('now') WHERE session_id=?",
            (str(demo_path), session_id)
        )
        cursor.execute(
            "UPDATE pipeline_steps SET status='COMPLETED', output_data=? WHERE id=?",
            (f"Démo générée dans {demo_path}", step_id)
        )
        db.commit()
        logger.info(f"🎉 [ATELIER_EXPORT] Export terminé avec succès")
        
    except Exception as e:
        logger.debug(f"\n{'='*80}")
        logger.debug(f"DEBUG [ATELIER_EXPORT] EXCEPTION CAPTURÉE: {type(e).__name__}: {str(e)}")
        logger.debug(f"{'='*80}\n")
        logger.error(f"💥 [ATELIER_EXPORT] ERREUR CRITIQUE: {str(e)}")
        import traceback
        logger.error(f"💥 [ATELIER_EXPORT] Traceback:\n{traceback.format_exc()}")
        cursor.execute(
            "UPDATE pipeline_steps SET status='FAILED', output_data=? WHERE id=?",
            (f"Erreur export: {str(e)}", step_id)
        )
        db.commit()
        raise
