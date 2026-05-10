from backend.database import get_connection, load_config
from backend.services.model_router import get_model_id
from datetime import datetime, timedelta
from typing import Optional
import httpx
import yfinance as yf
import json
import logging

logger = logging.getLogger("jarvis")


def get_budget_restant(mois: str) -> dict:
    """
    Calcule le budget restant pour un mois donné (format YYYY-MM).
    Retourne: {budget_mensuel, budget_utilise, budget_restant, carry_over}
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Récupérer le dernier cycle du mois
    cursor.execute("""
        SELECT budget_mensuel, budget_utilise 
        FROM sentinelle_cycles 
        WHERE mois = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (mois,))
    cycle_row = cursor.fetchone()
    
    if not cycle_row:
        conn.close()
        return {
            "budget_mensuel": 0.0,
            "budget_utilise": 0.0,
            "budget_restant": 0.0,
            "carry_over": 0.0
        }
    
    budget_mensuel = cycle_row["budget_mensuel"]
    budget_utilise = cycle_row["budget_utilise"]
    
    # Calculer carry-over du mois précédent
    carry_over = _get_carry_over(mois, cursor)
    
    budget_restant = budget_mensuel + carry_over - budget_utilise
    
    conn.close()
    
    return {
        "budget_mensuel": budget_mensuel,
        "budget_utilise": budget_utilise,
        "budget_restant": budget_restant,
        "carry_over": carry_over
    }


def _get_carry_over(mois: str, cursor) -> float:
    """Calcule le report du mois précédent."""
    try:
        year, month = map(int, mois.split('-'))
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        prev_mois = f"{prev_year:04d}-{prev_month:02d}"
        
        cursor.execute("""
            SELECT budget_mensuel, budget_utilise 
            FROM sentinelle_cycles 
            WHERE mois = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (prev_mois,))
        prev_row = cursor.fetchone()
        
        if not prev_row:
            return 0.0
        
        prev_restant = prev_row["budget_mensuel"] - prev_row["budget_utilise"]
        return max(0.0, prev_restant)
    
    except Exception:
        return 0.0


def get_dernier_budget_mensuel() -> float:
    """Retourne le dernier budget_mensuel connu (pour pré-remplir Phase 1)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT budget_mensuel 
        FROM sentinelle_cycles 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    return row["budget_mensuel"] if row else 20.0


def peut_creer_cycle() -> bool:
    """Vérifie qu'aucun cycle non clôturé n'existe déjà."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM sentinelle_cycles 
        WHERE etat != 'CLOTURE'
    """)
    row = cursor.fetchone()
    conn.close()
    
    return row["count"] == 0


def transition_etat_valide(etat_actuel: str, etat_suivant: str) -> bool:
    """Vérifie que la transition d'état est légale."""
    transitions_valides = {
        "PHASE_1": ["PHASE_2"],
        "PHASE_2": ["PHASE_3"],
        "PHASE_3": ["PHASE_4"],
        "PHASE_4": ["PHASE_5", "PHASE_6"],
        "PHASE_5": ["PHASE_6"],
        "PHASE_6": ["CLOTURE"],
        "CLOTURE": []
    }
    
    return etat_suivant in transitions_valides.get(etat_actuel, [])


def calculer_budget_utilise_cycle(cycle_id: int) -> float:
    """Calcule le budget utilisé pour un cycle donné (somme des transactions)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(quantite * prix_reel + frais), 0.0) as total
        FROM sentinelle_transactions
        WHERE cycle_id = ?
    """, (cycle_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row["total"]


CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "ADA", "DOT", "AVAX", "MATIC", "LINK", "UNI"]


def _fetch_yahoo_prices(tickers: list[str]) -> dict:
    """Récupère les cours et variations depuis Yahoo Finance."""
    prices = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1wk")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                week_ago_price = hist['Close'].iloc[0]
                variation_pct = ((current_price - week_ago_price) / week_ago_price) * 100
                prices[ticker] = {
                    "cours": round(current_price, 2),
                    "variation_1w": round(variation_pct, 2)
                }
            else:
                prices[ticker] = {"cours": None, "variation_1w": None}
        except Exception as e:
            logger.warning(f"[SENTINELLE] Erreur Yahoo Finance pour {ticker}: {e}")
            prices[ticker] = {"cours": None, "variation_1w": None}
    return prices


