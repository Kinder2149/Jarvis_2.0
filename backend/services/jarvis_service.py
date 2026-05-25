import json
import logging
from datetime import datetime
import httpx
from backend.database import load_config
from backend.services.model_router import get_model_id, call_model

logger = logging.getLogger("jarvis")

# Signaux indiquant un changement de sujet (skip routing si absent)
_CHANGEMENT_SUJET = [
    "maintenant", "autre chose", "différent", "stop", "j'ai fini",
    "autre sujet", "change de sujet", "parlons de", "oublie", "laisse tomber"
]

# Signaux de lancement FORGE depuis le chat (prioritaires sur le skip routing)
_FORGE_LAUNCH_SIGNALS = [
    "démarre forge", "demarre forge", "lance forge", "lancer forge",
    "démarrer forge", "démarrer le code", "lancer le code",
    "passe au code", "module code", "go forge", "start forge",
    "valide et forge", "ok forge",
    # Signaux de validation → lancement FORGE
    "je valide", "valide passe", "passe a la suite", "passe à la suite",
    "ok passe", "c'est bon lance", "lance le code", "exécute",
]

_MULTI_STEP_SIGNALS = [
    # Séquençage explicite
    "d'abord", "dans un premier temps", "premièrement",
    "étape 1", "plusieurs étapes", "étape par étape",
    "plan d'action", "roadmap", "en plusieurs",
    # Parallélisme
    "en même temps", "en parallèle", "simultanément",
    # Combinaisons multi-agents
    "puis code", "puis forge", "puis génère",
    "cadre puis", "analyse puis", "prospecte puis",
    "mentor puis forge", "réfléchis puis code",
    # Planning explicite
    "décompose", "plusieurs agents", "multi-missions",
    "organise les missions", "plan complet",
    # Langage naturel manquant (ajouts)
    "chaque agent", "tous les agents", "tester les agents",
    "chaque mission", "agent par agent", "un par un les agents",
    "mission par agent", "bilan final",
]


def _is_forge_launch(message: str) -> bool:
    msg_lower = message.lower().strip()
    return any(s in msg_lower for s in _FORGE_LAUNCH_SIGNALS)


def _is_multi_step_candidate(message: str) -> bool:
    """Filtre rapide (sans LLM) : True si le message semble multi-agents."""
    if len(message.strip()) < 25:
        return False
    msg = message.lower()
    return any(signal in msg for signal in _MULTI_STEP_SIGNALS)


# ─── Point d'entrée principal ────────────────────────────────────────────────

