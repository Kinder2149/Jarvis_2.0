import json
import logging
import re
from backend.services.model_router import get_model_id, call_model

logger = logging.getLogger("jarvis")

AGENT_NAME = "DISC"

_SYSTEM_PROMPT = (
    "Tu es DISC, expert certifié des règles WFDF d'Ultimate Frisbee 2025-2028. "
    "Tu maîtrises l'auto-arbitrage (self-officiating) et le Spirit of the Game (SOTG). "
    "Le jeu est sans arbitre externe : les joueurs appliquent les règles eux-mêmes.\n\n"
    "LANGUE : Réponds TOUJOURS en français, même si la question est en anglais. "
    "Les termes techniques WFDF (stall, foul, pick, strip, disc space, travel...) "
    "peuvent rester en anglais car ce sont des termes officiels du jeu.\n\n"
    "Structure TOUJOURS ta réponse exactement ainsi :\n\n"
    "## Situation analysée\n"
    "[Reformulation courte et précise de la situation décrite]\n\n"
    "## Règle(s) applicable(s)\n"
    "**Article X.Y — [Titre officiel]**\n"
    "> \"[Citation exacte du texte de la règle ou paraphrase fidèle]\"\n"
    "Source : WFDF Rules of Ultimate 2025-2028, §X.Y\n\n"
    "## Résolution étape par étape\n"
    "1. [Action immédiate du joueur concerné]\n"
    "2. [Réaction attendue de l'adversaire / de l'équipe]\n"
    "3. [Reprise du jeu — qui, où, comment]\n\n"
    "## Arbre de décision\n"
    "- Si accepté par tous → [résolution A]\n"
    "- Si contesté → [résolution B avec article applicable]\n"
    "- Si désaccord persistant → [procédure selon §X.X]\n\n"
    "## Spirit of the Game\n"
    "[Communication recommandée entre joueurs, ton à adopter, valeurs SOTG à rappeler]\n\n"
    "## Articles connexes\n"
    "- §X.Z — [titre] : [pourquoi pertinent pour ce cas]\n\n"
    "Règles de citation :\n"
    "- Cite TOUJOURS les numéros d'articles exacts (§X ou §X.Y)\n"
    "- Si tu n'es pas certain d'un numéro, écris 'environ §X' ou 'voir §X'\n"
    "- Préfère la précision à l'exhaustivité\n"
    "- Ne jamais inventer une règle — si tu ne la connais pas, dis-le clairement"
)

# Détection numéro d'article : "article 9", "§9", "§9.3", "art. 14.1", "règle 9"
_ARTICLE_PATTERN = re.compile(
    r"(?:article|§|art\.?\s*|règle\s+|section\s+)(\d{1,2}(?:\.\d{1,2})*(?:\.[A-Z])?)",
    re.IGNORECASE
)

# Aussi détecter numéro seul en début de message : "9", "9.3", "14.1"
_ARTICLE_ALONE_PATTERN = re.compile(
    r"^\s*(\d{1,2}(?:\.\d{1,2})*)\s*[?:]?\s*$"
)

_SOTG_KEYWORDS = [
    "sotg", "spirit", "esprit", "fair play", "fair-play", "fairplay",
    "esprit du jeu", "respect", "violence", "intimidation", "triche", "tricherie",
    "comportement", "attitude", "adversaire irrespectueux", "fair"
]

_STALL_KEYWORDS = [
    "stall", "décompte", "compte", "counting", "stalling", "fast count",
    "décompte rapide", "marqueur", "marquer", "défenseur marque"
]

_TRAVEL_KEYWORDS = [
    "travel", "marcher", "pivot", "pied pivot", "déplacer son pied",
    "bouger son pivot", "avance avec le disque"
]

_FOUL_KEYWORDS = [
    "foul", "faute", "contact", "touche", "heurte", "frappe",
    "strip", "arraché", "arrachage", "bousculade"
]

_OOB_KEYWORDS = [
    "hors", "ligne", "out", "oob", "hors-limites", "limite", "sortie",
    "touche la ligne", "dépasse", "derrière la ligne", "en-but"
]


# ─── Point d'entrée principal ─────────────────────────────────────────────────

