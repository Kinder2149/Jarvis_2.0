"""
Script standalone d'ingestion des règles WFDF d'Ultimate Frisbee 2025-2028.

Usage :
    python3 backend/scripts/ingest_disc_rules.py

Prérequis :
    pip install pdfplumber requests

Ce script :
1. Télécharge le PDF WFDF 2025-2028 depuis le site officiel
2. Parse la structure hiérarchique des articles
3. Insère ou met à jour disc_rules en base
4. Loggue les articles importés
"""

import re
import sys
import json
import logging
import sqlite3
from pathlib import Path

# Ajouter la racine du projet au sys.path pour les imports backend
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PDF_URL = "https://rules.wfdf.sport/wp-content/uploads/2024/12/WFDF-Rules-of-Ultimate-2025-2028.pdf"
PDF_CACHE = Path(__file__).parent / "wfdf_rules_2025_2028.pdf"
DB_PATH = Path(__file__).parent.parent / "data" / "jarvis.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ingest_disc")

# Mapping catégories par mots-clés du titre
_CATEGORY_MAP = [
    (["spirit", "esprit"], "spirit"),
    (["field", "terrain", "equipment", "équipement"], "field"),
    (["definition", "définition", "possession", "turnover", "live", "dead"], "definitions"),
    (["stall", "count", "décompte"], "stall"),
    (["foul", "faute", "contact"], "fouls"),
    (["violation", "travel", "double team", "pick", "disc space"], "violations"),
    (["scor", "point", "goal", "but", "end zone"], "scoring"),
    (["out of bound", "hors", "limit", "obb", "oob"], "out_of_bounds"),
    (["restart", "reprise", "brick", "pull", "pull-off"], "restart"),
    (["timeout", "time-out", "pause", "blessure", "injury"], "timeouts"),
    (["official", "arbitr", "observ"], "officiating"),
]

_ARTICLE_RE = re.compile(
    r'^(\d+(?:\.\d+)*(?:\.[A-Z])?)\s+(.+?)$',
    re.MULTILINE
)

_SECTION_HEADER_RE = re.compile(
    r'^(\d+(?:\.\d+)*(?:\.[A-Z])?)\s*[.:]?\s*(.{5,80})$'
)


def download_pdf() -> Path:
    """Télécharge le PDF si absent du cache local."""
    if PDF_CACHE.exists():
        logger.info(f"PDF déjà en cache : {PDF_CACHE}")
        return PDF_CACHE

    try:
        import requests
    except ImportError:
        logger.error("Module 'requests' manquant. Installe-le : pip install requests")
        sys.exit(1)

    logger.info(f"Téléchargement du PDF depuis {PDF_URL} ...")
    r = requests.get(PDF_URL, timeout=30, stream=True)
    r.raise_for_status()
    PDF_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(PDF_CACHE, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f"PDF sauvegardé : {PDF_CACHE} ({PDF_CACHE.stat().st_size // 1024} Ko)")
    return PDF_CACHE


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrait le texte brut du PDF avec pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.error("Module 'pdfplumber' manquant. Installe-le : pip install pdfplumber")
        sys.exit(1)

    logger.info("Extraction du texte PDF ...")
    pages_text = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
        logger.info(f"  {len(pdf.pages)} pages extraites, {len(pages_text)} avec contenu")
    return "\n".join(pages_text)


def parse_articles(raw_text: str) -> list[dict]:
    """
    Parse la structure hiérarchique des articles WFDF.
    Retourne une liste de dicts prêts pour insertion en DB.
    """
    lines = raw_text.split("\n")
    articles = []
    current_article = None
    current_lines = []

    # Patterns d'articles WFDF : "1.", "1.1", "1.1.A", "14.1.1" etc.
    article_start = re.compile(
        r'^(\d{1,2}(?:\.\d{1,2})*(?:\.[A-Z])?)\s{1,4}(.{3,})'
    )

    for line in lines:
        line = line.strip()
        if not line:
            if current_lines:
                current_lines.append("")
            continue

        match = article_start.match(line)
        if match:
            # Sauvegarder l'article précédent
            if current_article and current_lines:
                contenu = " ".join(l for l in current_lines if l).strip()
                if len(contenu) > 20:
                    current_article["contenu"] = contenu
                    articles.append(current_article)

            article_num = match.group(1)
            titre = match.group(2).strip()

            # Calculer parent_article
            parts = article_num.split(".")
            parent = ".".join(parts[:-1]) if len(parts) > 1 else None

            # Détecter la catégorie
            categorie = _detect_category(article_num, titre)

            current_article = {
                "article": article_num,
                "parent_article": parent,
                "titre": titre[:200],
                "contenu": "",
                "categorie": categorie,
                "mots_cles": json.dumps(_extract_keywords(titre), ensure_ascii=False),
                "cross_refs": "[]",
            }
            current_lines = []
        else:
            if current_article:
                current_lines.append(line)

    # Dernier article
    if current_article and current_lines:
        contenu = " ".join(l for l in current_lines if l).strip()
        if len(contenu) > 20:
            current_article["contenu"] = contenu
            articles.append(current_article)

    # Post-traitement : ajouter cross_refs basiques
    article_nums = {a["article"] for a in articles}
    for art in articles:
        refs = _find_cross_refs(art["contenu"], article_nums)
        art["cross_refs"] = json.dumps(refs, ensure_ascii=False)

    logger.info(f"  {len(articles)} articles parsés")
    return articles