async def process_message(conversation_id: int, user_message: str, db, force_agent: str | None = None) -> dict:
    """
    Traite un message utilisateur dans une conversation JARVIS.
    Retourne la réponse complète avec routing_info.
    """
    config = load_config()
    cursor = db.cursor()
    
    # Charger les 10 derniers messages (ordre chronologique)
    cursor.execute("""
        SELECT role, content, agent, instance_ref
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at DESC LIMIT 10
    """, (conversation_id,))
    recent = list(reversed([dict(r) for r in cursor.fetchall()]))
    
    # Charger le projet associé à la conversation
    cursor.execute("SELECT project_id FROM conversations WHERE id = ?", (conversation_id,))
    conv_row = cursor.fetchone()
    project_id = conv_row["project_id"] if conv_row else None
    
    # Charger les agents actifs
    cursor.execute("SELECT * FROM agent_registry WHERE is_active = 1")
    agents = [dict(a) for a in cursor.fetchall()]
    
    # Déterminer l'agent actif depuis le dernier message assistant
    agent_actif = _get_agent_actif(recent)
    
    # Relai réponse utilisateur vers étape MENTOR en attente
    if not force_agent:
        waiting_step = _find_waiting_plan_step(conversation_id, cursor)
        if waiting_step:
            return await _handle_plan_step_reply(
                conversation_id, user_message, waiting_step, db, cursor, config
            )
    
    # Détection plan multi-étapes (avant routing normal)
    if not force_agent and _is_multi_step_candidate(user_message):
        plan_data = await _generate_plan(user_message, config, db)
        if plan_data:
            return await _handle_multi_step(
                conversation_id, user_message, plan_data,
                project_id, db, cursor
            )
    
    # Routing
    if force_agent and force_agent in ("JARVIS", "MENTOR", "FORGE", "SENTINELLE", "ATELIER", "MEDIA"):
        routing_result = {
            "agent": force_agent, "action": "switch" if force_agent != agent_actif else "continue",
            "confidence": 1.0, "clarification_needed": False,
            "clarification_question": None, "reason": "user_selection"
        }
    elif _should_skip_routing(user_message, agent_actif):
        routing_result = {
            "agent": agent_actif, "action": "continue",
            "confidence": 1.0, "clarification_needed": False,
            "clarification_question": None, "reason": "continuation"
        }
    else:
        historique_court = [
            {"role": m["role"], "content": m["content"][:500], "agent": m.get("agent")}
            for m in recent[-3:]
        ]
        routing_result = await _route(
            user_message, agent_actif, historique_court, agents, config, db
        )
    
    # Persister le message utilisateur
    cursor.execute("""
        INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'user', ?, 'JARVIS', NULL, datetime('now'))
    """, (conversation_id, user_message))
    db.commit()
    
    # Cas clarification
    if routing_result.get("clarification_needed"):
        question = routing_result["clarification_question"]
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
            VALUES (?, 'assistant', ?, 'JARVIS', NULL, datetime('now'))
        """, (conversation_id, question))
        db.commit()
        msg_id = cursor.lastrowid
        cursor.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        db.commit()
        return {
            "message_id": msg_id, "role": "assistant", "content": question,
            "agent": "JARVIS", "instance_ref": None, "suggest_freeze": False,
            "freeze_reason": None,
            "routing_info": {**routing_result, "clarification_asked": True}
        }
    
    # Résoudre l'instance_ref courante pour l'agent sélectionné
    current_instance_ref = _find_current_instance_ref(recent, routing_result["agent"])
    
    # Dispatcher
    response_content, agent_used, instance_ref, suggest_freeze, freeze_reason = await _dispatch(
        routing_result, user_message, conversation_id, project_id,
        current_instance_ref, db, config, cursor
    )
    
    # Persister la réponse
    instance_ref_json = json.dumps(instance_ref, ensure_ascii=False) if instance_ref else None
    cursor.execute("""
        INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'assistant', ?, ?, ?, datetime('now'))
    """, (conversation_id, response_content, agent_used, instance_ref_json))
    db.commit()
    msg_id = cursor.lastrowid
    cursor.execute(
        "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
        (conversation_id,)
    )
    db.commit()
    
    return {
        "message_id": msg_id,
        "role": "assistant",
        "content": response_content,
        "agent": agent_used,
        "instance_ref": instance_ref,
        "suggest_freeze": suggest_freeze,
        "freeze_reason": freeze_reason,
        "routing_info": {**routing_result, "clarification_asked": False}
    }


# ─── Routing ─────────────────────────────────────────────────────────────────

async def _route(message: str, agent_actif: str | None, historique: list,
                 agents: list, config: dict, db) -> dict:
    """Appel Gemini Flash pour router l'intention. Fallback heuristique si échec."""
    agents_desc = [
        {
            "name": a["name"],
            "description": a["description"],
            "routing_hints": json.loads(a["routing_hints"])
        }
        for a in agents
    ]
    
    prompt = f"""Tu es le routeur d'intention de JARVIS, un assistant IA multi-agents.

Agent actuellement actif : {agent_actif or "aucun"}

Historique récent (3 derniers échanges) :
{json.dumps(historique, ensure_ascii=False)}

Agents disponibles :
{json.dumps(agents_desc, ensure_ascii=False)}

Message de l'utilisateur : "{message}"

Réponds UNIQUEMENT en JSON valide, aucun texte autour :
{{"agent": "NOM_AGENT", "action": "continue|new_instance|direct", "confidence": 0.0, "clarification_needed": false, "clarification_question": null, "reason": "raison courte en français"}}

Règles strictes :
- "action": "continue" → le message prolonge l'échange avec l'agent actif
- "action": "new_instance" → un agent spécialiste doit être activé pour une nouvelle tâche
- "action": "direct" → JARVIS répond directement (question générale, salutation, aucun agent pertinent)
- "clarification_needed": true SEULEMENT si confidence < 0.70 ET plusieurs agents sont plausibles
- "agent" doit être exactement l'un des noms : {[a["name"] for a in agents]}
- "reason" : 5-10 mots en français
- PRIORITÉ ABSOLUE : si le message commence par "non", "erreur", "annule" ou signale clairement une correction ou un changement de sujet, NE PAS continuer avec l'agent actif — router vers l'agent pertinent pour la nouvelle demande ou JARVIS si aucun agent ne correspond"""
    
    try:
        model_id = get_model_id("routing", config)
        response = await call_model(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            api_keys=config["api_keys"],
            session_id=None,
            step_name="jarvis_routing",
            model_type="routing",
            db_conn=db,
            module_name="jarvis"
        )
        result = json.loads(response)
        valid_agents = [a["name"] for a in agents]
        if result.get("agent") not in valid_agents:
            raise ValueError(f"Agent inconnu retourné: {result.get('agent')}")
        return result
    except Exception as e:
        logger.warning(f"[JARVIS] Routing LLM échoué ({e}), fallback heuristique")
        return _route_heuristique(message, agents)


