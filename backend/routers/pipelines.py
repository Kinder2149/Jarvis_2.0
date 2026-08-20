from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import json
import logging
from pydantic import BaseModel
from backend.schemas.pipeline import StartPipeline, StepValidation
from backend.database import get_connection, load_config
from backend.services.pipeline_engine import (
    create_session,
    get_session_with_steps,
    execute_step,
    validate_step as validate_step_service,
    retry_step as retry_step_service
)
from backend.services.mission_parser import parse_mission_prompt

logger = logging.getLogger("jarvis")


class MissionPromptRequest(BaseModel):
    text: str

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

LOG_PATH = Path(__file__).parent.parent / "data" / "jarvis.log"

@router.post("/parse-mission")
def parse_mission(request: MissionPromptRequest):
    try:
        result = parse_mission_prompt(request.text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Erreur inattendue lors du parsing mission : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors du parsing")


@router.post("/start")
async def start_pipeline(request: StartPipeline):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT path FROM projects WHERE id = ?", (request.project_id,))
    project_row = cursor.fetchone()
    
    if not project_row:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_path = project_row["path"]
    
    # Si une image est jointe, faire un appel vision préliminaire pour extraire la description
    enriched_input = request.initial_input or ""
    if request.attachment_base64 and request.attachment_filename:
        logger.info(f"🖼️ [PIPELINE] Image jointe détectée : {request.attachment_filename} — appel vision préliminaire")
        
        from backend.services import model_router
        from pathlib import Path as PathLib
        
        config = load_config()
        vision_model = config.get("chat", {}).get("vision_model", "anthropic/claude-sonnet-4-6")
        
        # Détecter le type MIME
        ext = PathLib(request.attachment_filename).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp"
        }
        mime = mime_map.get(ext, "image/jpeg")
        
        # Récupérer les clés API
        cursor.execute("SELECT key, value FROM app_config WHERE key IN ('openrouter_key', 'anthropic_key')")
        api_keys = {row["key"]: row["value"] for row in cursor.fetchall()}
        
        # Appel vision pour extraire la description
        vision_prompt = "Décris précisément ce que tu vois dans cette image, dans le contexte d'une mission de développement logiciel. Sois factuel et concis."
        
        try:
            vision_description = await model_router.call_model(
                model_id=vision_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{request.attachment_base64}"}}
                    ]
                }],
                api_keys=api_keys,
                session_id=None,
                step_name="vision_extraction_pipeline",
                model_type="vision",
                db_conn=db,
                module_name="pipeline"
            )
            
            # Enrichir le prompt initial avec la description
            enriched_input = f"""[Image jointe : {request.attachment_filename}]
Description : {vision_description}

---
{enriched_input}"""
            
            logger.info(f"✅ [PIPELINE] Description extraite de l'image ({len(vision_description)} caractères)")
        
        except Exception as e:
            logger.error(f"❌ [PIPELINE] Erreur lors de l'extraction vision : {e}")
            # Continuer sans la description en cas d'erreur
            enriched_input = f"[Image jointe : {request.attachment_filename} — extraction échouée]\n\n{enriched_input}"
    
    session = create_session(
        request.project_id,
        request.workflow_type,
        enriched_input,
        db,
        modele_override=request.modele_override,
        source_mission_prompt_id=request.source_mission_prompt_id
    )
    
    config = load_config()
    
    result = await execute_step(session["id"], 0, project_path, db, config)
    
    while result.get("status") == "auto_completed":
        result = await execute_step(session["id"], result["next_step"], project_path, db, config)
    
    session_with_steps = get_session_with_steps(session["id"], db)
    db.close()
    
    return {
        "session": session_with_steps,
        "execution_result": result
    }

@router.get("/{session_id}")
def get_pipeline(session_id: int):
    db = get_connection()
    session = get_session_with_steps(session_id, db)
    db.close()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@router.post("/{session_id}/validate/{step_id}")