def _detect_category(article_num: str, titre: str) -> str:
    """Détecte la catégorie d'un article depuis son titre."""
    text = (article_num + " " + titre).lower()
    for keywords, categorie in _CATEGORY_MAP:
        if any(kw in text for kw in keywords):
            return categorie
    # Fallback par numéro d'article (approximatif WFDF 2025-2028)
    top = int(article_num.split(".")[0]) if article_num[0].isdigit() else 0
    fallback = {
        1: "spirit", 2: "definitions", 3: "field", 4: "field",
        5: "field", 6: "restart", 7: "restart", 8: "restart",
        9: "stall", 10: "out_of_bounds", 11: "out_of_bounds",
        12: "possession", 13: "scoring", 14: "fouls",
        15: "violations", 16: "timeouts", 17: "officiating",
    }
    return fallback.get(top, "definitions")


def _extract_keywords(titre: str) -> list[str]:
    """Extrait des mots-clés depuis le titre."""
    stop = {"the", "a", "an", "of", "in", "to", "and", "or", "is", "are",
            "le", "la", "les", "un", "une", "de", "du", "et", "ou", "est"}
    words = re.findall(r'\w+', titre.lower())
    return [w for w in words if len(w) > 3 and w not in stop][:8]


def _find_cross_refs(contenu: str, all_articles: set) -> list[str]:
    """Détecte les références croisées vers d'autres articles dans le contenu."""
    refs = []
    for match in re.finditer(r'\b(\d{1,2}(?:\.\d{1,2})*(?:\.[A-Z])?)\b', contenu):
        num = match.group(1)
        if num in all_articles:
            refs.append(num)
    return list(set(refs))[:10]


def upsert_to_db(articles: list[dict]) -> int:
    """Insère ou met à jour les articles dans disc_rules. Retourne le nombre d'articles traités."""
    if not articles:
        logger.warning("Aucun article à insérer.")
        return 0

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    inserted = 0
    updated = 0

    for art in articles:
        cursor.execute("SELECT id FROM disc_rules WHERE article = ?", (art["article"],))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE disc_rules
                SET parent_article = ?, titre = ?, contenu = ?, categorie = ?,
                    mots_cles = ?, cross_refs = ?
                WHERE article = ?
            """, (
                art["parent_article"], art["titre"], art["contenu"],
                art["categorie"], art["mots_cles"], art["cross_refs"],
                art["article"]
            ))
            updated += 1
        else:
            cursor.execute("""
                INSERT INTO disc_rules
                    (article, parent_article, titre, contenu, categorie, mots_cles, cross_refs)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                art["article"], art["parent_article"], art["titre"],
                art["contenu"], art["categorie"], art["mots_cles"], art["cross_refs"]
            ))
            inserted += 1

    conn.commit()
    conn.close()
    logger.info(f"DB mise à jour : {inserted} insertions, {updated} mises à jour")
    return inserted + updated


def main():
    logger.info("=== Ingestion DISC Rules WFDF 2025-2028 ===")

    if not DB_PATH.exists():
        logger.error(f"Base de données introuvable : {DB_PATH}")
        logger.error("Lance d'abord le serveur JARVIS pour initialiser la DB.")
        sys.exit(1)

    pdf_path = download_pdf()
    raw_text = extract_text_from_pdf(pdf_path)

    if len(raw_text) < 1000:
        logger.error("Extraction PDF trop courte — le PDF est peut-être protégé ou vide.")
        sys.exit(1)

    articles = parse_articles(raw_text)

    if not articles:
        logger.error("Aucun article parsé. Vérifie le format du PDF.")
        sys.exit(1)

    total = upsert_to_db(articles)
    logger.info(f"=== Ingestion terminée : {total} règles en base ===")

    # Afficher un résumé par catégorie
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT categorie, COUNT(*) as n FROM disc_rules GROUP BY categorie ORDER BY n DESC")
    rows = cur.fetchall()
    conn.close()
    logger.info("Résumé par catégorie :")
    for row in rows:
        logger.info(f"  {row['categorie']:20s} : {row['n']} règles")


if __name__ == "__main__":
    main()
