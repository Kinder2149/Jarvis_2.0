import sqlite3
from pathlib import Path
from datetime import datetime
import difflib
import json
import asyncio
import re
from typing import Optional, List, Dict

from backend.schemas.reflexion import (
    LivrableType,
    ReflexionStatut,
    MessageRole,
    ReflexionMessage
)
from backend.services.cadrage import check_cadrage_health
from backend.services import model_router
from backend.services.context_manager import write_cloture_docs


def _get_reflexion_model() -> str:
    """Lit le modèle configuré pour la réflexion depuis config.json (analysis).
    Fallback : anthropic/claude-sonnet-4.5"""
    from backend.database import load_config
    try:
        config = load_config()
        model_id = config.get("model_preferences", {}).get("analysis", "")
        return model_id if model_id else "anthropic/claude-sonnet-4.5"
    except Exception:
        return "anthropic/claude-sonnet-4.5"


def _get_methodo_path(db: sqlite3.Connection) -> Path | None:
    """Lit le chemin METHODO depuis config.json (chat.methodo_path).
    Fallback : backend/data/methodo/ si non configuré.
    Retourne None si aucun chemin valide."""
    import logging
    logger = logging.getLogger("jarvis")
    
    from backend.database import load_config
    
    try:
        config = load_config()
        methodo_path_str = config.get("chat", {}).get("methodo_path", "")
        
        # Chemin externe configuré
        if methodo_path_str:
            external_path = Path(methodo_path_str)
            if external_path.exists():
                logger.info(f"📂 [METHODO] Utilisation chemin externe: {external_path}")
                return external_path
            else:
                logger.warning(f"⚠️ [METHODO] Chemin configuré inexistant: {external_path}")
    except Exception as e:
        logger.warning(f"⚠️ [METHODO] Erreur lecture config: {e}")
    
    # Fallback : copie interne
    fallback = Path(__file__).parent.parent / "data" / "methodo"
    if fallback.exists():
        logger.warning(f"⚠️ [METHODO] Utilisation fallback interne: {fallback}")
        return fallback
    
    logger.error("❌ [METHODO] Aucun chemin METHODO valide trouvé")
    return None


# Whitelist fichiers .md éditables
WRITABLE_MD_FILES = {
    "PROJET_CONTEXTE.md",
    "CHANGELOG.md",
    "README.md",
    "STACK_CODE.md",
}

# Slugs modèles valides
VALID_MODEL_SLUGS = {
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5",
    "anthropic/claude-opus-4",
    "google/gemini-2.5-flash",
    "google/gemini-flash-1.5",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
}