async def _fetch_coingecko_prices(crypto_symbols: list[str]) -> dict:
    """Récupère les cours crypto depuis CoinGecko API publique."""
    if not crypto_symbols:
        return {}
    
    crypto_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "BNB": "binancecoin", "ADA": "cardano", "DOT": "polkadot",
        "AVAX": "avalanche-2", "MATIC": "matic-network",
        "LINK": "chainlink", "UNI": "uniswap"
    }
    
    ids = ",".join([crypto_map.get(sym, sym.lower()) for sym in crypto_symbols if sym in crypto_map])
    if not ids:
        return {}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur&include_24h_change=true"
            )
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for symbol, coin_id in crypto_map.items():
                    if symbol in crypto_symbols and coin_id in data:
                        prices[symbol] = {
                            "cours": data[coin_id].get("eur"),
                            "variation_24h": round(data[coin_id].get("eur_24h_change", 0), 2)
                        }
                return prices
    except Exception as e:
        logger.warning(f"[SENTINELLE] Erreur CoinGecko: {e}")
    return {}


def _detecter_biais(positions: list, watchlist: list, cycles_precedents: list, theses: list) -> list:
    """Détecte les biais cognitifs dans le portefeuille."""
    biais = []
    
    total_value = sum([p.get("valorisation", 0) for p in positions])
    
    for pos in positions:
        if total_value > 0 and (pos.get("valorisation", 0) / total_value) > 0.30:
            biais.append({
                "type": "Sur-concentration",
                "actif": pos.get("ticker"),
                "details": f"{pos.get('ticker')} représente > 30% du portefeuille"
            })
    
    secteurs = {}
    for w in watchlist:
        niveau = w.get("niveau_risque", "modere")
        secteurs[niveau] = secteurs.get(niveau, 0) + 1
    
    if secteurs and max(secteurs.values()) / sum(secteurs.values()) > 0.80:
        biais.append({
            "type": "Biais de confirmation",
            "details": "Watchlist concentrée sur un seul niveau de risque"
        })
    
    return biais


async def run_veille(cycle_id: int) -> dict:
    """SKILL 1 - Veille : Récupère cours + variations et génère résumé IA."""
    from backend.services import model_router
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    cycle = cursor.fetchone()
    if not cycle:
        conn.close()
        raise ValueError("Cycle non trouvé")
    
    cursor.execute("SELECT ticker FROM sentinelle_positions")
    positions = [row["ticker"] for row in cursor.fetchall()]
    
    cursor.execute("SELECT ticker FROM sentinelle_watchlist")
    watchlist = [row["ticker"] for row in cursor.fetchall()]
    
    all_tickers = list(set(positions + watchlist))
    crypto_tickers = [t for t in all_tickers if t in CRYPTO_SYMBOLS]
    stock_tickers = [t for t in all_tickers if t not in CRYPTO_SYMBOLS]
    
    stock_prices = _fetch_yahoo_prices(stock_tickers)
    crypto_prices = await _fetch_coingecko_prices(crypto_tickers)
    
    all_prices = {**stock_prices, **crypto_prices}
    
    prompt = f"""Tu es Sentinelle, assistant d'investissement discipliné. Voici les positions et watchlist d'un investisseur particulier avec petits budgets (20€/mois).

Résume en bullet points les signaux notables cette semaine : variations importantes (>5%), actualités marquantes sur ces actifs.

Format : 3 sections — Positions détenues / Watchlist / Macro (1-2 points macro). Maximum 300 mots.

Actifs surveillés :
- Positions : {', '.join(positions) if positions else 'Aucune'}
- Watchlist : {', '.join(watchlist) if watchlist else 'Aucune'}

Variations cette semaine :
{json.dumps(all_prices, indent=2, ensure_ascii=False)}
"""
    
    config = load_config()
    model_id = get_model_id("routing", config)
    
    messages = [{"role": "user", "content": prompt}]
    
    resultat = await model_router.call_model(
        model_id=model_id,
        messages=messages,
        api_keys=config["api_keys"],
        session_id=0,
        step_name="sentinelle_veille",
        model_type="routing",
        db_conn=None
    )
    
    donnees_veille = {
        "cours": all_prices,
        "resume_ia": resultat,
        "timestamp": datetime.now().isoformat()
    }
    
    cursor.execute(
        "UPDATE sentinelle_cycles SET donnees_veille = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(donnees_veille), cycle_id)
    )
    conn.commit()
    conn.close()
    
    return donnees_veille