async def handle(
    conversation_id: int,
    message: str,
    current_instance_ref: dict | None,
    db,
    config: dict
) -> tuple:
    msg_stripped = message.strip()
    msg_lower = msg_stripped.lower()

    # Détection 1 — numéro d'article explicite
    article_match = _ARTICLE_PATTERN.search(msg_stripped)
    if not article_match:
        article_match = _ARTICLE_ALONE_PATTERN.match(msg_stripped)

    if article_match:
        article_num = article_match.group(1)
        logger.info(f"[DISC] Requête article #{article_num} (conv={conversation_id})")
        content, articles_used = await _handle_article_lookup(article_num, msg_stripped, db, config)
        _log_question(conversation_id, msg_stripped, articles_used, db)
        return content, AGENT_NAME, None, False, None

    # Détection 2 — SOTG / esprit du jeu
    if any(k in msg_lower for k in _SOTG_KEYWORDS):
        logger.info(f"[DISC] Requête SOTG (conv={conversation_id})")
        content, articles_used = await _handle_sotg(msg_stripped, db, config)
        _log_question(conversation_id, msg_stripped, articles_used, db)
        return content, AGENT_NAME, None, False, None

    # Détection 3 — situation concrète
    logger.info(f"[DISC] Requête situation (conv={conversation_id}) : {msg_stripped[:60]}…")
    content, articles_used = await _handle_situation(msg_stripped, db, config)
    _log_question(conversation_id, msg_stripped, articles_used, db)
    return content, AGENT_NAME, None, False, None


# ─── Recherche par numéro d'article ──────────────────────────────────────────

async def _handle_article_lookup(article_num: str, message: str, db, config: dict) -> tuple[str, list]:
    cur = db.cursor()
    # Chercher l'article exact + tous ses sous-articles
    cur.execute(
        "SELECT * FROM disc_rules WHERE article = ? OR article LIKE ? ORDER BY article",
        (article_num, f"{article_num}.%")
    )
    rules = [dict(r) for r in cur.fetchall()]
    articles_used = [r["article"] for r in rules]

    if rules:
        context = _format_rules_context(rules)
        prompt = (
            f"L'utilisateur demande des informations sur l'article §{article_num} "
            f"des règles WFDF d'Ultimate Frisbee 2025-2028.\n\n"
            f"Règles disponibles en base :\n{context}\n\n"
            f"Question complète : {message}"
        )
        logger.info(f"[DISC] Article §{article_num} : {len(rules)} règle(s) trouvée(s) en base")
    else:
        prompt = (
            f"L'utilisateur demande des informations sur l'article §{article_num} "
            f"des règles WFDF d'Ultimate Frisbee 2025-2028. "
            f"Cet article n'est pas encore dans la base locale. "
            f"Utilise ta connaissance des règles WFDF pour répondre. "
            f"Indique explicitement que le numéro d'article est approximatif si tu n'es pas certain.\n\n"
            f"Question : {message}"
        )
        logger.warning(f"[DISC] Article §{article_num} non trouvé en base — fallback LLM")

    content = await _call_disc_llm(prompt, config, db)
    return content, articles_used


# ─── Situation SOTG ───────────────────────────────────────────────────────────

async def _handle_sotg(message: str, db, config: dict) -> tuple[str, list]:
    cur = db.cursor()
    cur.execute("SELECT * FROM disc_rules WHERE categorie = 'spirit' ORDER BY article")
    rules = [dict(r) for r in cur.fetchall()]
    articles_used = [r["article"] for r in rules]

    context = _format_rules_context(rules) if rules else ""
    parts = [
        "L'utilisateur pose une question sur le Spirit of the Game (SOTG) / l'esprit du jeu."
    ]
    if context:
        parts.append(f"Règles SOTG disponibles :\n{context}")
    parts.append(f"Question : {message}")
    prompt = "\n\n".join(parts)

    logger.info(f"[DISC] SOTG : {len(rules)} règle(s) spirit chargée(s)")
    content = await _call_disc_llm(prompt, config, db)
    return content, articles_used


# ─── Situation concrète de terrain ────────────────────────────────────────────

async def _handle_situation(message: str, db, config: dict) -> tuple[str, list]:
    rules = _search_rules(message, db)
    articles_used = [r["article"] for r in rules]

    context = _format_rules_context(rules) if rules else ""
    parts = [
        "L'utilisateur décrit une situation de jeu concrète et demande "
        "l'application correcte des règles WFDF 2025-2028."
    ]
    if context:
        parts.append(f"Règles pertinentes trouvées en base :\n{context}")
    else:
        parts.append(
            "Aucune règle correspondante trouvée en base locale. "
            "Utilise ta connaissance des règles WFDF 2025-2028."
        )
    parts.append(f"Situation décrite par l'utilisateur : {message}")
    prompt = "\n\n".join(parts)

    logger.info(f"[DISC] Situation : {len(rules)} règle(s) candidate(s) → {[r['article'] for r in rules]}")
    content = await _call_disc_llm(prompt, config, db)
    return content, articles_used