def create_session(
    project_id: int,
    livrable_type: LivrableType,
    db_conn: sqlite3.Connection
) -> int:
    """Crée une nouvelle session de réflexion."""
    cursor = db_conn.cursor()
    
    # Vérifier que le projet existe
    cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
    if not cursor.fetchone():
        raise ValueError(f"Projet {project_id} introuvable")
    
    # Lire le modèle depuis config.json (model_preferences.analysis)
    modele_utilise = _get_reflexion_model()
    
    cursor.execute("""
        INSERT INTO reflexion_sessions (
            project_id, livrable_type, statut, modele_utilise,
            input_tokens_total, output_tokens_total,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, 0, 0, ?, ?)
    """, (
        project_id,
        livrable_type.value,
        ReflexionStatut.OUVERTE.value,
        modele_utilise,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    db_conn.commit()
    return cursor.lastrowid


def get_session(session_id: int, db_conn: sqlite3.Connection) -> Optional[dict]:
    """Récupère une session par ID."""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT id, project_id, livrable_type, titre, statut, modele_utilise,
               input_tokens_total, output_tokens_total, livrable_id,
               created_at, updated_at, frozen_at
        FROM reflexion_sessions
        WHERE id = ?
    """, (session_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return dict(row)


def get_sessions_by_project(project_id: int, db_conn: sqlite3.Connection) -> List[dict]:
    """Récupère toutes les sessions d'un projet."""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT id, project_id, livrable_type, titre, statut, modele_utilise,
               input_tokens_total, output_tokens_total, livrable_id,
               created_at, updated_at, frozen_at
        FROM reflexion_sessions
        WHERE project_id = ?
        ORDER BY created_at DESC
    """, (project_id,))
    
    return [dict(row) for row in cursor.fetchall()]


def delete_session(session_id: int, db_conn: sqlite3.Connection) -> None:
    """
    Supprime une session.
    Autorisé uniquement si statut OUVERTE ou ABANDONNEE.
    """
    cursor = db_conn.cursor()
    
    # Vérifier statut
    cursor.execute("SELECT statut FROM reflexion_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Session {session_id} introuvable")
    
    statut = row["statut"]
    if statut not in [ReflexionStatut.OUVERTE.value, ReflexionStatut.ABANDONNEE.value]:
        raise ValueError(f"Impossible de supprimer une session {statut}")
    
    cursor.execute("DELETE FROM reflexion_sessions WHERE id = ?", (session_id,))
    db_conn.commit()


def abandon_session(session_id: int, db_conn: sqlite3.Connection) -> None:
    """Passe une session en statut ABANDONNEE."""
    cursor = db_conn.cursor()
    
    # Vérifier que la session existe et n'est pas FIGEE
    cursor.execute("SELECT statut FROM reflexion_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Session {session_id} introuvable")
    
    if row["statut"] == ReflexionStatut.FIGEE.value:
        raise ValueError("Impossible d'abandonner une session figée")
    
    cursor.execute("""
        UPDATE reflexion_sessions
        SET statut = ?, updated_at = ?
        WHERE id = ?
    """, (ReflexionStatut.ABANDONNEE.value, datetime.now().isoformat(), session_id))
    
    db_conn.commit()


def add_message(
    session_id: int,
    role: str,
    content: str,
    db_conn: sqlite3.Connection,
    attachments: Optional[str] = None
) -> int:
    """Ajoute un message à une session."""
    cursor = db_conn.cursor()
    
    # Vérifier que la session existe et est OUVERTE
    cursor.execute("SELECT statut FROM reflexion_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Session {session_id} introuvable")
    
    if row["statut"] != ReflexionStatut.OUVERTE.value:
        raise ValueError(f"Session {session_id} n'est pas ouverte (statut: {row['statut']})")
    
    cursor.execute("""
        INSERT INTO reflexion_messages (
            session_id, role, content, attachments, compacted, created_at
        ) VALUES (?, ?, ?, ?, 0, ?)
    """, (session_id, role, content, attachments, datetime.now().isoformat()))
    
    # Mettre à jour updated_at de la session
    cursor.execute("""
        UPDATE reflexion_sessions
        SET updated_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), session_id))
    
    db_conn.commit()
    return cursor.lastrowid


def get_messages(
    session_id: int,
    db_conn: sqlite3.Connection,
    include_compacted: bool = False
) -> List[dict]:
    """Récupère les messages d'une session."""
    cursor = db_conn.cursor()
    
    if include_compacted:
        cursor.execute("""
            SELECT id, session_id, role, content, attachments, compacted, created_at
            FROM reflexion_messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        """, (session_id,))
    else:
        cursor.execute("""
            SELECT id, session_id, role, content, attachments, compacted, created_at
            FROM reflexion_messages
            WHERE session_id = ? AND compacted = 0
            ORDER BY created_at ASC
        """, (session_id,))
    
    return [dict(row) for row in cursor.fetchall()]


