# backend/services/chat_service.py

from pathlib import Path
import logging
import httpx
import re
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024  # 50 Ko


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


def read_graphify_report(project_path: str, max_lines: int = 80) -> str:
    """Lit les premières lignes du GRAPH_REPORT.md du projet sélectionné.
    
    Args:
        project_path: Chemin absolu vers le dossier du projet
        max_lines: Nombre de lignes maximum à lire (évite de surcharger le contexte)
        
    Returns:
        String avec le résumé du graphe, ou "" si absent
    """
    if not project_path:
        return ""
    
    report_path = Path(project_path) / "graphify-out" / "GRAPH_REPORT.md"
    
    if not report_path.exists():
        return ""
    
    try:
        lines = report_path.read_text(encoding="utf-8").splitlines()
        excerpt = "\n".join(lines[:max_lines])
        return excerpt
    except Exception as e:
        logger.warning(f"Erreur lecture graphify report : {e}")
        return ""


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


def read_local_folder(folder_path: str, recursive: bool = False) -> dict:
    """Liste les fichiers d'un dossier local.
    
    Args:
        folder_path: Chemin absolu vers le dossier
        recursive: Si True, liste récursivement
        
    Returns:
        Dict avec files (liste), graph_report (bool), error (str optionnel)
    """
    try:
        folder = Path(folder_path).resolve()
        
        if not folder.exists():
            return {"files": [], "graph_report": False, "error": "Dossier introuvable"}
        
        if not folder.is_dir():
            return {"files": [], "graph_report": False, "error": "Chemin n'est pas un dossier"}
        
        # Vérifier si GRAPH_REPORT.md existe
        graph_report_path = folder / "graphify-out" / "GRAPH_REPORT.md"
        has_graph_report = graph_report_path.exists()
        
        files = []
        
        if recursive:
            for file_path in folder.rglob("*"):
                if file_path.is_file():
                    try:
                        size = file_path.stat().st_size
                        rel_path = file_path.relative_to(folder)
                        files.append({"path": str(rel_path), "size": size})
                    except Exception:
                        continue
        else:
            for file_path in folder.iterdir():
                if file_path.is_file():
                    try:
                        size = file_path.stat().st_size
                        files.append({"path": file_path.name, "size": size})
                    except Exception:
                        continue
        
        return {
            "files": sorted(files, key=lambda x: x["path"]),
            "graph_report": has_graph_report,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"Erreur lecture dossier {folder_path} : {e}")
        return {"files": [], "graph_report": False, "error": str(e)}


def read_local_file(folder_path: str, relative_path: str) -> dict:
    """Lit le contenu d'un fichier dans le dossier local.
    
    Args:
        folder_path: Chemin absolu vers le dossier racine
        relative_path: Chemin relatif du fichier dans le dossier
        
    Returns:
        Dict avec content (str), truncated (bool), error (str optionnel)
    """
    try:
        folder = Path(folder_path).resolve()
        file_path = (folder / relative_path).resolve()
        
        # Sécurité : vérifier que le fichier est bien dans folder_path
        if not str(file_path).startswith(str(folder)):
            return {"content": "", "truncated": False, "error": "Accès refusé (path traversal)"}
        
        if not file_path.exists():
            return {"content": "", "truncated": False, "error": "Fichier introuvable"}
        
        if not file_path.is_file():
            return {"content": "", "truncated": False, "error": "Chemin n'est pas un fichier"}
        
        # Vérifier la taille
        file_size = file_path.stat().st_size
        
        if file_size > MAX_FILE_SIZE:
            # Lire les premiers 50 Ko
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(MAX_FILE_SIZE)
            return {
                "content": content,
                "truncated": True,
                "error": None
            }
        
        # Lire le fichier complet
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        
        return {
            "content": content,
            "truncated": False,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"Erreur lecture fichier {relative_path} dans {folder_path} : {e}")
        return {"content": "", "truncated": False, "error": str(e)}


async def search_web(query: str, api_key: str | None = None) -> dict:
    """Effectue une recherche web et retourne les résultats.
    
    Args:
        query: Requête de recherche
        api_key: Clé API pour le provider de recherche (optionnel)
        
    Returns:
        Dict avec results (liste), error (str optionnel)
    """
    if not api_key:
        logger.info("Recherche web désactivée : pas de clé API")
        return {"results": [], "error": "Recherche web désactivée (clé API manquante)"}
    
    try:
        # Utiliser Brave Search API (gratuit avec clé)
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        
        params = {
            "q": query,
            "count": 5
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                logger.warning(f"Erreur recherche web : {response.status_code}")
                return {"results": [], "error": f"Erreur API ({response.status_code})"}
            
            data = response.json()
            
            # Extraire les résultats
            results = []
            for item in data.get("web", {}).get("results", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", "")
                })
            
            return {"results": results, "error": None}
    
    except httpx.TimeoutException:
        logger.warning("Timeout recherche web")
        return {"results": [], "error": "Timeout"}
    except Exception as e:
        logger.error(f"Erreur recherche web : {e}")
        return {"results": [], "error": str(e)}