# ─── Recherche full-text dans disc_rules ─────────────────────────────────────

def _search_rules(query: str, db) -> list:
    """
    Recherche multi-passes dans disc_rules.
    Passe 1 : mots-clés spécialisés → ciblage catégorie
    Passe 2 : LIKE sur titre/contenu/mots_cles pour chaque token significatif
    """
    msg_lower = query.lower()
    cur = db.cursor()
    results: dict[int, dict] = {}

    # Passe 1 — catégories ciblées par mots-clés sémantiques
    category_hits = []
    if any(k in msg_lower for k in _STALL_KEYWORDS):
        category_hits.append("stall")
    if any(k in msg_lower for k in _TRAVEL_KEYWORDS):
        category_hits.append("violations")
    if any(k in msg_lower for k in _FOUL_KEYWORDS):
        category_hits.append("fouls")
    if any(k in msg_lower for k in _OOB_KEYWORDS):
        category_hits.append("out_of_bounds")
    if any(k in msg_lower for k in _SOTG_KEYWORDS):
        category_hits.append("spirit")

    if category_hits:
        placeholders = ",".join("?" * len(category_hits))
        cur.execute(
            f"SELECT * FROM disc_rules WHERE categorie IN ({placeholders}) ORDER BY article LIMIT 6",
            category_hits
        )
        for row in cur.fetchall():
            r = dict(row)
            results[r["id"]] = r

    # Passe 2 — LIKE sur tokens significatifs (2 chars min, inclut termes anglais courts)
    _stop = {
        "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "est",
        "qui", "que", "quand", "si", "avec", "dans", "sur", "par", "pour",
        "au", "aux", "il", "elle", "se", "ce", "son", "sa", "ses", "leur",
        "lors", "puis", "mais", "car", "donc", "doit", "peut", "sont", "ont",
        "the", "and", "for", "with", "this", "that", "from", "into"
    }
    tokens = [
        w for w in re.findall(r'\w+', msg_lower)
        if len(w) >= 3 and w not in _stop
    ]

    for token in tokens[:8]:
        like = f"%{token}%"
        cur.execute("""
            SELECT * FROM disc_rules
            WHERE LOWER(titre) LIKE ?
               OR LOWER(contenu) LIKE ?
               OR LOWER(mots_cles) LIKE ?
            LIMIT 4
        """, (like, like, like))
        for row in cur.fetchall():
            r = dict(row)
            results[r["id"]] = r

    # Limiter et trier par article
    all_results = sorted(results.values(), key=lambda r: r["article"])
    return all_results[:6]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _format_rules_context(rules: list) -> str:
    parts = []
    for r in rules:
        mots = ""
        try:
            kw = json.loads(r.get("mots_cles", "[]"))
            if kw:
                mots = f"\n  Mots-clés : {', '.join(kw[:5])}"
        except Exception:
            pass
        parts.append(
            f"**§{r['article']} — {r['titre']}**\n"
            f"{r['contenu']}"
            f"{mots}"
        )
    return "\n\n---\n\n".join(parts)


async def _call_disc_llm(user_content: str, config: dict, db) -> str:
    try:
        model_id = get_model_id("analysis", config)
        logger.info(f"[DISC] Appel LLM ({model_id})")
        result = await call_model(
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
        logger.info(f"[DISC] Réponse LLM reçue ({len(result)} chars)")
        return result
    except Exception as e:
        logger.error(f"[DISC] Erreur LLM : {e}")
        return (
            "**[DISC] Erreur de traitement**\n\n"
            "Je n'ai pas pu interroger le modèle de langage. "
            "Vérifie que ta clé API est configurée dans les Paramètres (OpenRouter ou Anthropic)."
        )


def _log_question(conversation_id: int, message: str, articles_used: list, db) -> None:
    try:
        db.execute("""
            INSERT INTO disc_sessions (conversation_id, question, articles_utilises, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (conversation_id, message[:500], json.dumps(articles_used, ensure_ascii=False)))
        db.commit()
        logger.info(f"[DISC] Question loggée — articles utilisés : {articles_used}")
    except Exception as e:
        logger.warning(f"[DISC] _log_question échoué : {e}")