def build_system_prompt(session: dict, project_path: Path, db_conn: sqlite3.Connection) -> str:
    """
    Construit le system prompt pour une session de réflexion.
    Assemble : profil utilisateur + règles globales + PROJET_CONTEXTE + graphify + prompt spécifique au livrable.
    """
    cursor = db_conn.cursor()
    
    # Lire profil utilisateur et règles globales depuis METHODO
    profil_utilisateur = ""
    regles_globales = ""
    
    methodo_path = _get_methodo_path(db_conn)
    if methodo_path:
        profil_path = methodo_path / "PROFIL_UTILISATEUR.md"
        if profil_path.exists():
            profil_utilisateur = profil_path.read_text(encoding="utf-8")
        
        regles_path = methodo_path / "REGLES_GLOBALES.md"
        if regles_path.exists():
            regles_globales = regles_path.read_text(encoding="utf-8")
    
    # Lire PROJET_CONTEXTE.md
    projet_contexte = ""
    projet_contexte_path = project_path / "PROJET_CONTEXTE.md"
    if projet_contexte_path.exists():
        projet_contexte = projet_contexte_path.read_text(encoding="utf-8")
    
    # Lire GRAPH_REPORT.md
    graphify_report = ""
    graph_path = project_path / "graphify-out" / "GRAPH_REPORT.md"
    if graph_path.exists():
        graphify_report = graph_path.read_text(encoding="utf-8")
    
    # Charger le prompt spécifique au livrable depuis prompts.json
    cursor.execute("SELECT value FROM app_config WHERE key = 'prompts_json_path'")
    row = cursor.fetchone()
    default_prompts_path = Path(__file__).parent.parent / "data" / "prompts.json"
    prompts_path = Path(row["value"]) if row and row["value"] else default_prompts_path
    
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    livrable_type = session["livrable_type"]
    prompt_key = f"reflexion_{livrable_type}"
    prompt_template = prompts.get(prompt_key, "")
    
    # Remplacer les variables
    system_prompt = prompt_template.replace("{{profil_utilisateur}}", profil_utilisateur)
    system_prompt = system_prompt.replace("{{regles_globales}}", regles_globales)
    system_prompt = system_prompt.replace("{{projet_contexte}}", projet_contexte)
    system_prompt = system_prompt.replace("{{graphify_report}}", graphify_report)
    
    return system_prompt