def build_system_prompt(preset: str, methodo_context: str, session_note: str, project_context: str | None, folder_context: str | None = None, global_context: str = "", context_summary: str = "", graphify_context: str = "", internet_access: bool = False) -> str:
    """Construit le system prompt complet pour le chat.
    
    Args:
        preset: Prompt de base JARVIS
        methodo_context: Contexte METHODO (vide si absent)
        session_note: Note de session utilisateur (vide si absent)
        project_context: Contexte projet (None si pas de projet)
        folder_context: Liste fichiers dossier local (None si pas de dossier)
        global_context: Contexte global (Prompt Générique) injecté en premier
        context_summary: Résumé de la conversation (vide si absent)
        graphify_context: Graphe du projet (vide si absent)
        
    Returns:
        System prompt complet
    """
    parts = []
    
    # Global context EN PREMIER
    if global_context:
        parts.append(global_context)
        parts.append("---")
    
    # Résumé de conversation APRÈS global_context
    if context_summary:
        parts.append(f"📋 RÉSUMÉ DE CETTE CONVERSATION :\n{context_summary}")
        parts.append("---")
    
    parts.append(preset)
    
    if methodo_context:
        parts.append("---")
        parts.append(methodo_context)
    
    if session_note:
        parts.append("---")
        parts.append(f"NOTE DE SESSION :\n{session_note}")
    
    if project_context is not None:
        parts.append("---")
        parts.append(f"PROJET ACTIF :\n{project_context}")
    
    if graphify_context:
        parts.append("\n--- GRAPHE PROJET (structure et dépendances) ---")
        parts.append(graphify_context)
        parts.append("--- FIN GRAPHE ---\n")
    
    if folder_context is not None:
        parts.append("---")
        parts.append(f"DOSSIER LOCAL :\n{folder_context}")
    
    if internet_access:
        parts.append("---")
        parts.append(
            "🌐 ACCÈS INTERNET ACTIVÉ : Tu as accès à des résultats de recherche web via Brave Search. "
            "Quand l'utilisateur pose des questions sur l'actualité, la météo, les événements récents "
            "ou toute information en temps réel, les résultats apparaissent dans la section "
            "\"Résultats recherche web\" du message. Utilise ces résultats directement. "
            "Ne dis jamais que tu ne peux pas accéder à internet."
        )
    
    return "\n\n".join(parts)


