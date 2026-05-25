"""
Plan Executor — JARVIS Phase 1
Appelé par APScheduler toutes les 5s.
Avance les plans CONFIRMED/EN_COURS étape par étape.
"""
import asyncio
import json
import logging
from backend.database import get_connection, load_config

logger = logging.getLogger("jarvis")


# ── Point d'entrée APScheduler ────────────────────────────────────────────────

async def tick_all_plans() -> None:
    """Tick principal : avance tous les plans actifs."""
    db = get_connection()
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, home_conversation_id, title, status
            FROM jarvis_plans
            WHERE status IN ('CONFIRMED', 'EN_COURS')
        """)
        plans = [dict(r) for r in cursor.fetchall()]
        
        for plan in plans:
            # Marquer EN_COURS si encore CONFIRMED
            if plan["status"] == "CONFIRMED":
                db.execute("""
                    UPDATE jarvis_plans
                    SET status = 'EN_COURS', updated_at = datetime('now')
                    WHERE id = ?
                """, (plan["id"],))
                db.commit()
                plan["status"] = "EN_COURS"
            
            await _tick_plan(plan, db)
    except Exception as e:
        logger.error(f"[PLAN_EXECUTOR] Erreur tick_all_plans: {e}")
    finally:
        db.close()


# ── Avancement d'un plan ──────────────────────────────────────────────────────

async def _tick_plan(plan: dict, db) -> None:
    """Avance un plan : démarre les étapes prêtes, détecte fin/échec."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, plan_id, step_order, agent, title, input_message,
               output_text, error_message, sub_conversation_id,
               status, depends_on
        FROM jarvis_plan_steps
        WHERE plan_id = ? ORDER BY step_order
    """, (plan["id"],))
    steps = [dict(r) for r in cursor.fetchall()]
    
    if not steps:
        return

    # Vérifier fin de plan
    if all(s["status"] == "TERMINEE" for s in steps):
        _finalize_plan(plan, steps, db)
        return

    if any(s["status"] == "ECHEC" for s in steps):
        _fail_plan(plan, steps, db)
        return

    # Cas suspension : une étape est EN_ATTENTE_UTILISATEUR et aucune autre n'est
    # prête à démarrer (EN_ATTENTE avec dépendances satisfaites).
    # Le plan reste EN_COURS — l'utilisateur doit répondre pour le débloquer.
    waiting_user = any(s["status"] == "EN_ATTENTE_UTILISATEUR" for s in steps)
    if waiting_user:
        step_map = {s["id"]: s for s in steps}
        has_ready = any(
            s["status"] == "EN_ATTENTE"
            and (not s["depends_on"] or step_map.get(s["depends_on"], {}).get("status") == "TERMINEE")
            for s in steps
        )
        if not has_ready:
            return  # Plan suspendu — rien à lancer, on attend l'utilisateur

    # Démarrer les étapes prêtes
    for step in steps:
        if step["status"] != "EN_ATTENTE":
            continue
        
        # Vérifier dépendance
        if step["depends_on"]:
            dep = next((s for s in steps if s["id"] == step["depends_on"]), None)
            if not dep or dep["status"] != "TERMINEE":
                continue
        
        # Marquer EN_COURS MAINTENANT (évite double-lancement au prochain tick)
        db.execute("""
            UPDATE jarvis_plan_steps
            SET status = 'EN_COURS', updated_at = datetime('now')
            WHERE id = ? AND status = 'EN_ATTENTE'
        """, (step["id"],))
        db.commit()
        
        # Lancer la tâche en arrière-plan
        asyncio.create_task(_run_step(step["id"], plan["id"],
                                      plan["home_conversation_id"],
                                      plan["title"]))


# ── Exécution d'une étape ─────────────────────────────────────────────────────

async def _run_step(step_id: int, plan_id: int,
                    home_conv_id: int, plan_title: str) -> None:
    """Exécute une étape dans une sous-conversation dédiée."""
    db = get_connection()
    try:
        cursor = db.cursor()
        
        # Recharger l'étape (données fraîches)
        cursor.execute("""
            SELECT id, plan_id, step_order, agent, title, input_message, depends_on
            FROM jarvis_plan_steps WHERE id = ?
        """, (step_id,))
        step = dict(cursor.fetchone())
        
        # Recharger le plan
        cursor.execute("SELECT * FROM jarvis_plans WHERE id = ?", (plan_id,))
        plan = dict(cursor.fetchone())
        
        # Récupérer project_id de la conversation d'origine
        cursor.execute("SELECT project_id FROM conversations WHERE id = ?", (home_conv_id,))
        conv_row = cursor.fetchone()
        home_project_id = conv_row["project_id"] if conv_row else None
        
        # Notifier démarrage
        _inject_update(home_conv_id, step, "EN_COURS", None, db)
        
        # Créer sous-conversation dédiée
        cursor.execute("""
            INSERT INTO conversations (project_id, title, created_at, updated_at)
            VALUES (?, ?, datetime('now'), datetime('now'))
        """, (home_project_id, f"[Plan #{plan_id}] Ét.{step['step_order']} {step['agent']} — {step['title']}",))
        sub_conv_id = cursor.lastrowid
        db.execute("""
            UPDATE jarvis_plan_steps
            SET sub_conversation_id = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (sub_conv_id, step_id))
        db.commit()
        
        # Construire le message d'entrée (avec contexte étape précédente)
        input_msg = _build_input(step, db)
        
        # Appel direct à l'agent (bypass routeur)
        from backend.services.jarvis_service import dispatch_direct
        config = load_config()
        result_content, suggest_freeze = await dispatch_direct(
            agent=step["agent"],
            conversation_id=sub_conv_id,
            message=input_msg,
            db=db,
            config=config,
            project_id=home_project_id
        )
        
        # MENTOR : détecter si en dialogue ou livrable terminé
        mentor_done = suggest_freeze or (
            "[mission_prete]" in result_content.lower()
            or "[MISSION_PRETE]" in result_content
        )
        
        # MENTOR terminé → freeze_session pour persister le livrable
        if step["agent"] == "MENTOR" and mentor_done:
            cursor.execute("""
                SELECT instance_ref FROM messages
                WHERE conversation_id = ? AND role = 'assistant'
                ORDER BY created_at DESC LIMIT 1
            """, (sub_conv_id,))
            last_msg = cursor.fetchone()
            if last_msg and last_msg["instance_ref"]:
                try:
                    ref_raw = last_msg["instance_ref"]
                    ref = json.loads(ref_raw) if isinstance(ref_raw, str) else ref_raw
                    if ref and ref.get("type") == "reflexion" and ref.get("id"):
                        from backend.services import reflexion_service
                        await reflexion_service.freeze_session(ref["id"], db)
                        logger.info(f"[PLAN_EXECUTOR] freeze_session session {ref['id']} — étape {step_id}")
                except Exception as e:
                    logger.warning(f"[PLAN_EXECUTOR] freeze_session échoué étape {step_id}: {e}")
        
        if step["agent"] == "MENTOR" and not mentor_done:
            # MENTOR pose encore des questions → pause, notifier conv d'origine
            db.execute("""
                UPDATE jarvis_plan_steps
                SET status = 'EN_ATTENTE_UTILISATEUR', output_text = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (result_content, step_id))
            db.commit()
            
            question = _extract_mentor_question(result_content)
            pause_msg = (
                f"[JARVIS] ⏸️ MENTOR a besoin d'une précision "
                f"*(Étape {step['step_order']} — {step['title']})*:\n\n"
                f"{question}\n\n"
                f"*Réponds directement ici — je transmettrai à MENTOR.*"
            )
            _inject_msg(home_conv_id, pause_msg, db)
            return  # Pas de TERMINEE — jarvis_service reprend sur réponse utilisateur
        
        # Étape terminée (tous agents sauf MENTOR en dialogue)
        db.execute("""
            UPDATE jarvis_plan_steps
            SET status = 'TERMINEE', output_text = ?,
                completed_at = datetime('now'), updated_at = datetime('now')
            WHERE id = ?
        """, (result_content, step_id))
        db.commit()
        
        _inject_update(home_conv_id, {**step, "output_text": result_content},
                       "TERMINEE", None, db)
    
    except Exception as e:
        logger.error(f"[PLAN_EXECUTOR] Étape {step_id} échouée: {e}")
        db.execute("""
            UPDATE jarvis_plan_steps
            SET status = 'ECHEC', error_message = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (str(e)[:500], step_id))
        db.commit()
        
        _inject_update(home_conv_id,
                       {"step_order": "?", "agent": "?",
                        "title": "?", "error_message": str(e)},
                       "ECHEC", str(e), db)
    finally:
        db.close()