async def run_analyse(cycle_id: int) -> dict:
    """SKILL 2 - Analyse : Calcule valorisation + allocation + dérives."""
    from backend.services import model_router
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    cycle = cursor.fetchone()
    if not cycle:
        conn.close()
        raise ValueError("Cycle non trouvé")
    
    cursor.execute("SELECT * FROM sentinelle_positions")
    positions_rows = cursor.fetchall()
    
    veille_data = json.loads(cycle["donnees_veille"]) if cycle["donnees_veille"] else {}
    cours = veille_data.get("cours", {})
    
    if not cours or (datetime.now() - datetime.fromisoformat(veille_data.get("timestamp", "2000-01-01"))).seconds > 3600:
        cursor.execute("SELECT ticker FROM sentinelle_positions")
        tickers = [row["ticker"] for row in cursor.fetchall()]
        cours = _fetch_yahoo_prices(tickers)
    
    positions_valorisees = []
    total_value = 0
    repartition_enveloppe = {"PEA": 0, "CTO": 0, "liquidites": 0}
    
    for pos in positions_rows:
        ticker = pos["ticker"]
        quantite = pos["quantite"]
        enveloppe = pos["enveloppe"]
        prix_actuel = cours.get(ticker, {}).get("cours", 0)
        valorisation = quantite * prix_actuel if prix_actuel else 0
        
        positions_valorisees.append({
            "ticker": ticker,
            "quantite": quantite,
            "enveloppe": enveloppe,
            "prix_actuel": prix_actuel,
            "valorisation": valorisation
        })
        
        total_value += valorisation
        repartition_enveloppe[enveloppe] += valorisation
    
    allocation_cible = {"passif": 0.70, "thematique": 0.20, "speculatif": 0.10}
    
    prompt = f"""Voici le portefeuille valorisé. Calcule le bilan : valeur totale, répartition par enveloppe (PEA/CTO), dérive vs allocation cible 70/20/10.

Identifie les dérives > 10%. Format structuré en 3 blocs : Valorisation / Allocation / Alertes dérive.

Données :
- Valeur totale : {total_value:.2f}€
- Répartition enveloppe : {json.dumps(repartition_enveloppe, ensure_ascii=False)}
- Positions : {json.dumps(positions_valorisees, indent=2, ensure_ascii=False)}
- Allocation cible : 70% passif / 20% thématique / 10% spéculatif
"""
    
    config = load_config()
    model_id = get_model_id("routing", config)
    
    messages = [{"role": "user", "content": prompt}]
    
    resultat = await model_router.call_model(
        model_id=model_id,
        messages=messages,
        api_keys=config["api_keys"],
        session_id=0,
        step_name="sentinelle_analyse",
        model_type="routing",
        db_conn=None
    )
    
    donnees_analyse = {
        "valorisation_totale": total_value,
        "repartition_enveloppe": repartition_enveloppe,
        "positions": positions_valorisees,
        "resume_ia": resultat,
        "timestamp": datetime.now().isoformat()
    }
    
    cursor.execute(
        "UPDATE sentinelle_cycles SET donnees_analyse = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(donnees_analyse), cycle_id)
    )
    conn.commit()
    conn.close()
    
    return donnees_analyse