def _route_heuristique(message: str, agents: list) -> dict:
    """Routing local sans appel réseau. Utilisé si Gemini Flash est indisponible."""
    if len(message.strip()) < 20:
        return {
            "agent": "JARVIS", "action": "direct", "confidence": 1.0,
            "clarification_needed": False, "clarification_question": None,
            "reason": "message trop court pour router"
        }
    
    msg_lower = message.lower()
    scores = {}
    for agent in agents:
        if agent["name"] == "JARVIS":
            continue
        hints = json.loads(agent["routing_hints"])
        scores[agent["name"]] = sum(1 for h in hints if h in msg_lower)
    
    best = max(scores, key=scores.get) if scores else "JARVIS"
    if scores.get(best, 0) >= 2:
        return {
            "agent": best, "action": "new_instance", "confidence": 0.60,
            "clarification_needed": False, "clarification_question": None,
            "reason": f"heuristique locale → {best}"
        }
    
    return {
        "agent": "JARVIS", "action": "direct", "confidence": 1.0,
        "clarification_needed": False, "clarification_question": None,
        "reason": "aucun agent spécialiste identifié"
    }


# ─── Dispatch ────────────────────────────────────────────────────────────────

async def _dispatch(
    routing_result: dict,
    message: str,
    conversation_id: int,
    project_id: int | None,
    current_instance_ref: dict | None,
    db,
    config: dict,
    cursor
) -> tuple:
    """Retourne (content, agent_used, instance_ref, suggest_freeze, freeze_reason)."""
    agent = routing_result["agent"]
    reason = routing_result.get("reason", "")

    if agent == "JARVIS" or routing_result["action"] == "direct":
        content = await _jarvis_direct_response(message, conversation_id, db, config, cursor)
        return content, "JARVIS", None, False, None

    if agent == "MENTOR":
        from backend.services import mentor_handler
        from backend.services.model_router import get_model_id, call_model
        content, agent_used, instance_ref, suggest_freeze, freeze_reason = await mentor_handler.handle(
            conversation_id=conversation_id,
            project_id=project_id,
            message=message,
            current_instance_ref=current_instance_ref,
            db=db,
            config=config
        )
        
        # Reformulation JARVIS si MENTOR en dialogue (pas livrable final)
        if not suggest_freeze and agent_used == "MENTOR":
            try:
                reformulation_prompt = (
                    f"Tu es JARVIS. Reformule ce message de MENTOR en langage fonctionnel "
                    f"humain pour l'utilisateur non-développeur. Garde toutes les questions, "
                    f"raccourcis de rien, ajoute aucune information. Max 400 mots.\n\n"
                    f"Message MENTOR :\n{content}"
                )
                model_id = get_model_id("routing", config)
                reformulated = await call_model(
                    model_id=model_id,
                    messages=[{"role": "user", "content": reformulation_prompt}],
                    api_keys=config["api_keys"],
                    session_id=None,
                    step_name="jarvis_reformulation_mentor",
                    model_type="routing",
                    db_conn=db,
                    module_name="jarvis"
                )
                content = reformulated
            except Exception:
                pass  # En cas d'échec reformulation, garder le contenu MENTOR original
        
        return content, agent_used, instance_ref, suggest_freeze, freeze_reason

    if agent == "FORGE":
        from backend.services import forge_handler
        # Priorité : si un pipeline est WAITING_VALIDATION, l'utilisateur répond à la validation
        if current_instance_ref and current_instance_ref.get("type") == "pipeline":
            pipeline_cursor = cursor.connection.cursor() if hasattr(cursor, 'connection') else db.cursor()
            pipeline_cursor.execute(
                "SELECT status FROM sessions WHERE id = ?",
                (current_instance_ref["id"],)
            )
            sess_row = pipeline_cursor.fetchone()
            if sess_row and sess_row["status"] == "WAITING_VALIDATION":
                return await forge_handler.handle_chat_validation(
                    session_id=current_instance_ref["id"],
                    message=message,
                    conversation_id=conversation_id,
                    db=db
                )
        if _is_forge_launch(message):
            return await forge_handler.handle_launch_chat(
                conversation_id=conversation_id,
                project_id=project_id,
                db=db,
                config=config
            )
        return await forge_handler.handle_status_query(
            project_id=project_id,
            current_instance_ref=current_instance_ref,
            db=db
        )

    if agent == "SENTINELLE":
        from backend.services.sentinelle_handler import handle as sentinelle_handle
        return await sentinelle_handle(conversation_id, message, db)

    if agent == "ATELIER":
        from backend.services.atelier_handler import handle as atelier_handle
        return await atelier_handle(conversation_id, message, current_instance_ref, db, config)

    if agent == "MEDIA":
        from backend.services.media_handler import handle as media_handle
        return await media_handle(conversation_id, message, current_instance_ref, db, config)

    # Fallback pour agents inconnus
    content = (
        f"[{agent}] Je détecte que tu souhaites {reason}.\n\n"
        f"Cet agent n'est pas encore disponible. "
        f"Puis-je t'aider autrement en attendant ?"
    )
    return content, agent, None, False, None


