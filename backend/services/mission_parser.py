"""
mission_parser.py — Parseur de prompts mission produits par Module Réflexion.
Format attendu : SPEC_MODULE_REFLEXION §6.C (sections markdown ## ).
Tolérant : sections optionnelles génèrent des warnings.
Sections obligatoires : "Objectif" et "Fichiers concernés".
"""
import re
import logging

logger = logging.getLogger("jarvis")


def parse_mission_prompt(text: str) -> dict:
    """
    Parse un prompt mission au format SPEC_MODULE_REFLEXION §6.C.

    Retourne :
    {
      "titre": str,
      "objectif": str,
      "contexte": str,
      "fichiers_concernes": [{"path": str, "role": str}],
      "contraintes": [str],
      "criteres_reussite": [str],
      "modele_recommande": str | None,
      "raw": str,
      "parse_warnings": [str]
    }

    Lève ValueError si "Objectif" ou "Fichiers concernés" sont absents/vides.
    """
    if not text or not text.strip():
        raise ValueError("Le texte de mission est vide.")

    raw = text.strip()
    warnings: list[str] = []

    # ── Titre : première ligne H1 ou H2 ou ligne de titre avant le premier ## ──
    titre = ""
    lines = raw.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            titre = stripped[2:].strip()
            break
        if stripped.startswith("## "):
            break
        if stripped and not titre:
            titre = stripped

    # ── Découper en sections par "## Nom" ──
    section_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(section_pattern.finditer(raw))

    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        sections[section_name] = raw[start:end].strip()

    # ── Normalisation des noms de sections (casse insensible) ──
    def get_section(key: str) -> str | None:
        for k, v in sections.items():
            if k.lower().startswith(key.lower()):
                return v
        return None

    # ── Objectif (obligatoire) ──
    objectif_raw = get_section("Objectif")
    if not objectif_raw:
        raise ValueError("Section '## Objectif' manquante ou vide dans le prompt mission.")
    objectif = objectif_raw.strip()

    # ── Fichiers concernés (obligatoire) ──
    fichiers_raw = get_section("Fichiers concernés") or get_section("Fichiers concernes")
    if not fichiers_raw:
        raise ValueError("Section '## Fichiers concernés' manquante ou vide dans le prompt mission.")

    fichiers_concernes = _parse_file_list(fichiers_raw)
    if not fichiers_concernes:
        raise ValueError("Section '## Fichiers concernés' présente mais vide ou non parseable.")

    # ── Contexte (optionnel) ──
    contexte_raw = get_section("Contexte")
    if not contexte_raw:
        warnings.append("Section '## Contexte' absente — contexte sera vide.")
        contexte = ""
    else:
        contexte = contexte_raw.strip()

    # ── Contraintes (optionnel) ──
    contraintes_raw = get_section("Contraintes")
    if not contraintes_raw:
        warnings.append("Section '## Contraintes' absente — liste vide.")
        contraintes: list[str] = []
    else:
        contraintes = _parse_bullet_list(contraintes_raw)

    # ── Critères de réussite (optionnel) ──
    criteres_raw = (
        get_section("Critères de réussite")
        or get_section("Criteres de reussite")
        or get_section("Critères")
    )
    if not criteres_raw:
        warnings.append("Section '## Critères de réussite' absente — liste vide.")
        criteres_reussite: list[str] = []
    else:
        criteres_reussite = _parse_bullet_list(criteres_raw)

    # ── Recommandation modèle (optionnel) ──
    modele_raw = get_section("Recommandation modèle") or get_section("Recommandation model")
    modele_recommande: str | None = None
    if modele_raw:
        modele_recommande = _extract_model_id(modele_raw)
        if not modele_recommande:
            warnings.append("Section '## Recommandation modèle' présente mais aucun identifiant de modèle détecté.")
    else:
        warnings.append("Section '## Recommandation modèle' absente — pas de recommandation modèle.")

    if warnings:
        for w in warnings:
            logger.warning(f"[MISSION_PARSER] {w}")

    return {
        "titre": titre,
        "objectif": objectif,
        "contexte": contexte,
        "fichiers_concernes": fichiers_concernes,
        "contraintes": contraintes,
        "criteres_reussite": criteres_reussite,
        "modele_recommande": modele_recommande,
        "raw": raw,
        "parse_warnings": warnings,
    }


def _parse_file_list(text: str) -> list[dict]:
    """
    Parse une liste de fichiers du format :
    - `chemin/fichier.ext` — rôle du fichier
    - chemin/fichier.ext — rôle
    """
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Supprimer le tiret de liste en début
        if line.startswith("- "):
            line = line[2:].strip()
        elif line.startswith("* "):
            line = line[2:].strip()

        # Extraire le chemin (entre backticks ou directement)
        path_match = re.match(r"`([^`]+)`", line)
        if path_match:
            path = path_match.group(1).strip()
            rest = line[path_match.end():].strip()
        else:
            # Essayer de couper sur " — " ou " - "
            sep_match = re.split(r"\s+[—–-]+\s+", line, maxsplit=1)
            if sep_match:
                path = sep_match[0].strip()
                rest = sep_match[1].strip() if len(sep_match) > 1 else ""
            else:
                path = line
                rest = ""

        if not path:
            continue

        # Extraire le rôle après — ou -
        role = ""
        role_match = re.split(r"\s+[—–-]+\s+", rest, maxsplit=1)
        if role_match and len(role_match) > 1:
            role = role_match[1].strip()
        elif rest:
            role = rest.strip()

        result.append({"path": path, "role": role})

    return result


def _parse_bullet_list(text: str) -> list[str]:
    """Parse une liste à puces ou numérotée en liste de strings."""
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Supprimer préfixes de liste
        line = re.sub(r"^[-*•]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        line = re.sub(r"^\[\s*[xX ]?\s*\]\s+", "", line)
        if line:
            result.append(line)
    return result


def _extract_model_id(text: str) -> str | None:
    """
    Extrait un identifiant de modèle du type 'provider/model-name' ou entre backticks.
    """
    # Chercher entre backticks d'abord
    backtick_match = re.search(r"`([a-zA-Z0-9/_.-]+)`", text)
    if backtick_match:
        candidate = backtick_match.group(1)
        if "/" in candidate:
            return candidate

    # Chercher un pattern provider/model
    pattern_match = re.search(r"\b(anthropic|google|openai|mistral|meta-llama)[/\-][\w._-]+", text)
    if pattern_match:
        return pattern_match.group(0)

    return None