async def send_user_message(
    session_id: int,
    content: str,
    db_conn: sqlite3.Connection
) -> List[dict]:
    """
    Envoie un message utilisateur et appelle Claude Sonnet 4.5 pour obtenir une réponse.
    Retourne la liste complète des messages mise à jour.
    """
    cursor = db_conn.cursor()
    
    # Ajouter message user
    add_message(session_id, MessageRole.USER.value, content, db_conn)
    
    # Récupérer la session
    session = get_session(session_id, db_conn)
    if not session:
        raise ValueError(f"Session {session_id} introuvable")
    
    # Générer titre auto si premier message
    if not session["titre"]:
        titre = content[:50] + ("..." if len(content) > 50 else "")
        cursor.execute("""
            UPDATE reflexion_sessions
            SET titre = ?, updated_at = ?
            WHERE id = ?
        """, (titre, datetime.now().isoformat(), session_id))
        db_conn.commit()
    
    # Récupérer project_path
    cursor.execute("SELECT path FROM projects WHERE id = ?", (session["project_id"],))
    project_row = cursor.fetchone()
    if not project_row:
        raise ValueError(f"Projet {session['project_id']} introuvable")
    project_path = Path(project_row["path"])
    
    # Construire le system prompt
    try:
        system_prompt = build_system_prompt(session, project_path, db_conn)
    except Exception as e:
        raise ValueError(f"Erreur construction du prompt système : {e}")
    
    # Récupérer l'historique des messages (non compactés)
    messages_history = get_messages(session_id, db_conn, include_compacted=False)
    
    # Construire la liste de messages pour l'API
    api_messages = []
    for msg in messages_history:
        if msg["role"] in ["user", "assistant"]:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Récupérer les clés API
    cursor.execute("SELECT key, value FROM app_config WHERE key IN ('openrouter_key', 'anthropic_key')")
    api_keys = {row["key"]: row["value"] for row in cursor.fetchall()}
    
    # Appeler le modèle
    try:
        response_content = await model_router.call_model(
            model_id=_get_reflexion_model(),
            messages=[{"role": "system", "content": system_prompt}] + api_messages,
            api_keys=api_keys,
            session_id=session_id,
            step_name="reflexion_conversation",
            model_type="analysis",
            db_conn=db_conn
        )
        
        # Récupérer les tokens de l'appel (dernière entrée model_decision_log)
        cursor.execute("""
            SELECT input_tokens, output_tokens
            FROM model_decision_log
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (session_id,))
        log_row = cursor.fetchone()
        if log_row:
            input_tokens = log_row["input_tokens"]
            output_tokens = log_row["output_tokens"]
            
            # Mettre à jour les totaux de la session
            cursor.execute("""
                UPDATE reflexion_sessions
                SET input_tokens_total = input_tokens_total + ?,
                    output_tokens_total = output_tokens_total + ?,
                    updated_at = ?
                WHERE id = ?
            """, (input_tokens, output_tokens, datetime.now().isoformat(), session_id))
            db_conn.commit()
        
        # Ajouter message assistant
        add_message(session_id, MessageRole.ASSISTANT.value, response_content, db_conn)
        
    except Exception as e:
        # En cas d'erreur LLM, ajouter un message système d'erreur
        error_message = f"Erreur lors de l'appel au modèle : {str(e)}"
        add_message(session_id, MessageRole.SYSTEM.value, error_message, db_conn)
    
    return get_messages(session_id, db_conn, include_compacted=False)


def recommend_model(files_targeted: List[str], project_path: Path) -> str:
    """
    Recommande un modèle selon l'heuristique définie dans la spec.
    """
    # Calculer la taille totale des fichiers cibles
    total_size = 0
    for file_rel in files_targeted:
        file_path = project_path / file_rel
        if file_path.exists():
            total_size += file_path.stat().st_size
    
    total_size_kb = total_size / 1024
    
    # Heuristique
    if len(files_targeted) <= 2 and total_size_kb <= 80:
        return "anthropic/claude-haiku-4.5"
    elif len(files_targeted) > 2 or total_size_kb > 80:
        return "google/gemini-2.5-pro"
    else:
        return "anthropic/claude-haiku-4.5"


async def freeze_session(session_id: int, db_conn: sqlite3.Connection) -> dict:
    """
    Fige une session de réflexion : génère le livrable final via un appel LLM spécial.
    Retourne le livrable créé.
    """
    cursor = db_conn.cursor()
    
    # Récupérer la session
    session = get_session(session_id, db_conn)
    if not session:
        raise ValueError(f"Session {session_id} introuvable")
    
    if session["statut"] != ReflexionStatut.OUVERTE.value:
        raise ValueError(f"Session {session_id} n'est pas ouverte (statut: {session['statut']})")
    
    # Passer en EN_FIGEMENT
    cursor.execute("""
        UPDATE reflexion_sessions
        SET statut = ?, updated_at = ?
        WHERE id = ?
    """, (ReflexionStatut.EN_FIGEMENT.value, datetime.now().isoformat(), session_id))
    db_conn.commit()
    
    try:
        # Récupérer project_path
        cursor.execute("SELECT path FROM projects WHERE id = ?", (session["project_id"],))
        project_row = cursor.fetchone()
        if not project_row:
            raise ValueError(f"Projet {session['project_id']} introuvable")
        project_path = Path(project_row["path"])
        
        # Lire profil utilisateur et règles globales depuis METHODO
        profil_utilisateur = ""
        regles_globales = ""
        
        methodo_path = _get_methodo_path(db_conn)
        if methodo_path:
            profil_path = methodo_path / "PROFIL_UTILISATEUR.md"
            if profil_path.exists():
                profil_utilisateur = profil_path.read_text(encoding="utf-8")
            
            regles_path = methodo_path / "REGLES_GLOBALES.md"
            if regles_path.exists():
                regles_globales = regles_path.read_text(encoding="utf-8")
        
        # Lire PROJET_CONTEXTE.md
        projet_contexte = ""
        projet_contexte_path = project_path / "PROJET_CONTEXTE.md"
        if projet_contexte_path.exists():
            projet_contexte = projet_contexte_path.read_text(encoding="utf-8")
        
        # Lire GRAPH_REPORT.md
        graphify_report = ""
        graph_path = project_path / "graphify-out" / "GRAPH_REPORT.md"
        if graph_path.exists():
            graphify_report = graph_path.read_text(encoding="utf-8")
        
        # Récupérer l'historique de conversation
        messages_history = get_messages(session_id, db_conn, include_compacted=False)
        conversation_history = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages_history
            if msg["role"] in ["user", "assistant"]
        ])
        
        # Charger le prompt de figement depuis prompts.json
        cursor.execute("SELECT value FROM app_config WHERE key = 'prompts_json_path'")
        row = cursor.fetchone()
        prompts_path = Path(row["value"]) if row and row["value"] else Path("backend/data/prompts.json")
        
        with open(prompts_path, "r", encoding="utf-8") as f:
            prompts = json.load(f)
        
        livrable_type = session["livrable_type"]
        prompt_key = f"reflexion_figement_{livrable_type}"
        prompt_template = prompts.get(prompt_key, "")
        
        # Remplacer les variables
        figement_prompt = prompt_template.replace("{{profil_utilisateur}}", profil_utilisateur)
        figement_prompt = figement_prompt.replace("{{regles_globales}}", regles_globales)
        figement_prompt = figement_prompt.replace("{{conversation_history}}", conversation_history)
        figement_prompt = figement_prompt.replace("{{projet_contexte}}", projet_contexte)
        figement_prompt = figement_prompt.replace("{{graphify_report}}", graphify_report)
        figement_prompt = figement_prompt.replace("{{session_id}}", str(session_id))
        figement_prompt = figement_prompt.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
        
        # Récupérer les clés API
        cursor.execute("SELECT key, value FROM app_config WHERE key IN ('openrouter_key', 'anthropic_key')")
        api_keys = {row["key"]: row["value"] for row in cursor.fetchall()}
        
        # Appeler le modèle pour générer le livrable
        livrable_content = await model_router.call_model(
            model_id=_get_reflexion_model(),
            messages=[{"role": "user", "content": figement_prompt}],
            api_keys=api_keys,
            session_id=session_id,
            step_name="reflexion_figement",
            model_type="analysis",
            db_conn=db_conn
        )
        
        # Parser le livrable pour extraire files_targeted et recommandation_modele
        files_targeted = []
        recommandation_modele = ""
        
        if livrable_type == "mission_code" or livrable_type == "plan_multi_missions":
            # Extraire les fichiers concernés (lignes commençant par - ` ou - chemin/)
            file_pattern = re.compile(r'^\s*-\s*`?([^`\s]+\.[a-z]+)`?', re.MULTILINE)
            files_targeted = file_pattern.findall(livrable_content)
            
            # Extraire la recommandation modèle (chercher dans la section dédiée)
            model_pattern = re.compile(r'Recommandation\s+mod[eè]le[^\n]*\n+`([^`]+)`', re.MULTILINE | re.IGNORECASE)
            model_match = model_pattern.search(livrable_content)
            if model_match:
                extracted = model_match.group(1).strip()
                if extracted in VALID_MODEL_SLUGS:
                    recommandation_modele = extracted
                else:
                    import logging as _log
                    _log.getLogger("jarvis").warning(
                        f"freeze_session: slug modèle extrait invalide '{extracted}' — fallback heuristique"
                    )
                    recommandation_modele = recommend_model(files_targeted, project_path)
            else:
                recommandation_modele = recommend_model(files_targeted, project_path)
        
        # Créer le mission_prompts
        cursor.execute("""
            INSERT INTO mission_prompts (
                reflexion_session_id, livrable_type, content,
                recommandation_modele, files_targeted, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            livrable_type,
            livrable_content,
            recommandation_modele or None,
            json.dumps(files_targeted) if files_targeted else None,
            datetime.now().isoformat()
        ))
        livrable_id = cursor.lastrowid
        
        # Mettre à jour la session
        cursor.execute("""
            UPDATE reflexion_sessions
            SET statut = ?, livrable_id = ?, frozen_at = ?, updated_at = ?
            WHERE id = ?
        """, (
            ReflexionStatut.FIGEE.value,
            livrable_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            session_id
        ))
        db_conn.commit()
        
        # Écriture immédiate PROJET_CONTEXTE section 8 + CHANGELOG (cadrage)
        fichiers_modifies = []
        if livrable_type in ("mission_code", "plan_multi_missions"):
            titre_mission = (session.get("titre") or "Mission").strip()
            section_8 = (
                f"**Statut :** 🔒 Mission cadrée — en attente d'exécution\n"
                f"**Titre :** {titre_mission}\n"
                f"**Type de livrable :** {livrable_type}\n"
                f"**Modèle recommandé :** {recommandation_modele or 'n/a'}\n"
                f"**Fichiers ciblés :** {', '.join(files_targeted) if files_targeted else 'à définir'}\n"
                f"**Cadrage figé le :** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"**Source :** session de réflexion #{session_id}"
            )
            changelog_line = (
                f"- {datetime.now().strftime('%Y-%m-%d')} : "
                f"CADRAGE — {titre_mission} (réflexion #{session_id}, "
                f"livrable {livrable_type}) — en attente d'exécution"
            )
            try:
                write_cloture_docs(
                    {"section_8": section_8, "changelog_line": changelog_line},
                    str(project_path)
                )
                fichiers_modifies = ["PROJET_CONTEXTE.md", "CHANGELOG.md"]
            except Exception as e:
                import logging
                logging.getLogger("jarvis").warning(
                    f"freeze_session: écriture cadrage docs échouée: {e}"
                )
        
        if livrable_type == "decision_figee":
            if projet_contexte_path.exists():
                current_content = projet_contexte_path.read_text(encoding="utf-8")

                section_6_pattern = re.compile(r'(## 6\. DÉCISIONS FIGÉES.*?)(\n## 7\.)', re.DOTALL)
                match = section_6_pattern.search(current_content)

                if match:
                    section_6_content = match.group(1)
                    new_content = current_content.replace(
                        match.group(0),
                        section_6_content + "\n" + livrable_content + "\n" + match.group(2)
                    )
                    projet_contexte_path.write_text(new_content, encoding="utf-8")
                    fichiers_modifies = ["PROJET_CONTEXTE.md"]
        
        # Retourner le livrable
        cursor.execute("""
            SELECT id, reflexion_session_id, livrable_type, content,
                   recommandation_modele, files_targeted, created_at, consumed_at
            FROM mission_prompts
            WHERE id = ?
        """, (livrable_id,))
        livrable = dict(cursor.fetchone())
        
        livrable["fichiers_modifies"] = fichiers_modifies
        return livrable
        
    except Exception as e:
        # En cas d'erreur, repasser en OUVERTE avec message système
        cursor.execute("""
            UPDATE reflexion_sessions
            SET statut = ?, updated_at = ?
            WHERE id = ?
        """, (ReflexionStatut.OUVERTE.value, datetime.now().isoformat(), session_id))
        db_conn.commit()
        
        error_message = f"Erreur lors du figement : {str(e)}"
        add_message(session_id, MessageRole.SYSTEM.value, error_message, db_conn)
        
        raise


