# backend/services/chat_service.py

from pathlib import Path
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


def read_methodo_context(methodo_path: str) -> str:
    """Lit JARVIS_INDEX.md et charge les fichiers METHODO à injecter en contexte.
    
    Args:
        methodo_path: Chemin absolu vers le dossier METHODO
        
    Returns:
        String formaté avec les sections METHODO ou "" si absent
    """
    index_path = Path(methodo_path) / "JARVIS_INDEX.md"
    
    if not index_path.exists():
        logger.warning(f"JARVIS_INDEX.md absent : {index_path}")
        return ""
    
    try:
        index_content = index_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Erreur lecture JARVIS_INDEX.md : {e}")
        return ""
    
    # Parser les fichiers listés sous "TOUJOURS injectés"
    files_to_inject = []
    in_always_section = False
    
    for line in index_content.split('\n'):
        if "TOUJOURS injectés" in line:
            in_always_section = True
            continue
        
        if in_always_section:
            # Ignorer lignes vides au début
            if line.strip() == "":
                # Si on a déjà trouvé des fichiers, c'est la fin de section
                if files_to_inject:
                    break
                # Sinon continuer (ligne vide avant le tableau)
                continue
            
            # Fin de section si nouveau titre
            if line.startswith('#'):
                break
            
            # Ignorer ligne séparateur (|---|---|)
            if line.strip().startswith('|') and '---' in line:
                continue
            
            # Parser ligne tableau : | ordre | `chemin/fichier.md` | description |
            if '|' in line and '`' in line:
                parts = line.split('`')
                if len(parts) >= 2:
                    file_path = parts[1].strip()
                    if file_path and not file_path.startswith('-'):
                        files_to_inject.append(file_path)
    
    # Charger chaque fichier
    sections = []
    for file_rel_path in files_to_inject:
        file_path = Path(methodo_path) / file_rel_path
        
        if not file_path.exists():
            logger.warning(f"Fichier METHODO absent : {file_path}")
            continue
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Tronquer si trop long
            if len(content) > 16000:
                content = content[:16000] + "\n\n[... tronqué ...]"
            
            # Extraire titre depuis le nom de fichier
            title = file_path.stem.replace('_', ' ').upper()
            sections.append(f"=== {title} ===\n{content}")
            
        except Exception as e:
            logger.warning(f"Erreur lecture {file_path} : {e}")
            continue
    
    return "\n\n".join(sections)


def get_project_context(project_path: str) -> str | None:
    """Lit PROJET_CONTEXTE.md depuis le projet.
    
    Args:
        project_path: Chemin absolu vers le projet
        
    Returns:
        Contenu du fichier ou None si absent
    """
    context_path = Path(project_path) / "PROJET_CONTEXTE.md"
    
    if not context_path.exists():
        return None
    
    try:
        content = context_path.read_text(encoding="utf-8")
        
        # Tronquer si trop long
        if len(content) > 12000:
            content = content[:12000] + "\n\n[... tronqué ...]"
        
        return content
    
    except Exception as e:
        logger.warning(f"Erreur lecture PROJET_CONTEXTE.md : {e}")
        return None


def build_system_prompt(preset: str, methodo_context: str, session_note: str, project_context: str | None) -> str:
    """Construit le system prompt complet pour le chat.
    
    Args:
        preset: Prompt de base JARVIS
        methodo_context: Contexte METHODO (vide si absent)
        session_note: Note de session utilisateur (vide si absent)
        project_context: Contexte projet (None si pas de projet)
        
    Returns:
        System prompt complet
    """
    parts = [preset]
    
    if methodo_context:
        parts.append("---")
        parts.append(methodo_context)
    
    if session_note:
        parts.append("---")
        parts.append(f"NOTE DE SESSION :\n{session_note}")
    
    if project_context is not None:
        parts.append("---")
        parts.append(f"PROJET ACTIF :\n{project_context}")
    
    return "\n\n".join(parts)


async def send_chat_message(conversation_id: int, user_content: str, db, config: dict) -> dict:
    """Envoie un message chat et retourne la réponse de l'assistant.
    
    Args:
        conversation_id: ID de la conversation
        user_content: Message de l'utilisateur
        db: Connexion SQLite
        config: Configuration JARVIS (clés API, modèle chat, etc.)
        
    Returns:
        Dict avec user_message_id, assistant_message_id, content, tokens
        
    Raises:
        Exception: Si conversation introuvable ou erreur API
    """
    cursor = db.cursor()
    
    # Récupérer la conversation
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    conv_row = cursor.fetchone()
    
    if not conv_row:
        raise Exception(f"Conversation {conversation_id} introuvable")
    
    project_id = conv_row["project_id"]
    project_path = None
    
    # Récupérer le project_path si projet défini
    if project_id:
        cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
        project_row = cursor.fetchone()
        if project_row:
            project_path = project_row["path"]
    
    # Construire le contexte
    methodo_path = config.get("chat", {}).get("methodo_path", "")
    methodo_context = read_methodo_context(methodo_path) if methodo_path else ""
    
    project_context = None
    if project_path:
        project_context = get_project_context(project_path)
    
    # Construire le system prompt
    preset = config.get("chat", {}).get("system_prompt_preset", "")
    session_note = config.get("chat", {}).get("session_note", "")
    system_prompt = build_system_prompt(preset, methodo_context, session_note, project_context)
    
    # Récupérer les 20 derniers messages
    cursor.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 20",
        (conversation_id,)
    )
    history = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]
    
    # Construire les messages pour l'API
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})
    
    # Appel API OpenRouter
    openrouter_key = config.get("api_keys", {}).get("openrouter_key", "")
    model = config.get("chat", {}).get("model", "anthropic/claude-sonnet-4-5")
    
    if not openrouter_key:
        raise Exception("Clé API OpenRouter manquante dans la configuration")
    
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json"
    }
    
    body = {
        "model": model,
        "messages": messages
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=body
            )
            
            # Gestion erreurs HTTP
            if response.status_code == 401:
                raise Exception("Clé API invalide ou expirée. Vérifier dans Paramètres.")
            elif response.status_code == 429:
                raise Exception("Quota dépassé. Réessayer dans quelques minutes.")
            elif response.status_code == 404:
                raise Exception(f"Modèle introuvable : {model}. Vérifier le slug dans Paramètres.")
            elif response.status_code != 200:
                error_text = response.text[:200]
                raise Exception(f"Erreur API ({response.status_code}) : {error_text}")
            
            response_data = response.json()
    
    except httpx.TimeoutException:
        raise Exception("Modèle injoignable. Vérifier la connexion.")
    except httpx.NetworkError:
        raise Exception("Modèle injoignable. Vérifier la connexion.")
    
    # Extraire la réponse
    assistant_content = response_data["choices"][0]["message"]["content"]
    usage = response_data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    
    # Sauvegarder le message user
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content, input_tokens, output_tokens, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (conversation_id, "user", user_content, input_tokens, 0, now)
    )
    user_message_id = cursor.lastrowid
    
    # Sauvegarder le message assistant
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content, input_tokens, output_tokens, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (conversation_id, "assistant", assistant_content, 0, output_tokens, now)
    )
    assistant_message_id = cursor.lastrowid
    
    # Mettre à jour updated_at de la conversation
    cursor.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id)
    )
    
    db.commit()
    
    return {
        "user_message_id": user_message_id,
        "assistant_message_id": assistant_message_id,
        "content": assistant_content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    }
