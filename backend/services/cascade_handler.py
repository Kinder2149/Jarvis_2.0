import json
import logging
import re
from pathlib import Path
from backend.services.model_router import get_model_id, call_model

logger = logging.getLogger("jarvis")


async def handle_launch(mission_prompt_id: int, conversation_id: int, db, config) -> tuple:
    """
    Appelé après freeze, quand cascade_mode=True et utilisateur a confirmé "oui".
    Retourne (content, agent, instance_ref, suggest_freeze, freeze_reason).
    """
    cursor = db.cursor()
    
    # Lire mission_prompts.content depuis DB
    cursor.execute("""
        SELECT mp.content, mp.livrable_type, rs.titre
        FROM mission_prompts mp
        JOIN reflexion_sessions rs ON rs.id = mp.reflexion_session_id
        WHERE mp.id = ?
    """, (mission_prompt_id,))
    row = cursor.fetchone()
    
    if not row:
        return (
            "[MENTOR] Erreur : mission introuvable.",
            "MENTOR",
            None,
            False,
            None
        )
    
    content = row["content"]
    titre = row["titre"] or "Mission"
    
    # Parser les blocs de mission
    steps = _parse_mission_blocks(content)
    
    # Construire instance_ref
    instance_ref = {
        "type": "cascade_mission",
        "mp_id": mission_prompt_id,
        "step": 1,
        "total": len(steps),
        "steps": steps
    }
    
    # Construire le message pour l'étape 1
    step_content = steps[0] if steps else content
    
    message = (
        f"**Mission prête — Étape 1/{len(steps)}**\n\n"
        f"---\n\n"
        f"{step_content}\n\n"
        f"---\n\n"
        f"Copie ce prompt dans Cascade (Windsurf), exécute-le, "
        f"puis reviens me dire ce qui a été fait."
    )
    
    return (message, "MENTOR", instance_ref, False, None)


async def handle(conversation_id: int, message: str, current_instance_ref: dict, db, config) -> tuple:
    """
    Appelé quand instance_ref["type"] == "cascade_mission".
    Retourne (content, agent, instance_ref, suggest_freeze, freeze_reason).
    """
    # Règle de routing : message trop court = pas encore de résultat
    if len(message.strip()) < 30:
        step = current_instance_ref.get("step", 1)
        total = current_instance_ref.get("total", 1)
        steps = current_instance_ref.get("steps", [])
        
        if step <= len(steps):
            step_content = steps[step - 1]
            reminder = (
                f"**En attente de ton résultat pour l'étape {step}/{total}**\n\n"
                f"---\n\n"
                f"{step_content}\n\n"
                f"---\n\n"
                f"Reviens me dire ce qui a été fait après avoir exécuté ce prompt dans Cascade."
            )
            return (reminder, "MENTOR", current_instance_ref, False, None)
    
    # Message suffisant → valider l'étape
    return await _validate_step(conversation_id, message, current_instance_ref, db, config)


async def _validate_step(conversation_id: int, message: str, instance_ref: dict, db, config) -> tuple:
    """
    Valide l'étape courante avec un appel LLM.
    Retourne (content, agent, instance_ref, suggest_freeze, freeze_reason).
    """
    step = instance_ref.get("step", 1)
    total = instance_ref.get("total", 1)
    steps = instance_ref.get("steps", [])
    mp_id = instance_ref.get("mp_id")
    
    if step > len(steps):
        return (
            "[MENTOR] Erreur : étape invalide.",
            "MENTOR",
            instance_ref,
            False,
            None
        )
    
    # Extraire le texte de l'étape courante
    current_step_text = steps[step - 1]
    
    # Extraire les critères de réussite
    criteres = ""
    criteres_match = re.search(
        r'## Critères de réussite.*?\n(.*?)(?=\n##|\Z)',
        current_step_text,
        re.DOTALL | re.IGNORECASE
    )
    if criteres_match:
        criteres = criteres_match.group(1).strip()[:500]
    
    if not criteres:
        criteres = "Non précisés"
    
    # Charger le prompt mentor_cascade_validate
    prompts_path = Path(__file__).parent.parent / "data" / "prompts.json"
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    template = prompts.get("mentor_cascade_validate", "")
    
    # Injecter les variables
    prompt = template.replace("{{step_index}}", str(step))
    prompt = prompt.replace("{{step_total}}", str(total))
    prompt = prompt.replace("{{etape_prompt}}", current_step_text[:600])
    prompt = prompt.replace("{{criteres_succes}}", criteres)
    prompt = prompt.replace("{{resultat_utilisateur}}", message[:800])
    
    # Appel LLM
    try:
        model_id = get_model_id("analysis", config)
        llm_response = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config["api_keys"],
            session_id=mp_id,
            step_name="cascade_validate_step",
            model_type="analysis",
            db_conn=db,
            module_name="jarvis"
        )
    except Exception as e:
        logger.error(f"[CASCADE] Erreur validation LLM: {e}")
        llm_response = "Validation impossible — erreur technique."
    
    # Détecter si validation KO
    negative_words = [
        "manque", "incomplet", "incorrect", "n'est pas", "pas correct",
        "problème", "à corriger", "à revoir", "partiel", "devrait", "semble"
    ]
    
    llm_lower = llm_response.lower()
    negative_count = sum(1 for word in negative_words if word in llm_lower)
    is_ok = negative_count <= 1
    
    # Si OK et pas dernière étape → passer à la suivante
    if is_ok and step < total:
        instance_ref["step"] = step + 1
        next_step_content = steps[step]  # step+1 en index 0-based
        
        content = (
            f"✓ Étape {step} validée. {llm_response}\n\n"
            f"---\n\n"
            f"**Étape {step + 1}/{total} :**\n\n"
            f"{next_step_content}\n\n"
            f"---\n\n"
            f"Reviens me donner le résultat."
        )
        return (content, "MENTOR", instance_ref, False, None)
    
    # Si OK et dernière étape → clôture
    if is_ok and step == total:
        return await _trigger_closure(conversation_id, instance_ref, db, config)
    
    # Si pas OK → demander correction
    content = f"⚠️ Étape {step} à corriger. {llm_response}"
    return (content, "MENTOR", instance_ref, False, None)


