import json
import logging
import re
from backend.database import get_connection
from backend.services.model_router import get_model_id, call_model

logger = logging.getLogger("jarvis")

AGENT_NAME = "DISC"

_SYSTEM_PROMPT = (
    "Tu es DISC, expert certifié des règles WFDF d'Ultimate Frisbee 2025-2028. "
    "Tu maîtrises l'auto-arbitrage (self-officiating) et le Spirit of the Game (SOTG). "
    "Le jeu est sans arbitre externe : les joueurs appliquent les règles eux-mêmes.\n\n"
    "Structure TOUJOURS ta réponse exactement ainsi :\n\n"
    "## Situation analysée\n"
    "[Reformulation courte et précise de la situation décrite]\n\n"
    "## Règle(s) applicable(s)\n"
    "**Article X.Y — [Titre officiel]**\n"
    "> \"[Citation exacte du texte de la règle]\"\n"
    "Source : WFDF Rules of Ultimate 2025-2028, §X.Y\n\n"
    "## Résolution étape par étape\n"
    "1. [Action immédiate du joueur concerné]\n"
    "2. [Réaction attendue de l'adversaire]\n"
    "3. [Reprise du jeu]\n\n"
    "## Arbre de décision\n"
    "- Si accepté par tous → [résolution A]\n"
    "- Si contesté → [résolution B avec article applicable]\n"
    "- Si désaccord persistant → [procédure selon §X.X]\n\n"
    "## Spirit of the Game\n"
    "[Communication recommandée entre joueurs, ton à adopter, valeurs SOTG]\n\n"
    "## Articles connexes\n"
    "- §X.Z — [titre] : [pourquoi pertinent pour ce cas]\n\n"
    "Cite TOUJOURS les numéros d'articles exacts. Si tu n'es pas certain, "
    "indique-le explicitement. Préfère la précision à l'exhaustivité."
)

_ARTICLE_PATTERN = re.compile(
    r"(?:article|§|art\.?|règle|section)\s*(\d+[\.\d]*[a-zA-Z]?)",
    re.IGNORECASE
)

_SOTG_KEYWORDS = [
    "sotg", "spirit", "esprit", "fair play", "fair-play", "fairplay",
    "esprit du jeu", "respect", "violence", "intimidation", "triche", "tricherie"
]


async def handle(
    conversation_id: int,
    message: str,
    current_instance_ref: dict | None,
    db,
    config: dict
) -> tuple:
    msg_lower = message.lower()

    # Enregistrer la question
    _log_question(conversation_id, message, db)

    # Détection 1 — article par numéro
    article_match = _ARTICLE_PATTERN.search(message)
    if article_match:
        article_num = article_match.group(1)
        return await _handle_article_lookup(article_num, message, db, config)

    # Détection 2 — SOTG / esprit du jeu
    if any(k in msg_lower for k in _SOTG_KEYWORDS):
        return await _handle_sotg(message, db, config)

    # Détection 3 — situation concrète (fallback enrichi)
    return await _handle_situation(message, db, config)


# ─── Recherche par numéro d'article ──────────────────────────────────────────

async def _handle_article_lookup(article_num: str, message: str, db, config: dict) -> tuple:
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM disc_rules WHERE article = ? OR article LIKE ?",
        (article_num, f"{article_num}.%")
    )
    rules = [dict(r) for r in cur.fetchall()]

    if rules:
        context = _format_rules_context(rules)
        prompt = f"L'utilisateur demande des informations sur l'article {article_num}.\n\nRègles disponibles :\n{context}\n\nQuestion : {message}"
    else:
        prompt = f"L'utilisateur demande des informations sur l'article {article_num} des règles WFDF 2025-2028. Réponds selon ta connaissance des règles. Question : {message}"

    content = await _call_disc_llm(prompt, config, db)
    return content, AGENT_NAME, None, False, None


# ─── Situation SOTG ───────────────────────────────────────────────────────────

async def _handle_sotg(message: str, db, config: dict) -> tuple:
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM disc_rules WHERE categorie = 'spirit' ORDER BY article"
    )
    rules = [dict(r) for r in cur.fetchall()]

    context = _format_rules_context(rules) if rules else ""
    prompt_parts = ["L'utilisateur pose une question sur le Spirit of the Game (SOTG)."]
    if context:
        prompt_parts.append(f"Règles SOTG disponibles :\n{context}")
    prompt_parts.append(f"Question : {message}")
    prompt = "\n\n".join(prompt_parts)

    content = await _call_disc_llm(prompt, config, db)
    return content, AGENT_NAME, None, False, None


# ─── Situation concrète ───────────────────────────────────────────────────────

async def _handle_situation(message: str, db, config: dict) -> tuple:
    rules = _search_rules(message, db)

    context = _format_rules_context(rules) if rules else ""
    prompt_parts = ["L'utilisateur décrit une situation de jeu et demande l'application des règles WFDF 2025-2028."]
    if context:
        prompt_parts.append(f"Règles pertinentes trouvées :\n{context}")
    prompt_parts.append(f"Situation : {message}")
    prompt = "\n\n".join(prompt_parts)

    content = await _call_disc_llm(prompt, config, db)
    return content, AGENT_NAME, None, False, None


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _search_rules(query: str, db) -> list:
    """Recherche full-text dans disc_rules : mots-clés extraits + LIKE sur titre/contenu/mots_cles."""
    stop_words = {"le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "est", "qui",
                  "que", "quand", "si", "avec", "dans", "sur", "par", "pour", "au", "aux"}
    words = [w for w in re.findall(r'\w+', query.lower()) if len(w) > 3 and w not in stop_words]

    if not words:
        cur = db.cursor()
        cur.execute("SELECT * FROM disc_rules LIMIT 5")
        return [dict(r) for r in cur.fetchall()]

    cur = db.cursor()
    results = {}
    for word in words[:6]:
        cur.execute("""
            SELECT * FROM disc_rules
            WHERE LOWER(titre) LIKE ?
               OR LOWER(contenu) LIKE ?
               OR LOWER(mots_cles) LIKE ?
            LIMIT 5
        """, (f"%{word}%", f"%{word}%", f"%{word}%"))
        for row in cur.fetchall():
            r = dict(row)
            results[r["id"]] = r

    return list(results.values())[:5]


def _format_rules_context(rules: list) -> str:
    parts = []
    for r in rules:
        parts.append(
            f"**§{r['article']} — {r['titre']}**\n"
            f"{r['contenu']}"
        )
    return "\n\n".join(parts)


async def _call_disc_llm(user_content: str, config: dict, db) -> str:
    try:
        model_id = get_model_id("analysis", config)
        return await call_model(
            model_id=model_id,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            api_keys=config["api_keys"],
            session_id=None,
            step_name="disc_response",
            model_type="analysis",
            db_conn=db,
            module_name="disc"
        )
    except Exception as e:
        logger.error(f"[DISC] Erreur LLM: {e}")
        return (
            "[DISC] Je n'ai pas pu interroger le modèle. "
            "Vérifie que ta clé API est configurée dans les Paramètres."
        )


def _log_question(conversation_id: int, message: str, db) -> None:
    try:
        db.execute("""
            INSERT INTO disc_sessions (conversation_id, question, articles_utilises, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (conversation_id, message, "[]"))
        db.commit()
    except Exception as e:
        logger.warning(f"[DISC] _log_question échoué: {e}")
