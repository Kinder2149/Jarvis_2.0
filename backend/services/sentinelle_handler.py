import json
import logging
import re
from backend.database import load_config
from backend.services.model_router import get_model_id, call_model
from backend.services import sentinelle_service
from datetime import datetime

logger = logging.getLogger("jarvis")


async def handle(conversation_id: int, message: str, db) -> tuple:
    """
    Retourne un 5-tuple identique aux autres handlers :
    (content, agent_used, instance_ref, suggest_freeze, freeze_reason)
    """
    config = load_config()
    
    # Étape 1 — Détection d'intention via call_model (Gemini Flash)
    intention = await _detect_intention(message, config, db)
    
    # Étape 2 — Traitement selon l'intention
    if intention == "agir":
        content = (
            "Je ne peux pas effectuer de transactions directement depuis cette conversation.\n\n"
            "Pour agir sur ton portefeuille (passer un ordre, valider une transaction, créer un cycle), "
            "rends-toi sur la page **Sentinelle** : [Ouvrir Sentinelle](sentinelle.html)"
        )
        return content, "SENTINELLE", None, False, None
    
    elif intention == "consulter":
        content = await _handle_consulter(message, config, db)
        return content, "SENTINELLE", None, False, None
    
    elif intention == "mettre_a_jour":
        content = await _handle_mettre_a_jour(message, db)
        return content, "SENTINELLE", None, False, None
    
    else:
        content = "Je n'ai pas bien compris ta demande. Peux-tu reformuler ?"
        return content, "SENTINELLE", None, False, None


async def _detect_intention(message: str, config: dict, db) -> str:
    """Détecte l'intention via call_model (Gemini Flash). Retourne 'consulter', 'mettre_a_jour' ou 'agir'."""
    prompt_system = """Tu analyses un message utilisateur concernant son portefeuille d'investissement SENTINELLE.
Classe l'intention dans exactement une des catégories suivantes :
- "consulter" : questions sur budget, positions, alertes, historique, watchlist
- "mettre_a_jour" : modifier thèses d'investissement, ajouter/retirer de la watchlist
- "agir" : passer un ordre, valider une transaction, créer un cycle, clôturer un cycle
Retourne uniquement du JSON strict : {"intention": "consulter"|"mettre_a_jour"|"agir"}"""
    
    try:
        model_id = get_model_id("routing", config)
        response = await call_model(
            model_id=model_id,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": message}
            ],
            api_keys=config["api_keys"],
            session_id=None,
            step_name="sentinelle_intention",
            model_type="routing",
            db_conn=db,
            module_name="sentinelle"
        )
        data = json.loads(response)
        return data.get("intention", "consulter")
    except Exception as e:
        logger.warning(f"[SENTINELLE] Détection intention échouée: {e}")
        return "consulter"


async def _handle_consulter(message: str, config: dict, db) -> str:
    """Traite une demande de consultation via call_model (Sonnet)."""
    mois_actuel = datetime.now().strftime("%Y-%m")
    budget = sentinelle_service.get_budget_restant(mois_actuel)
    
    # Utiliser la connexion db passée en paramètre (pas de nouvelle connexion)
    cur = db.cursor()
    cur.execute("SELECT ticker, quantite, enveloppe FROM sentinelle_positions ORDER BY created_at DESC")
    positions = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT ticker, niveau_risque FROM sentinelle_watchlist ORDER BY date_ajout DESC LIMIT 10")
    watchlist = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT ticker, variation_pct, cours_actuel FROM sentinelle_alertes WHERE lu = 0 ORDER BY created_at DESC LIMIT 5")
    alertes = [dict(r) for r in cur.fetchall()]
    
    prompt_system = f"""Tu es SENTINELLE, l'assistant investissement de Kinder.
Tu réponds à ses questions sur son portefeuille de façon concise et précise.
Données disponibles (JSON) :
- Budget mois {mois_actuel} : {budget}
- Positions : {json.dumps(positions, ensure_ascii=False)}
- Watchlist (10 derniers) : {json.dumps(watchlist, ensure_ascii=False)}
- Alertes non lues : {json.dumps(alertes, ensure_ascii=False)}
Réponds en français, max 300 mots, sans inventer de données absentes."""
    
    try:
        model_id = get_model_id("analysis", config)
        return await call_model(
            model_id=model_id,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": message}
            ],
            api_keys=config["api_keys"],
            session_id=None,
            step_name="sentinelle_consulter",
            model_type="analysis",
            db_conn=db,
            module_name="sentinelle"
        )
    except Exception as e:
        logger.error(f"[SENTINELLE] Erreur consultation: {e}")
        return "Désolé, je n'ai pas pu accéder aux données de ton portefeuille."


async def _handle_mettre_a_jour(message: str, db) -> str:
    """Traite une demande de mise à jour (watchlist uniquement depuis JARVIS)."""
    if "watchlist" in message.lower():
        return _update_watchlist(message, db)
    else:
        return (
            "Les thèses d'investissement se modifient directement dans la page **Sentinelle**.\n\n"
            "[Ouvrir Sentinelle](sentinelle.html)"
        )


def _update_watchlist(message: str, db) -> str:
    """Ajoute ou retire un ticker de la watchlist."""
    ticker_match = re.search(r'\b([A-Z]{2,5})\b', message)
    if not ticker_match:
        return "Je n'ai pas pu identifier le ticker dans ta demande."
    
    ticker = ticker_match.group(1)
    cursor = db.cursor()
    
    if any(word in message.lower() for word in ["ajoute", "ajouter", "add"]):
        cursor.execute(
            "INSERT OR IGNORE INTO sentinelle_watchlist (ticker, niveau_risque) VALUES (?, 'modere')",
            (ticker,)
        )
        db.commit()
        if cursor.rowcount > 0:
            return f"✅ **{ticker}** ajouté à ta watchlist."
        else:
            return f"**{ticker}** est déjà dans ta watchlist."
    
    elif any(word in message.lower() for word in ["retire", "retirer", "supprime", "supprimer", "remove"]):
        cursor.execute("DELETE FROM sentinelle_watchlist WHERE ticker = ?", (ticker,))
        db.commit()
        if cursor.rowcount > 0:
            return f"✅ **{ticker}** retiré de ta watchlist."
        else:
            return f"**{ticker}** n'était pas dans ta watchlist."
    
    else:
        return "Je n'ai pas compris si tu veux ajouter ou retirer ce ticker."