async def validate_pipeline_step(session_id: int, step_id: int, validation: StepValidation):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT p.path FROM sessions s JOIN projects p ON s.project_id = p.id WHERE s.id = ?", (session_id,))
    project_row = cursor.fetchone()
    project_path = project_row["path"] if project_row else None
    
    result = validate_step_service(session_id, step_id, validation.model_dump(), db, project_path)
    
    import logging
    logger = logging.getLogger("uvicorn")
    
    logger.debug(f"\n{'='*80}")
    logger.debug(f"DEBUG [VALIDATE] session_id={session_id}, step_id={step_id}")
    logger.debug(f"DEBUG [VALIDATE] Result status: {result.get('status')}, next_step: {result.get('next_step')}, project_path: {project_path}")
    logger.debug(f"{'='*80}\n")
    
    logger.info(f"📋 [VALIDATE] Result status: {result.get('status')}, next_step: {result.get('next_step')}, project_path: {project_path}")
    
    if result.get("status") == "validated" and result.get("next_step") is not None:
        logger.info(f"✅ [VALIDATE] Validation OK, lancement step {result['next_step']}")
        
        # Pour les workflows atelier, project_path = "__atelier__" (valeur spéciale)
        # On doit quand même lancer l'auto-complétion des étapes suivantes
        is_atelier = project_path == "__atelier__"
        
        if project_path and (project_path != "__atelier__" or is_atelier):
            logger.debug(f"DEBUG [VALIDATE] Lancement auto-complétion (atelier={is_atelier})...")
            logger.info(f"🚀 [VALIDATE] Lancement auto-complétion (atelier={is_atelier})...")
            config = load_config()
            exec_result = await execute_step(session_id, result["next_step"], project_path, db, config)
            logger.debug(f"DEBUG [VALIDATE] exec_result status: {exec_result.get('status')}")
            logger.info(f"📊 [VALIDATE] exec_result status: {exec_result.get('status')}")
            
            while exec_result.get("status") == "auto_completed":
                logger.debug(f"DEBUG [VALIDATE] Auto-completion, step suivant: {exec_result.get('next_step')}")
                logger.info(f"🔄 [VALIDATE] Auto-completion, step suivant: {exec_result.get('next_step')}")
                exec_result = await execute_step(session_id, exec_result["next_step"], project_path, db, config)
                logger.debug(f"DEBUG [VALIDATE] exec_result status après auto-completion: {exec_result.get('status')}")
                logger.info(f"📊 [VALIDATE] exec_result status après auto-completion: {exec_result.get('status')}")
        else:
            logger.warning(f"⚠️ [VALIDATE] project_path est vide, pas d'auto-exécution")
    
    session_with_steps = get_session_with_steps(session_id, db)
    
    # Déclenchement automatique de graphify après validation d'une étape verification
    if result.get("status") == "validated":
        cursor = db.cursor()
        cursor.execute("SELECT step_name FROM pipeline_steps WHERE id = ?", (step_id,))
        step_row = cursor.fetchone()
        
        if step_row and step_row["step_name"] == "verification":
            # Récupérer le path du projet
            cursor.execute("""
                SELECT p.path 
                FROM sessions s 
                JOIN projects p ON s.project_id = p.id 
                WHERE s.id = ?
            """, (session_id,))
            proj_row = cursor.fetchone()
            
            if proj_row and proj_row["path"]:
                project_path = proj_row["path"]
                from pathlib import Path
                if Path(project_path).exists():
                    try:
                        import subprocess
                        subprocess.Popen(
                            ["graphify", "."],
                            cwd=project_path,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        logger.info(f"🔍 Graphify lancé automatiquement après validation verification pour {project_path}")
                    except FileNotFoundError:
                        logger.warning(f"⚠️ graphify non installé, mise à jour ignorée pour {project_path}")
                    except Exception as e:
                        logger.error(f"❌ Erreur lancement graphify pour {project_path}: {str(e)}")
    
    db.close()
    
    return {
        "session": session_with_steps,
        "validation_result": result
    }

@router.post("/{session_id}/retry/{step_id}")
async def retry_pipeline_step(session_id: int, step_id: int):
    db = get_connection()
    
    result = retry_step_service(session_id, step_id, db)
    
    if result.get("status") == "ready_for_retry":
        cursor = db.cursor()
        cursor.execute("SELECT path FROM sessions s JOIN projects p ON s.project_id = p.id WHERE s.id = ?", (session_id,))
        project_row = cursor.fetchone()
        
        if project_row:
            config = load_config()
            exec_result = await execute_step(session_id, result["step_index"], project_row["path"], db, config)
            
            while exec_result.get("status") == "auto_completed":
                exec_result = await execute_step(session_id, exec_result["next_step"], project_row["path"], db, config)
    
    session_with_steps = get_session_with_steps(session_id, db)
    db.close()
    
    return {
        "session": session_with_steps,
        "retry_result": result
    }

@router.post("/{session_id}/abort")
def abort_pipeline(session_id: int):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("UPDATE sessions SET status = ? WHERE id = ?", ("ABORTED", session_id))
    db.commit()
    
    session_with_steps = get_session_with_steps(session_id, db)
    db.close()
    
    return session_with_steps

@router.delete("/{session_id}", status_code=204)
def delete_pipeline(session_id: int):
    """Supprime une session pipeline et tous ses steps."""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT status FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    if row["status"] == "RUNNING":
        db.close()
        raise HTTPException(status_code=400, detail="Impossible de supprimer une session en cours")
    
    cursor.execute("DELETE FROM pipeline_steps WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()
    db.close()
    return None

@router.get("/{session_id}/costs")
def get_pipeline_costs(session_id: int):
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT step_name, model_id_chosen, input_tokens, output_tokens
        FROM model_decision_log
        WHERE session_id = ?
    """, (session_id,))
    
    rows = cursor.fetchall()
    db.close()
    
    model_prices = {
        "google/gemini-2.5-flash": 0.10,
        "google/gemini-flash-2.0": 0.10,
        "anthropic/claude-haiku-4.5": 1.00,
        "anthropic/claude-haiku-4-5": 1.00,
        "anthropic/claude-sonnet-4.5": 3.00,
        "anthropic/claude-sonnet-4-5": 3.00,
        "anthropic/claude-opus-4": 5.00,
        "anthropic/claude-opus-4.5": 5.00
    }
    
    costs = []
    for row in rows:
        model_id = row["model_id_chosen"]
        price = model_prices.get(model_id, 1.00)
        input_tokens = row["input_tokens"] or 0
        output_tokens = row["output_tokens"] or 0
        cost_usd = (input_tokens / 1e6 * price) + (output_tokens / 1e6 * price)
        
        costs.append({
            "step_name": row["step_name"],
            "model": model_id.split('/')[-1] if '/' in model_id else model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd
        })
    
    return costs

@router.get("/logs")
def get_logs(lines: int = Query(default=100), project_id: int | None = None):
    if not LOG_PATH.exists():
        return {"lines": []}
    
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        
        # Filtrage par project_id si fourni
        if project_id is not None:
            # Récupérer les session_id du projet
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE project_id = ?", (project_id,))
            session_ids = [str(row["id"]) for row in cursor.fetchall()]
            conn.close()
            
            if not session_ids:
                return {"lines": []}
            
            # Filtrer les lignes contenant ces session_id
            filtered_lines = []
            for line in all_lines:
                for session_id in session_ids:
                    if f"session {session_id}" in line.lower() or f"session_id={session_id}" in line.lower():
                        filtered_lines.append(line)
                        break
            
            last_lines = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
        else:
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {"lines": [line.rstrip() for line in last_lines]}
    
    except Exception:
        return {"lines": []}


class WriteFileRequest(BaseModel):
    path: str
    content: str


@router.post("/write-file")
def write_file(request: WriteFileRequest):
    """Écrit le contenu dans un fichier (sécurisé pour PROJET_CONTEXTE.md uniquement)."""
    file_path = Path(request.path)
    
    # Sécurité : vérifier que le chemin est dans V:\DEV\PROJETS\ et que c'est PROJET_CONTEXTE.md
    if not str(file_path).startswith("C:\\DEV\\PROJETS\\"):
        raise HTTPException(status_code=403, detail="Chemin non autorisé")
    
    if file_path.name != "PROJET_CONTEXTE.md":
        raise HTTPException(status_code=403, detail="Seul PROJET_CONTEXTE.md peut être modifié via cet endpoint")
    
    if not file_path.parent.exists():
        raise HTTPException(status_code=404, detail="Répertoire parent introuvable")
    
    try:
        file_path.write_text(request.content, encoding="utf-8")
        logger.info(f"✅ Fichier écrit : {file_path}")
        return {"status": "written", "path": str(file_path)}
    except Exception as e:
        logger.error(f"❌ Erreur écriture fichier {file_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/propose-contexte")
async def propose_projet_contexte_update(session_id: int):
    """Génère une proposition de mise à jour des sections 8 et 9 du PROJET_CONTEXTE.md."""
    db = get_connection()
    cursor = db.cursor()
    
    try:
        # 1. Vérifier que la session existe et est terminée
        cursor.execute("SELECT status, workflow_type FROM sessions WHERE id = ?", (session_id,))
        session_row = cursor.fetchone()
        
        if not session_row:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        if session_row["status"] != "COMPLETED":
            raise HTTPException(status_code=400, detail="Pipeline non terminé")
        
        # 2. Récupérer les steps complétés avec leurs résumés
        cursor.execute("""
            SELECT step_display_name, summary_fr, step_index
            FROM pipeline_steps
            WHERE session_id = ? AND status = 'COMPLETED'
            ORDER BY step_index ASC
        """, (session_id,))
        steps = cursor.fetchall()
        
        summaries = []
        for step in steps:
            if step["summary_fr"]:
                summaries.append(f"- {step['step_display_name']}: {step['summary_fr']}")
        
        summaries_text = "\n".join(summaries) if summaries else "Aucun résumé disponible"
        
        # 3. Récupérer le titre de la mission
        cursor.execute("""
            SELECT mp.titre 
            FROM mission_prompts mp 
            WHERE mp.forge_session_id = ?
        """, (session_id,))
        mission_row = cursor.fetchone()
        titre = mission_row["titre"] if mission_row and mission_row["titre"] else "Mission sans titre"
        
        # 4. Récupérer le chemin du projet
        cursor.execute("""
            SELECT p.path 
            FROM sessions s 
            JOIN projects p ON p.id = s.project_id 
            WHERE s.id = ?
        """, (session_id,))
        project_row = cursor.fetchone()
        
        if not project_row or not project_row["path"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        project_path = Path(project_row["path"])
        projet_contexte_path = project_path / "PROJET_CONTEXTE.md"
        
        # 5. Lire le fichier PROJET_CONTEXTE.md
        if not projet_contexte_path.exists():
            raise HTTPException(status_code=404, detail="PROJET_CONTEXTE.md introuvable")
        
        full_content = projet_contexte_path.read_text(encoding="utf-8")
        lines = full_content.split("\n")
        
        # 6. Extraire les sections 8 et 9
        section_8_start = None
        section_9_start = None
        next_section_after_8 = None
        next_section_after_9 = None
        
        for i, line in enumerate(lines):
            if line.startswith("## 8."):
                section_8_start = i
            elif line.startswith("## 9."):
                section_9_start = i
            elif section_8_start is not None and next_section_after_8 is None and line.startswith("##") and i > section_8_start:
                next_section_after_8 = i
            elif section_9_start is not None and next_section_after_9 is None and line.startswith("##") and i > section_9_start:
                next_section_after_9 = i
        
        if section_8_start is None or section_9_start is None:
            raise HTTPException(status_code=404, detail="Sections 8 ou 9 introuvables dans PROJET_CONTEXTE.md")
        
        # Extraire le contenu actuel des sections
        section_8_end = next_section_after_8 if next_section_after_8 else section_9_start
        section_9_end = next_section_after_9 if next_section_after_9 else len(lines)
        
        current_section_8 = "\n".join(lines[section_8_start:section_8_end]).strip()
        current_section_9 = "\n".join(lines[section_9_start:section_9_end]).strip()
        
        # 7. Appeler le LLM pour générer la proposition
        from backend.services.model_router import call_model, get_model_id
        
        config = load_config()
        model_id = get_model_id("routing", config)
        
        system_prompt = """Tu es un assistant qui met à jour la documentation d'un projet de développement.
Tu dois proposer une mise à jour des sections 8 et 9 d'un PROJET_CONTEXTE.md
basée sur ce qui vient d'être accompli dans une mission de code.
Réponds UNIQUEMENT avec un JSON valide, sans markdown, sans explication.
Format exact :
{
  "section_8": "## 8. SESSION EN COURS\\n\\n[contenu complet de la nouvelle section 8]",
  "section_9": "## 9. BACKLOG\\n\\n[contenu complet de la nouvelle section 9]"
}"""
        
        user_prompt = f"""Mission terminée : {titre}

Ce qui a été accompli (résumés des étapes) :
{summaries_text}

Section 8 actuelle :
{current_section_8}

Section 9 actuelle :
{current_section_9}

Règles :
- Section 8 : mettre à jour avec ce qui a été fait dans cette mission.
  Garder le format existant si présent (Graphify, Objectif, Fichiers concernés, Résultat).
- Section 9 : si la mission correspond à un item du backlog, le marquer ✅ et le déplacer 
  en bas avec la date. Ne pas supprimer les autres items. Conserver la numérotation.
- Ne pas inventer de nouvelles missions backlog sauf si clairement détectable 
  depuis les résumés."""
        
        response = await call_model(
            model_id=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            api_keys=config["api_keys"],
            session_id=session_id,
            step_name="propose_contexte",
            model_type="routing",
            db_conn=db,
            module_name="pipeline"
        )
        
        # 8. Parser le JSON retourné
        try:
            # Nettoyer la réponse (enlever les markdown code blocks si présents)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # Enlever les délimiteurs markdown
                cleaned_response = "\n".join([
                    line for line in cleaned_response.split("\n")
                    if not line.strip().startswith("```")
                ])
            
            proposal = json.loads(cleaned_response)
            new_section_8 = proposal["section_8"]
            new_section_9 = proposal["section_9"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Erreur parsing JSON LLM: {e}\nRéponse brute: {response}")
            raise HTTPException(status_code=500, detail=f"Erreur parsing réponse LLM: {str(e)}")
        
        # 9. Reconstituer le nouveau PROJET_CONTEXTE.md complet
        new_lines = lines[:section_8_start]
        new_lines.append(new_section_8)
        new_lines.append("")
        new_lines.append(new_section_9)
        
        if next_section_after_9:
            new_lines.append("")
            new_lines.extend(lines[next_section_after_9:])
        
        full_updated_content = "\n".join(new_lines)
        
        # 10. Retourner la proposition
        current_content = f"{current_section_8}\n\n{current_section_9}"
        proposed_content = f"{new_section_8}\n\n{new_section_9}"
        
        return {
            "current_content": current_content,
            "proposed_content": proposed_content,
            "full_updated_content": full_updated_content,
            "projet_contexte_path": str(projet_contexte_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur propose_projet_contexte_update session={session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