def get_livrable(session_id: int, db_conn: sqlite3.Connection) -> Optional[dict]:
    """
    Récupère le livrable (mission_prompts) associé à une session figée.
    """
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT mp.id, mp.reflexion_session_id, mp.livrable_type, mp.content,
               mp.recommandation_modele, mp.files_targeted, mp.created_at, mp.consumed_at
        FROM mission_prompts mp
        JOIN reflexion_sessions rs ON rs.livrable_id = mp.id
        WHERE rs.id = ?
    """, (session_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return dict(row)


def mark_consumed(mission_prompt_id: int, db_conn: sqlite3.Connection) -> None:
    """
    Marque un mission_prompts comme consommé (copié dans le Module Code).
    """
    cursor = db_conn.cursor()
    
    cursor.execute("""
        UPDATE mission_prompts
        SET consumed_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), mission_prompt_id))
    
    db_conn.commit()


def is_file_writable(file_path: str, project_path: Path) -> bool:
    """
    Vérifie si un fichier est dans la whitelist d'écriture.
    
    Autorisé :
    - PROJET_CONTEXTE.md, CHANGELOG.md, README.md, STACK_CODE.md (racine projet)
    
    Interdit :
    - Sortie hors projet (..)
    - Fichiers non-.md
    - Fichiers code (.py, .js, .json, etc.)
    """
    try:
        # Normaliser le chemin
        full_path = (project_path / file_path).resolve()
        
        # Vérifier que le fichier est .md
        if not full_path.suffix == ".md":
            return False
        
        # Vérifier que le fichier est dans le projet
        try:
            full_path.relative_to(project_path.resolve())
        except ValueError:
            return False
        
        # Vérifier si dans la whitelist racine
        if full_path.name in WRITABLE_MD_FILES and full_path.parent == project_path:
            return True
        
        return False
    
    except Exception:
        return False