# ── Transfert de contexte ─────────────────────────────────────────────────────

def _build_input(step: dict, db) -> str:
    """Construit le message d'entrée avec contexte de l'étape dépendante."""
    base = step["input_message"]
    if not step["depends_on"]:
        return base
    
    cursor = db.cursor()
    cursor.execute("""
        SELECT title, output_text FROM jarvis_plan_steps WHERE id = ?
    """, (step["depends_on"],))
    dep = cursor.fetchone()
    
    if dep and dep["output_text"]:
        ctx = dep["output_text"][:1500]
        return (f"{base}\n\n---\n"
                f"Contexte issu de l'étape précédente ({dep['title']}) :\n{ctx}")
    return base


def _extract_mentor_question(content: str) -> str:
    """
    Extrait la partie affichable de la réponse MENTOR pour la conversation d'origine.
    Retire le préfixe [MENTOR] si présent, tronque à 500 chars.
    """
    text = content.strip()
    if text.lower().startswith("[mentor]"):
        nl = text.find("\n")
        text = text[nl:].strip() if nl != -1 else text[8:].strip()
    return text[:500]


def _inject_msg(conv_id: int, content: str, db) -> None:
    """Injecte un message libre dans une conversation."""
    try:
        db.execute("""
            INSERT INTO messages
            (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'JARVIS', NULL, datetime('now'))
        """, (conv_id, content))
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conv_id,)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"[PLAN_EXECUTOR] _inject_msg échoué: {e}")