async def _trigger_closure(conversation_id: int, instance_ref: dict, db, config) -> tuple:
    """
    Génère le document de clôture après validation de toutes les étapes.
    Retourne (content, agent, instance_ref, suggest_freeze, freeze_reason).
    """
    cursor = db.cursor()
    mp_id = instance_ref.get("mp_id")
    
    # Lire mission_prompts.content et titre
    cursor.execute("""
        SELECT mp.content, rs.titre
        FROM mission_prompts mp
        JOIN reflexion_sessions rs ON rs.id = mp.reflexion_session_id
        WHERE mp.id = ?
    """, (mp_id,))
    row = cursor.fetchone()
    
    if not row:
        return (
            "[MENTOR] Erreur : mission introuvable pour clôture.",
            "MENTOR",
            {"type": "cascade_mission_done", "mp_id": mp_id},
            False,
            None
        )
    
    content_mission = row["content"]
    titre = row["titre"] or "Mission"
    
    # Récupérer les 12 derniers messages de la conversation
    cursor.execute("""
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at DESC
        LIMIT 12
    """, (conversation_id,))
    msgs = cursor.fetchall()
    msgs = list(reversed(msgs))  # Ordre chronologique
    
    history = "\n".join([
        f"{m['role'].upper()}: {m['content'][:300]}"
        for m in msgs
    ])
    
    # Charger le prompt cloture
    prompts_path = Path(__file__).parent.parent / "data" / "prompts.json"
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    template = prompts.get("cloture", "")
    
    # Injecter les variables
    prompt = template.replace("{{previous_output_execution}}", history[:1500])
    prompt = prompt.replace("{{previous_output_document_mission}}", content_mission[:800])
    prompt = prompt.replace("{{previous_output_diagnostic}}", "")
    prompt = prompt.replace("{{previous_output_correction}}", "")
    prompt = prompt.replace("{{projet_contexte}}", "")
    prompt = prompt.replace("{{global_rules}}", "")
    
    # Appel LLM
    try:
        model_id = get_model_id("structuring", config)
        llm_response = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config["api_keys"],
            session_id=mp_id,
            step_name="cascade_closure",
            model_type="structuring",
            db_conn=db,
            module_name="jarvis"
        )
        
        # Parser le JSON
        result = json.loads(llm_response)
        section_8 = result.get("section_8", "Mission terminée.")
        changelog_line = result.get("changelog_line", "")
        commit_message = result.get("commit_message", f"feat: {titre}")
        
    except Exception as e:
        logger.error(f"[CASCADE] Erreur clôture LLM: {e}")
        section_8 = "Mission terminée."
        changelog_line = ""
        commit_message = f"feat: {titre}"
    
    # Construire le message formaté avec 3 blocs copiables
    message = (
        f"**Mission terminée — {titre}** ✅\n\n"
        f"Voici les 3 blocs à copier dans ton projet :\n\n"
        f"---\n\n"
        f"**1. PROJET_CONTEXTE.md — Section 8**\n\n"
        f"```\n{section_8}\n```\n\n"
        f"---\n\n"
        f"**2. CHANGELOG.md**\n\n"
        f"```\n{changelog_line}\n```\n\n"
        f"---\n\n"
        f"**3. Commit message**\n\n"
        f"```\n{commit_message}\n```"
    )
    
    return (
        message,
        "MENTOR",
        {"type": "cascade_mission_done", "mp_id": mp_id},
        False,
        None
    )


def _parse_mission_blocks(content: str) -> list:
    """
    Détecter les blocs "### Mission N" dans le contenu.
    Retourne une liste de strings (chaque bloc = 1 prompt Cascade complet).
    """
    # Si aucun "### Mission" dans content → retourner [content.strip()]
    if "### Mission" not in content:
        return [content.strip()]
    
    # Split sur les titres de mission
    pattern = re.compile(r'\n(### Mission \d+(?:\s*—\s*.+)?)\n', re.MULTILINE)
    parts = pattern.split(content)
    
    # Reconstruire les blocs
    blocks = []
    i = 1  # Sauter le premier élément (texte avant le premier ### Mission)
    while i < len(parts):
        if i + 1 < len(parts):
            title = parts[i].strip()
            body = parts[i + 1].strip()
            if body:
                blocks.append(f"{title}\n\n{body}")
            i += 2
        else:
            i += 1
    
    # Filtrer les blocs vides
    blocks = [b for b in blocks if b.strip()]
    
    # Si aucun bloc trouvé après parsing → retourner contenu complet
    if not blocks:
        return [content.strip()]
    
    return blocks