_WEATHER_TRIGGERS = ["météo", "meteo", "température", "temperature", "temps qu'il fait", "fait-il froid", "fait-il chaud", "pluie", "ensoleillement"]
_NEWS_TRIGGERS = ["actualité", "actualite", "news", "information", "récent", "récente", "vient de", "annonce", "breaking", "dernière heure", "à la une"]
_OTHER_WEB_TRIGGERS = ["prix actuel", "cours actuel", "bourse", "cac 40", "inflation", "élection", "election", "résultat match", "score"]


async def _brave_search(query: str, api_key: str, label: str = "") -> str:
    """Appelle l'API Brave Search et retourne un bloc de résultats formaté."""
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": 5, "text_decorations": False, "search_lang": "fr", "country": "FR"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
        results = data.get("web", {}).get("results", [])
        if not results:
            return ""
        header = f"**Résultats web — {label} :**" if label else "**Résultats web :**"
        lines = [f"- {res.get('title', '')} : {res.get('description', '')} ({res.get('url', '')})" for res in results[:5]]
        return header + "\n" + "\n".join(lines)
    except Exception as e:
        logger.warning(f"[JARVIS] Brave Search échoué ({label}): {e}")
        return ""


async def _jarvis_direct_response(message: str, conversation_id: int,
                                   db, config: dict, cursor) -> str:
    """JARVIS répond directement via le modèle d'analyse (Sonnet)."""
    cursor.execute("""
        SELECT role, content FROM messages
        WHERE conversation_id = ? AND role IN ('user', 'assistant')
        ORDER BY created_at ASC
    """, (conversation_id,))
    history = [{"role": r["role"], "content": r["content"]} for r in cursor.fetchall()]

    # Enrichissement web si clé Brave disponible — appels ciblés par intention
    web_key = config.get("api_keys", {}).get("web_search_key", "")
    web_blocks = []
    if web_key:
        msg_lower = message.lower()
        # Météo : requête focalisée sur la ville mentionnée
        if any(t in msg_lower for t in _WEATHER_TRIGGERS):
            bloc = await _brave_search(message, web_key, label="Météo")
            if bloc:
                web_blocks.append(bloc)
        # Actualités : requête ciblée indépendante
        if any(t in msg_lower for t in _NEWS_TRIGGERS):
            bloc = await _brave_search("actualités France importantes aujourd'hui", web_key, label="Actualités")
            if bloc:
                web_blocks.append(bloc)
        # Autres sujets factuels temps réel
        if any(t in msg_lower for t in _OTHER_WEB_TRIGGERS):
            bloc = await _brave_search(message, web_key, label="Info")
            if bloc:
                web_blocks.append(bloc)
    web_context = "\n\n".join(web_blocks)

    # Injection du contexte utilisateur depuis app_config
    ctx = config.get("context", {})
    profil = ctx.get("profil_utilisateur", "").strip()
    global_ctx = ctx.get("global_context", "").strip()
    regles = ctx.get("regles_globales", "").strip()

    context_block = ""
    if profil:
        context_block += f"\n\n## Profil utilisateur\n{profil}"
    if global_ctx:
        context_block += f"\n\n## Contexte global\n{global_ctx}"
    if regles:
        context_block += f"\n\n## Règles\n{regles}"

    system_content = (
        "Tu es JARVIS, la seule interface entre l'utilisateur et les agents spécialistes "
        "(MENTOR pour le cadrage, FORGE pour le code, SENTINELLE pour les investissements, "
        "ATELIER pour les prospects commerciaux, MEDIA pour les images et vidéos). "
        "Les agents ne parlent jamais directement à l'utilisateur — tu es leur interprète. "
        "Quand un agent te retourne un résultat, tu le reformules en langage fonctionnel humain "
        "avant de le présenter : pas de jargon technique, pas de balises internes. "
        "Tu poses tes questions une par une — jamais plusieurs à la fois dans le même message. "
        "Tu ne codes jamais toi-même : tu délègues à FORGE (via MENTOR pour le cadrage). "
        "Tu es concis, direct, toujours en français."
        + context_block
        + "\n\nRÈGLE ABSOLUE : tu n'inventes JAMAIS de balises XML, tags d'orchestration, "
        "ni simulation de dispatch agents. Si une demande nécessite plusieurs agents, "
        "réponds : 'Cette demande nécessite plusieurs agents. Reformule-la en précisant "
        "les étapes (ex: d'abord MENTOR pour X, puis FORGE pour Y) et je créerai un plan automatiquement.'"
    )
    system = {"role": "system", "content": system_content}

    # Si enrichissement web : l'ajouter en contexte avant le message utilisateur
    user_content = message
    if web_context:
        user_content = f"{web_context}\n\n---\nQuestion : {message}"

    history.append({"role": "user", "content": user_content})
    messages_llm = [system] + history[-20:]

    model_id = get_model_id("analysis", config)
    return await call_model(
        model_id=model_id,
        messages=messages_llm,
        api_keys=config["api_keys"],
        session_id=None,
        step_name="jarvis_direct",
        model_type="analysis",
        db_conn=db,
        module_name="jarvis"
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_agent_actif(messages: list) -> str | None:
    """Retourne l'agent actif depuis le dernier message assistant.
    Cherche d'abord un agent explicite non-JARVIS, puis déduit via instance_ref.type pour les messages JARVIS."""
    _type_to_agent = {
        "pipeline": "FORGE",
        "reflexion": "MENTOR",
        "atelier_confirm": "ATELIER",
        "atelier_checkpoint": "ATELIER",
        "atelier_pipeline": "ATELIER",
        "atelier_done": "ATELIER",
        "atelier_collecting": "ATELIER",
        "media_confirm": "MEDIA",
        "media_running": "MEDIA",
    }
    for msg in reversed(messages):
        if msg.get("role") != "assistant":
            continue
        ag = msg.get("agent")
        if ag in (None, "SENTINELLE_ALERT"):
            continue
        if ag not in ("JARVIS", "SENTINELLE_ALERT"):
            return ag  # agent explicite non-JARVIS (compatibilité messages anciens)
        if ag == "JARVIS" and msg.get("instance_ref"):
            try:
                ref = msg["instance_ref"]
                ref_parsed = json.loads(ref) if isinstance(ref, str) else ref
                inferred = _type_to_agent.get(ref_parsed.get("type"))
                if inferred:
                    return inferred
            except Exception:
                pass
    return None


def _should_skip_routing(message: str, agent_actif: str | None) -> bool:
    """Skip le routeur LLM si l'agent actif est connu et que le message
    ne signale pas un changement de sujet. Économise un appel Gemini Flash."""
    if not agent_actif or agent_actif == "JARVIS":
        return False
    # Signal FORGE depuis MENTOR → forcer le routage
    if agent_actif == "MENTOR" and _is_forge_launch(message):
        return False
    msg_lower = message.lower().strip()
    return not any(signal in msg_lower for signal in _CHANGEMENT_SUJET)


def _find_current_instance_ref(messages: list, agent: str) -> dict | None:
    """Retourne l'instance_ref du dernier message lié à l'agent.
    Cherche dans les messages à agent explicite ET dans les messages JARVIS via instance_ref.type."""
    _agent_to_types = {
        "FORGE": ["pipeline"],
        "MENTOR": ["reflexion"],
        "ATELIER": ["atelier_confirm", "atelier_checkpoint", "atelier_pipeline", "atelier_done", "atelier_collecting"],
        "MEDIA": ["media_confirm", "media_running"],
    }
    valid_types = _agent_to_types.get(agent, [])
    for msg in reversed(messages):
        if not msg.get("instance_ref"):
            continue
        try:
            ref = msg["instance_ref"]
            ref_parsed = json.loads(ref) if isinstance(ref, str) else ref
        except Exception:
            continue
        if msg.get("agent") == agent:
            return ref_parsed
        if msg.get("agent") == "JARVIS" and ref_parsed.get("type") in valid_types:
            return ref_parsed
    return None


def check_sentinelle_alertes(conversation_id: int, db) -> str | None:
    """
    Vérifie s'il y a des alertes Sentinelle non lues à injecter.
    Retourne le contenu markdown du message d'alerte, ou None.
    """
    cursor = db.cursor()
    
    # Déjà injecté aujourd'hui dans cette conversation ?
    cursor.execute("""
        SELECT 1 FROM messages
        WHERE conversation_id = ? AND agent = 'SENTINELLE_ALERT'
          AND DATE(created_at) = DATE('now')
        LIMIT 1
    """, (conversation_id,))
    if cursor.fetchone():
        return None
    
    # Alertes non lues ?
    cursor.execute("""
        SELECT ticker, variation_pct, cours_actuel
        FROM sentinelle_alertes WHERE lu = 0
        ORDER BY created_at DESC LIMIT 5
    """)
    alertes = cursor.fetchall()
    if not alertes:
        return None
    
    # Marquer lues
    cursor.execute("UPDATE sentinelle_alertes SET lu = 1 WHERE lu = 0")
    db.commit()
    
    # Formater
    lignes = []
    for a in alertes:
        signe = "+" if a["variation_pct"] > 0 else ""
        cours = f" (cours : {a['cours_actuel']} $)" if a["cours_actuel"] else ""
        lignes.append(f"- **{a['ticker']}** : {signe}{a['variation_pct']:.1f}%{cours}")
    
    return (
        f"**🔔 SENTINELLE — {len(alertes)} alerte{'s' if len(alertes) > 1 else ''} en attente**\n"
        + "\n".join(lignes)
        + "\n\n→ [Ouvrir SENTINELLE](sentinelle.html) pour agir"
    )


# ─── Génération et gestion plans multi-étapes ────────────────────────────────

def _find_waiting_plan_step(conversation_id: int, cursor) -> dict | None:
    """
    Cherche une étape MENTOR EN_ATTENTE_UTILISATEUR pour cette conversation.
    Retourne le dict de l'étape ou None.
    """
    cursor.execute("""
        SELECT ps.id, ps.plan_id, ps.step_order, ps.agent, ps.title,
               ps.sub_conversation_id, ps.depends_on
        FROM jarvis_plan_steps ps
        JOIN jarvis_plans p ON ps.plan_id = p.id
        WHERE p.home_conversation_id = ?
          AND ps.status = 'EN_ATTENTE_UTILISATEUR'
          AND ps.agent = 'MENTOR'
        ORDER BY ps.id DESC LIMIT 1
    """, (conversation_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


async def _handle_plan_step_reply(
    conversation_id: int,
    user_message: str,
    waiting_step: dict,
    db,
    cursor,
    config: dict
) -> dict:
    """
    Relaie la réponse de l'utilisateur vers MENTOR dans sa sous-conversation.
    Si MENTOR produit [MISSION_PRETE] → marque étape TERMINEE, plan reprend.
    Sinon → MENTOR pose une autre question, reste EN_ATTENTE_UTILISATEUR.
    """
    # Persister le message user dans la conversation d'origine
    cursor.execute("""
        INSERT INTO messages
        (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'user', ?, 'JARVIS', NULL, datetime('now'))
    """, (conversation_id, user_message))
    db.commit()

    # Relayer vers la sous-conversation MENTOR
    sub_conv_id = waiting_step["sub_conversation_id"]
    result_content, suggest_freeze = await dispatch_direct(
        agent="MENTOR",
        conversation_id=sub_conv_id,
        message=user_message,
        db=db,
        config=config
    )

    step_id   = waiting_step["id"]
    step_num  = waiting_step["step_order"]
    step_title = waiting_step["title"]
    plan_id   = waiting_step["plan_id"]

    mentor_done = suggest_freeze or (
        "[mission_prete]" in result_content.lower()
        or "[MISSION_PRETE]" in result_content
    )

    if mentor_done:
        # MENTOR a terminé → marquer étape TERMINEE
        db.execute("""
            UPDATE jarvis_plan_steps
            SET status = 'TERMINEE', output_text = ?,
                completed_at = datetime('now'), updated_at = datetime('now')
            WHERE id = ?
        """, (result_content, step_id))
        db.commit()
        content = (
            f"[JARVIS] ✅ MENTOR a terminé *(Étape {step_num} — {step_title})*\n\n"
            f"Suite du plan en cours…"
        )
    else:
        # MENTOR pose encore une question → rester EN_ATTENTE_UTILISATEUR
        db.execute("""
            UPDATE jarvis_plan_steps
            SET output_text = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (result_content, step_id))
        db.commit()
        preview = result_content[:500]
        content = (
            f"[JARVIS] ⏸️ MENTOR *(Étape {step_num})* :\n\n"
            f"{preview}\n\n"
            f"*Réponds ici — je transmettrai à MENTOR.*"
        )

    # Persister la réponse dans la conversation d'origine
    cursor.execute("""
        INSERT INTO messages
        (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'assistant', ?, 'JARVIS', NULL, datetime('now'))
    """, (conversation_id, content))
    db.execute(
        "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
        (conversation_id,)
    )
    db.commit()
    msg_id = cursor.lastrowid

    return {
        "message_id": msg_id,
        "role": "assistant",
        "content": content,
        "agent": "JARVIS",
        "instance_ref": None,
        "suggest_freeze": False,
        "freeze_reason": None,
        "routing_info": {
            "agent": "JARVIS", "action": "direct", "confidence": 1.0,
            "clarification_needed": False, "clarification_question": None,
            "reason": f"relay MENTOR étape {step_num}",
            "clarification_asked": False
        }
    }


async def _generate_plan(message: str, config: dict, db) -> dict | None:
    """
    Appelle Gemini Flash pour générer un plan structuré.
    Retourne le dict du plan ou None si la demande est finalement mono-agent.
    """
    prompt = """Tu analyses une demande utilisateur pour JARVIS (assistant multi-agents).
Détermine si elle nécessite plusieurs agents distincts.

Agents disponibles :
- MENTOR : réflexion, cadrage, architecture, décision (single-shot, livrable direct)
- FORGE : exécution code (nécessite toujours MENTOR avant, depends_on_order obligatoire)
- SENTINELLE : portefeuille investissement, watchlist, alertes
- ATELIER : prospection commerciale (seulement si une URL de site est fournie)
- MEDIA : génération image ou vidéo
- JARVIS : synthèse finale ou rapport (jamais en 1re étape)

Règles générales :
- Si la demande ne nécessite qu'un seul agent → retourne {"multi_step": false}
- Maximum 5 étapes
- FORGE doit toujours avoir depends_on_order pointant vers MENTOR
- Les étapes sans lien de dépendance peuvent tourner en parallèle (depends_on_order: null)

Règles STRICTES par agent pour input_message :
- MENTOR : input_message DOIT commencer EXACTEMENT par "[PLAN_DIRECT] " (avec espace)
  suivi de la spec complète (contexte, objectif, fichiers si code, critères de succès).
  Exemple : "[PLAN_DIRECT] Cadre une mission pour ajouter une page de statistiques au
  dashboard. Fichiers concernés : dashboard.py, stats.html. Critère : graphiques mensuels."
- SENTINELLE : input_message DOIT être une question de consultation pure, jamais une action.
  Exemple : "Quel est le budget disponible ce mois ?" ou "Quelles sont les positions actuelles ?"
  NE PAS formuler comme : "effectue", "teste", "vérifie en simulant", "passe un ordre".
- ATELIER : N'inclure ATELIER que si le message de l'utilisateur contient explicitement une URL
  (https://...). Si pas d'URL → ne pas inclure ATELIER dans le plan.
  input_message DOIT contenir l'URL exacte du message original.
- MEDIA : input_message = description précise de l'image/vidéo à générer.
- JARVIS : input_message = "Synthétise les livrables des étapes précédentes en un rapport final."

Format de retour (JSON strict, aucun texte autour) :
{"multi_step": true, "plan_title": "...", "steps": [
  {"order": 1, "agent": "...", "title": "...",
   "input_message": "...", "depends_on_order": null},
  {"order": 2, "agent": "...", "title": "...",
   "input_message": "...", "depends_on_order": 1}
]}
OU si mono-agent :
{"multi_step": false}"""

    try:
        model_id = get_model_id("routing", config)
        response = await call_model(
            model_id=model_id,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            api_keys=config["api_keys"],
            session_id=None,
            step_name="jarvis_plan_generate",
            model_type="routing",
            db_conn=db,
            module_name="jarvis"
        )
        data = json.loads(response)
        if not data.get("multi_step"):
            return None
        steps = data.get("steps", [])
        if len(steps) < 2:
            return None
        return data
    except Exception as e:
        logger.warning(f"[JARVIS] _generate_plan échoué ({e}), fallback routing normal")
        return None


async def _handle_multi_step(
    conversation_id: int,
    user_message: str,
    plan_data: dict,
    project_id: int | None,
    db,
    cursor
) -> dict:
    """
    Crée le plan en DB, formate la plan card, persiste et retourne la réponse.
    """
    plan_title = plan_data["plan_title"]
    steps = plan_data["steps"]

    # Persister le message utilisateur
    cursor.execute("""
        INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'user', ?, 'JARVIS', NULL, datetime('now'))
    """, (conversation_id, user_message))
    db.commit()

    # Créer le plan en DB
    cursor.execute("""
        INSERT INTO jarvis_plans (home_conversation_id, title, status)
        VALUES (?, ?, 'EN_ATTENTE_CONFIRM')
    """, (conversation_id, plan_title))
    plan_id = cursor.lastrowid

    order_to_step_id: dict[int, int] = {}
    for step in steps:
        dep_id = order_to_step_id.get(step.get("depends_on_order")) \
                 if step.get("depends_on_order") else None
        cursor.execute("""
            INSERT INTO jarvis_plan_steps
            (plan_id, step_order, agent, title, input_message, depends_on)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (plan_id, step["order"], step["agent"],
              step["title"], step["input_message"], dep_id))
        order_to_step_id[step["order"]] = cursor.lastrowid
    db.commit()

    # Construire la plan card (markdown)
    agent_icons = {
        "MENTOR": "🧠", "FORGE": "⚙️", "SENTINELLE": "🛡️",
        "ATELIER": "💼", "MEDIA": "🎨", "JARVIS": "📝"
    }
    lines = [f"[JARVIS] J'ai décomposé ta demande en **{len(steps)} étapes** :\n"]
    lines.append(f"📋 **{plan_title}**\n")
    for s in steps:
        icon = agent_icons.get(s["agent"], "•")
        dep = f" *(↳ Ét.{s['depends_on_order']})*" if s.get("depends_on_order") else ""
        lines.append(f"- Étape {s['order']} · {icon} **{s['agent']}** — {s['title']}{dep}")
    lines.append("\nConfirme pour lancer l'exécution automatique.")
    content = "\n".join(lines)

    # instance_ref portant le plan_id pour les boutons frontend
    instance_ref = {"type": "plan_confirm", "plan_id": plan_id}
    instance_ref_json = json.dumps(instance_ref, ensure_ascii=False)

    # Persister la réponse assistant
    cursor.execute("""
        INSERT INTO messages (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'assistant', ?, 'JARVIS', ?, datetime('now'))
    """, (conversation_id, content, instance_ref_json))
    db.commit()
    msg_id = cursor.lastrowid
    cursor.execute(
        "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
        (conversation_id,)
    )
    db.commit()

    return {
        "message_id": msg_id,
        "role": "assistant",
        "content": content,
        "agent": "JARVIS",
        "instance_ref": instance_ref,
        "suggest_freeze": False,
        "freeze_reason": None,
        "routing_info": {
            "agent": "JARVIS", "action": "direct", "confidence": 1.0,
            "clarification_needed": False, "clarification_question": None,
            "reason": f"plan multi-étapes généré ({len(steps)} étapes)",
            "clarification_asked": False
        }
    }


# ─── Dispatch direct (Plan Executor) ─────────────────────────────────────────

async def dispatch_direct(
    agent: str,
    conversation_id: int,
    message: str,
    db,
    config: dict,
    project_id: int | None = None
) -> tuple[str, bool]:
    """
    Envoie un message directement à un agent sans passer par le routeur LLM.
    Utilisé par plan_executor pour exécuter les étapes d'un plan.
    Retourne (response_content, suggest_freeze).
    """
    cursor = db.cursor()

    # Persister le message utilisateur dans la sous-conversation
    cursor.execute("""
        INSERT INTO messages
        (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'user', ?, 'JARVIS', NULL, datetime('now'))
    """, (conversation_id, message))
    db.commit()

    # Routing synthétique — agent déjà connu
    routing_result = {
        "agent": agent,
        "action": "new_instance",
        "confidence": 1.0,
        "clarification_needed": False,
        "clarification_question": None,
        "reason": "dispatch_direct — plan executor"
    }

    # Pas d'instance_ref précédente (étape fraîche)
    current_instance_ref = None

    # Appel au dispatcher existant
    response_content, agent_used, instance_ref, suggest_freeze, freeze_reason = \
        await _dispatch(routing_result, message, conversation_id, project_id,
                        current_instance_ref, db, config, cursor)

    # Persister la réponse dans la sous-conversation
    import json as _json
    instance_ref_json = _json.dumps(instance_ref, ensure_ascii=False) \
                        if instance_ref else None
    cursor.execute("""
        INSERT INTO messages
        (conversation_id, role, content, agent, instance_ref, created_at)
        VALUES (?, 'assistant', ?, ?, ?, datetime('now'))
    """, (conversation_id, response_content, agent_used, instance_ref_json))
    db.execute(
        "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
        (conversation_id,)
    )
    db.commit()

    return response_content, suggest_freeze