async def send_chat_message(conversation_id: int, user_content: str, db, config: dict) -> dict:
    """Envoie un message chat et retourne la réponse de l'assistant.
    
    Args:
        conversation_id: ID de la conversation
        user_content: Message de l'utilisateur
        db: Connexion SQLite
        config: Configuration JARVIS (clés API, modèle chat, etc.)
        
    Returns:
        Dict avec user_message_id, assistant_message_id, content, tokens, web_search_used
        
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
    folder_path = conv_row["folder_path"]
    internet_access = bool(conv_row["internet_access"]) if "internet_access" in conv_row.keys() else False
    context_summary = conv_row["context_summary"] if "context_summary" in conv_row.keys() else ""
    conv_model = conv_row["model"] if "model" in conv_row.keys() else ""
    project_path = None
    
    # Récupérer le project_path si projet défini
    if project_id:
        cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
        project_row = cursor.fetchone()
        if project_row:
            project_path = project_row["path"]
    
    # Déterminer le dossier local à utiliser
    local_folder = None
    if folder_path:
        local_folder = folder_path
    elif project_path:
        local_folder = project_path
    
    # Construire le contexte
    methodo_path = config.get("chat", {}).get("methodo_path", "")
    methodo_context = read_methodo_context(methodo_path) if methodo_path else ""
    
    project_context = None
    if project_path:
        project_context = get_project_context(project_path)
    
    graphify_context = read_graphify_report(project_path) if project_path else ""
    
    # Contexte dossier local
    folder_context = None
    if local_folder:
        folder_data = read_local_folder(local_folder, recursive=False)
        if not folder_data["error"]:
            files_list = "\n".join([f"- {f['path']} ({f['size']} bytes)" for f in folder_data["files"][:50]])
            folder_context = f"Dossier : {local_folder}\n\nFichiers disponibles :\n{files_list}"
            
            # Priorité GRAPH_REPORT.md si présent
            if folder_data["graph_report"]:
                graph_result = read_local_file(local_folder, "graphify-out/GRAPH_REPORT.md")
                if not graph_result["error"]:
                    folder_context += f"\n\n=== GRAPH_REPORT.md ===\n{graph_result['content'][:8000]}"
    
    # Détection fichiers à lire dans le message utilisateur
    file_content_injected = ""
    if local_folder:
        # Patterns : "lis [fichier]", "ouvre [fichier]", "lit [fichier]"
        file_patterns = [
            r'(?:lis|ouvre|lit|lire|ouvrir)\s+([^\s]+)',
            r'(?:fichier|file)\s+([^\s]+)'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, user_content, re.IGNORECASE)
            for filename in matches:
                filename = filename.strip('"`\'')
                file_result = read_local_file(local_folder, filename)
                if not file_result["error"]:
                    truncated_msg = " [TRONQUÉ]" if file_result["truncated"] else ""
                    file_content_injected += f"\n\n=== Contenu de {filename}{truncated_msg} ===\n{file_result['content']}"
    
    # Détection recherche web (conditionnée sur internet_access)
    web_search_used = False
    web_results_text = ""
    
    if internet_access:
        web_search_patterns = [
            r'(?:cherche|recherche|trouve|search)',
            r'(?:internet|web|en ligne)',
            r'(?:dernière version|version actuelle|aujourd\'hui|actuellement|récemment)',
            r'(?:actualités?|actu|nouvelles?|news)',
            r'(?:météo|temps qu\'il fait|température|climat)',
            r'(?:hier|demain|cette semaine|ce mois|en \d{4})',
        ]
        
        should_search = any(re.search(pattern, user_content, re.IGNORECASE) for pattern in web_search_patterns)
        
        logger.info(f"🌐 [CHAT_SERVICE] internet_access={internet_access}, should_search={should_search}")
        
        if should_search:
            web_search_key = config.get("api_keys", {}).get("web_search_key")
            logger.info(f"🔑 [CHAT_SERVICE] web_search_key présente: {bool(web_search_key)}, longueur: {len(web_search_key) if web_search_key else 0}")
            if web_search_key:
                search_result = await search_web(user_content, web_search_key)
                logger.info(f"🔍 [CHAT_SERVICE] Résultat recherche: error={search_result.get('error')}, nb_results={len(search_result.get('results', []))}")
                if not search_result["error"] and search_result["results"]:
                    web_search_used = True
                    web_results_text = "\n\n=== Résultats recherche web ===\n"
                    for i, result in enumerate(search_result["results"], 1):
                        web_results_text += f"{i}. {result['title']}\n   {result['url']}\n   {result['description']}\n\n"
            else:
                logger.warning(f"⚠️ [CHAT_SERVICE] Recherche web demandée mais clé absente")
    
    # Récupérer global_context depuis app_config
    try:
        cursor.execute("SELECT value FROM app_config WHERE key = 'global_context'")
        global_context_row = cursor.fetchone()
        global_context = global_context_row["value"] if global_context_row else ""
    except Exception:
        global_context = ""
    
    # Construire le system prompt
    preset = config.get("chat", {}).get("system_prompt_preset", "")
    session_note = config.get("chat", {}).get("session_note", "")
    system_prompt = build_system_prompt(preset, methodo_context, session_note, project_context, folder_context, global_context, context_summary, graphify_context, internet_access)
    
    # Récupérer les 20 derniers messages
    cursor.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 20",
        (conversation_id,)
    )
    history = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]
    
    # Construire le message utilisateur enrichi
    enriched_user_content = user_content + file_content_injected + web_results_text
    
    # Construire les messages pour l'API
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": enriched_user_content})
    
    # Appel API OpenRouter
    openrouter_key = config.get("api_keys", {}).get("openrouter_key", "")
    # Utiliser conv_model en priorité si défini
    model = conv_model or config.get("chat", {}).get("model", "anthropic/claude-sonnet-4-5")
    
    logger.info(f"🔑 [CHAT_SERVICE] openrouter_key présente: {bool(openrouter_key)}, longueur: {len(openrouter_key) if openrouter_key else 0}")
    logger.info(f"🤖 [CHAT_SERVICE] Modèle: {model}")
    
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
    
    # Auto-titrage sur le premier message
    cursor.execute("SELECT COUNT(*) as count FROM messages WHERE conversation_id = ?", (conversation_id,))
    message_count = cursor.fetchone()["count"]
    
    if message_count == 1:
        # Premier message → mettre à jour le titre
        title = user_content[:60]
        # Couper proprement sur un mot
        if len(user_content) > 60:
            last_space = title.rfind(' ')
            if last_space > 30:  # Garder au moins 30 caractères
                title = title[:last_space]
            title += "..."
        
        cursor.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (title, conversation_id)
        )
    
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
    
    # Auto-update du résumé toutes les 10 paires user/assistant
    cursor.execute(
        "SELECT COUNT(*) as count FROM messages WHERE conversation_id = ? AND role = 'user'",
        (conversation_id,)
    )
    user_message_count = cursor.fetchone()["count"]
    
    if user_message_count % 10 == 0 and user_message_count > 0:
        logger.info(f"📋 [CHAT_SERVICE] Déclenchement auto-update résumé — {user_message_count} paires pour conv {conversation_id}")
        import asyncio
        from backend.routers.chat import update_conversation_summary
        try:
            asyncio.ensure_future(update_conversation_summary(conversation_id))
        except Exception as e:
            logger.warning(f"⚠️ [CHAT_SERVICE] Erreur auto-update résumé : {e}")
    
    return {
        "user_message_id": user_message_id,
        "assistant_message_id": assistant_message_id,
        "content": assistant_content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "web_search_used": web_search_used
    }