# ── Notifications conversation d'origine ─────────────────────────────────────

def _inject_update(conv_id: int, step: dict, status: str,
                   error: str | None, db) -> None:
    icons = {"EN_COURS": "🔄", "TERMINEE": "✅", "ECHEC": "❌"}
    icon = icons.get(status, "•")
    
    if status == "EN_COURS":
        content = (f"[JARVIS] {icon} Étape {step['step_order']} démarrée — "
                   f"**{step['agent']}** : {step['title']}…")
    elif status == "TERMINEE":
        preview = (step.get("output_text") or "")[:300]
        ellipsis = "…" if len(preview) == 300 else ""
        content = (f"[JARVIS] {icon} Étape {step['step_order']} terminée — "
                   f"**{step['agent']}** : {step['title']}\n\n"
                   f"> {preview}{ellipsis}")
    else:  # ECHEC
        content = (f"[JARVIS] {icon} Étape {step['step_order']} échouée — "
                   f"**{step['agent']}** : {step['title']}\n\n"
                   f"Erreur : {error or 'inconnue'}")
    
    try:
        db.execute("""
            INSERT INTO messages
            (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'JARVIS', NULL, datetime('now'))
        """, (conv_id, content))
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conv_id,)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"[PLAN_EXECUTOR] _inject_update échoué: {e}")


# ── Finalisation ──────────────────────────────────────────────────────────────

def _finalize_plan(plan: dict, steps: list, db) -> None:
    db.execute("""
        UPDATE jarvis_plans
        SET status = 'TERMINE', updated_at = datetime('now')
        WHERE id = ?
    """, (plan["id"],))
    db.commit()
    
    # Construire le bilan avec extraits des livrables
    lines = [f"[JARVIS] 🎉 **Plan terminé : {plan['title']}**\n"]
    for s in steps:
        preview = (s.get("output_text") or "")[:200]
        ellipsis = "…" if preview and len(s.get("output_text", "")) > 200 else ""
        lines.append(f"- ✅ Étape {s['step_order']} ({s['agent']}) — {s['title']}")
        if preview:
            lines.append(f"  > {preview}{ellipsis}")
    lines.append("\n**Bilan :** Toutes les étapes ont été complétées. Teste manuellement les critères de réussite de chaque mission.")
    content = "\n".join(lines)
    
    try:
        db.execute("""
            INSERT INTO messages
            (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'JARVIS', NULL, datetime('now'))
        """, (plan["home_conversation_id"], content))
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (plan["home_conversation_id"],)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"[PLAN_EXECUTOR] _finalize_plan échoué: {e}")


def _fail_plan(plan: dict, steps: list, db) -> None:
    db.execute("""
        UPDATE jarvis_plans
        SET status = 'ECHEC', updated_at = datetime('now')
        WHERE id = ?
    """, (plan["id"],))
    db.execute("""
        UPDATE jarvis_plan_steps
        SET status = 'ANNULEE', updated_at = datetime('now')
        WHERE plan_id = ? AND status = 'EN_ATTENTE'
    """, (plan["id"],))
    db.commit()
    
    failed = [s for s in steps if s["status"] == "ECHEC"]
    names = ", ".join(f"Ét.{s['step_order']} {s['agent']}" for s in failed)
    content = (f"[JARVIS] ⚠️ **Plan bloqué : {plan['title']}**\n\n"
               f"Étape(s) échouée(s) : {names}\n\n"
               f"Relance via `POST /api/plans/{plan['id']}/retry`.")
    
    try:
        db.execute("""
            INSERT INTO messages
            (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'JARVIS', NULL, datetime('now'))
        """, (plan["home_conversation_id"], content))
        db.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (plan["home_conversation_id"],)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"[PLAN_EXECUTOR] _fail_plan échoué: {e}")