def propose_edit(
    session_id: int,
    file_path: str,
    new_content: str,
    db_conn: sqlite3.Connection
) -> dict:
    """
    Calcule le diff pour une édition proposée.
    Retourne le diff + metadata.
    """
    cursor = db_conn.cursor()
    
    # Récupérer project_id
    cursor.execute("SELECT project_id FROM reflexion_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Session {session_id} introuvable")
    
    project_id = row["project_id"]
    
    # Récupérer project_path
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    project_row = cursor.fetchone()
    if not project_row:
        raise ValueError(f"Projet {project_id} introuvable")
    
    project_path = Path(project_row["path"])
    
    # Vérifier whitelist
    if not is_file_writable(file_path, project_path):
        raise PermissionError(f"Fichier {file_path} non autorisé à l'écriture")
    
    full_path = project_path / file_path
    
    # Lire contenu actuel (ou vide si fichier n'existe pas)
    if full_path.exists():
        try:
            old_content = full_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Erreur lecture {file_path}: {str(e)}")
    else:
        old_content = ""
    
    # Calculer diff
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=file_path, tofile=file_path))
    
    return {
        "file_path": file_path,
        "diff": "".join(diff),
        "old_content": old_content,
        "new_content": new_content,
        "file_exists": full_path.exists()
    }


def apply_edit(
    session_id: int,
    file_path: str,
    new_content: str,
    db_conn: sqlite3.Connection
) -> None:
    """
    Applique une édition via mécanisme .tmp all-or-nothing.
    """
    cursor = db_conn.cursor()
    
    # Récupérer project_id
    cursor.execute("SELECT project_id FROM reflexion_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Session {session_id} introuvable")
    
    project_id = row["project_id"]
    
    # Récupérer project_path
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    project_row = cursor.fetchone()
    if not project_row:
        raise ValueError(f"Projet {project_id} introuvable")
    
    project_path = Path(project_row["path"])
    
    # Vérifier whitelist
    if not is_file_writable(file_path, project_path):
        raise PermissionError(f"Fichier {file_path} non autorisé à l'écriture")
    
    full_path = project_path / file_path
    tmp_path = full_path.with_suffix(full_path.suffix + ".tmp")
    
    try:
        # Écrire dans .tmp
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(new_content, encoding="utf-8")
        
        # Renommer atomique
        tmp_path.replace(full_path)
        
    except Exception as e:
        # Nettoyer .tmp en cas d'erreur
        if tmp_path.exists():
            tmp_path.unlink()
        raise ValueError(f"Erreur écriture {file_path}: {str(e)}")