async def run_propositions(cycle_id: int) -> dict:
    """SKILL 3 - Propositions : Génère 3 scénarios d'investissement avec détection biais."""
    from backend.services import model_router
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    cycle = cursor.fetchone()
    if not cycle:
        conn.close()
        raise ValueError("Cycle non trouvé")
    
    veille_data = json.loads(cycle["donnees_veille"]) if cycle["donnees_veille"] else {}
    analyse_data = json.loads(cycle["donnees_analyse"]) if cycle["donnees_analyse"] else {}
    
    cursor.execute("SELECT * FROM sentinelle_theses WHERE statut = 'active'")
    theses = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM sentinelle_positions")
    positions = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM sentinelle_watchlist")
    watchlist = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id < ? ORDER BY created_at DESC LIMIT 3", (cycle_id,))
    cycles_precedents = [dict(row) for row in cursor.fetchall()]
    
    biais_detectes = _detecter_biais(analyse_data.get("positions", []), watchlist, cycles_precedents, theses)
    
    budget_info = get_budget_restant(cycle["mois"])
    budget_restant = budget_info["budget_restant"]
    
    prompt = f"""Tu es Sentinelle, assistant d'investissement discipliné pour un investisseur débutant avec 20€/mois.

Stratégie : 70% ETF passif / 20% thématique / 10% spéculatif.

Budget disponible ce cycle : {budget_restant:.2f}€.

Voici le bilan du portefeuille :
{json.dumps(analyse_data, indent=2, ensure_ascii=False)}

Voici la veille de la semaine :
{veille_data.get('resume_ia', 'Aucune veille disponible')}

Voici les thèses actives :
{json.dumps(theses, indent=2, ensure_ascii=False) if theses else 'Aucune thèse active'}

Biais détectés automatiquement :
{json.dumps(biais_detectes, indent=2, ensure_ascii=False) if biais_detectes else 'Aucun biais détecté'}

Produis exactement 3 scénarios d'utilisation du budget. Pour chaque scénario :
- Nom du scénario
- Actif(s) concerné(s)
- Montant proposé
- Niveau de risque (faible/modéré/élevé/spéculatif)
- Argumentaire en 3 phrases
- Contre-arguments en 2 phrases

Signale les biais détectés avec une question de recadrage. Ne jamais utiliser le terme 'valeur sûre'. Pas de prédictions de cours.
"""
    
    config = load_config()
    model_id = get_model_id("analysis", config)
    
    messages = [{"role": "user", "content": prompt}]
    
    resultat = await model_router.call_model(
        model_id=model_id,
        messages=messages,
        api_keys=config["api_keys"],
        session_id=0,
        step_name="sentinelle_propositions",
        model_type="analysis",
        db_conn=None
    )
    
    donnees_propositions = {
        "scenarios": resultat,
        "biais_detectes": biais_detectes,
        "budget_disponible": budget_restant,
        "timestamp": datetime.now().isoformat()
    }
    
    cursor.execute(
        "UPDATE sentinelle_cycles SET donnees_propositions = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(donnees_propositions), cycle_id)
    )
    conn.commit()
    conn.close()
    
    return donnees_propositions


async def run_ordre(cycle_id: int, scenario_choisi: str, montant: float) -> dict:
    """SKILL 4 - Ordre : Génère paramètres d'ordre précis pour Trade Republic."""
    from backend.services import model_router
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sentinelle_cycles WHERE id = ?", (cycle_id,))
    cycle = cursor.fetchone()
    if not cycle:
        conn.close()
        raise ValueError("Cycle non trouvé")
    
    propositions_data = json.loads(cycle["donnees_propositions"]) if cycle["donnees_propositions"] else {}
    veille_data = json.loads(cycle["donnees_veille"]) if cycle["donnees_veille"] else {}
    cours = veille_data.get("cours", {})
    
    prompt = f"""L'investisseur a choisi le scénario suivant : {scenario_choisi}.

Budget : {montant}€.

Cours actuels disponibles :
{json.dumps(cours, indent=2, ensure_ascii=False)}

Génère les paramètres d'ordre précis pour Trade Republic :
- Type d'ordre recommandé (market order ou limit order avec prix suggéré)
- Quantité exacte calculée
- Enveloppe à utiliser (PEA ou CTO)
- Frais estimés (1€ par ordre Trade Republic)

Format : tableau clair avec 4 colonnes : Paramètre / Valeur / Pourquoi / Attention.
"""
    
    config = load_config()
    model_id = get_model_id("routing", config)
    
    messages = [{"role": "user", "content": prompt}]
    
    resultat = await model_router.call_model(
        model_id=model_id,
        messages=messages,
        api_keys=config["api_keys"],
        session_id=0,
        step_name="sentinelle_ordre",
        model_type="routing",
        db_conn=None
    )
    
    conn.close()
    
    return {
        "scenario": scenario_choisi,
        "montant": montant,
        "parametres_ordre": resultat,
        "timestamp": datetime.now().isoformat()
    }
