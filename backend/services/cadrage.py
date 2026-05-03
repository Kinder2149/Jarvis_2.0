import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger("jarvis")


def _get_methodo_path(db: sqlite3.Connection) -> Path | None:
    """Lit le chemin METHODO depuis config.json (chat.methodo_path).
    Fallback : backend/data/methodo/ si non configuré.
    Retourne None si aucun chemin valide."""
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


def check_cadrage_health(project_id: int, db_conn: sqlite3.Connection) -> dict:
    """
    Vérifie la santé du cadrage pour un projet donné.
    Retourne un dict avec verdict_global et liste de checks.
    
    Spec: SPEC_MODULE_REFLEXION.md §3
    """
    cursor = db_conn.cursor()
    
    # Récupérer le projet
    cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
    project_row = cursor.fetchone()
    if not project_row:
        return {
            "verdict_global": "rouge",
            "checks": [{"nom": "projet", "statut": "rouge", "message": "Projet introuvable"}]
        }
    
    project_path = Path(project_row["path"])
    checks = []
    
    # Check 1: PROJET_CONTEXTE.md lu et parsé
    projet_contexte_path = project_path / "PROJET_CONTEXTE.md"
    if projet_contexte_path.exists():
        try:
            content = projet_contexte_path.read_text(encoding="utf-8")
            checks.append({
                "nom": "PROJET_CONTEXTE.md",
                "statut": "vert",
                "message": f"Trouvé ({len(content)} caractères)"
            })
            projet_contexte_content = content
        except Exception as e:
            checks.append({
                "nom": "PROJET_CONTEXTE.md",
                "statut": "rouge",
                "message": f"Erreur lecture: {str(e)}"
            })
            projet_contexte_content = None
    else:
        checks.append({
            "nom": "PROJET_CONTEXTE.md",
            "statut": "rouge",
            "message": "Fichier absent"
        })
        projet_contexte_content = None
    
    # Check 2: graphify-out/GRAPH_REPORT.md présent
    graphify_path = project_path / "graphify-out" / "GRAPH_REPORT.md"
    if graphify_path.exists():
        try:
            content = graphify_path.read_text(encoding="utf-8")
            # Extraire nombre de nodes si possible
            nodes_count = "?"
            for line in content.split("\n")[:20]:
                if "nodes" in line.lower():
                    import re
                    match = re.search(r'(\d+)\s+nodes', line, re.IGNORECASE)
                    if match:
                        nodes_count = match.group(1)
                        break
            checks.append({
                "nom": "Graphify",
                "statut": "vert",
                "message": f"Présent ({nodes_count} nodes)"
            })
        except Exception:
            checks.append({
                "nom": "Graphify",
                "statut": "orange",
                "message": "Présent mais illisible"
            })
    else:
        checks.append({
            "nom": "Graphify",
            "statut": "orange",
            "message": "Absent (suggérer init graphify)"
        })
    
    # Check 3: Section 8 « Session en cours » récente
    if projet_contexte_content:
        if "## 8." in projet_contexte_content or "## 8 " in projet_contexte_content:
            # Heuristique simple: chercher "Session en cours" ou "En cours"
            if "session en cours" in projet_contexte_content.lower():
                checks.append({
                    "nom": "Section 8",
                    "statut": "vert",
                    "message": "Section présente"
                })
            else:
                checks.append({
                    "nom": "Section 8",
                    "statut": "orange",
                    "message": "Section présente mais potentiellement obsolète"
                })
        else:
            checks.append({
                "nom": "Section 8",
                "statut": "orange",
                "message": "Section 8 non trouvée"
            })
    else:
        checks.append({
            "nom": "Section 8",
            "statut": "rouge",
            "message": "PROJET_CONTEXTE absent"
        })
    
    # Check 4: Décisions figées section 6 vs code (heuristique simple)
    if projet_contexte_content:
        if "## 6." in projet_contexte_content or "## 6 " in projet_contexte_content:
            # Compter les lignes de tableau (lignes commençant par |)
            section_6_lines = []
            in_section_6 = False
            for line in projet_contexte_content.split("\n"):
                if "## 6" in line:
                    in_section_6 = True
                    continue
                if in_section_6 and line.strip().startswith("##"):
                    break
                if in_section_6 and line.strip().startswith("|") and not line.strip().startswith("|---"):
                    section_6_lines.append(line)
            
            decision_count = max(0, len(section_6_lines) - 1)  # -1 pour header
            checks.append({
                "nom": "Décisions figées",
                "statut": "vert",
                "message": f"{decision_count} décisions trouvées"
            })
        else:
            checks.append({
                "nom": "Décisions figées",
                "statut": "orange",
                "message": "Section 6 non trouvée"
            })
    else:
        checks.append({
            "nom": "Décisions figées",
            "statut": "rouge",
            "message": "PROJET_CONTEXTE absent"
        })
    
    # Check 5: Fichiers .md méthode accessibles
    methodo_path = _get_methodo_path(db_conn)
    
    methodo_ok = 0
    methodo_total = 2
    
    if methodo_path:
        regles_path = methodo_path / "REGLES_GLOBALES.md"
        profil_path = methodo_path / "PROFIL_UTILISATEUR.md"
        
        if regles_path.exists():
            methodo_ok += 1
        if profil_path.exists():
            methodo_ok += 1
    
    if methodo_ok == methodo_total:
        checks.append({
            "nom": "Fichiers méthode",
            "statut": "vert",
            "message": f"{methodo_ok}/{methodo_total} accessibles"
        })
    elif methodo_ok > 0:
        checks.append({
            "nom": "Fichiers méthode",
            "statut": "orange",
            "message": f"{methodo_ok}/{methodo_total} accessibles"
        })
    else:
        checks.append({
            "nom": "Fichiers méthode",
            "statut": "rouge",
            "message": "Aucun fichier accessible"
        })
    
    # Check 6: Backlog (section 9) à jour
    if projet_contexte_content:
        if "## 9." in projet_contexte_content or "## 9 " in projet_contexte_content:
            checks.append({
                "nom": "Backlog",
                "statut": "vert",
                "message": "Section 9 présente"
            })
        else:
            checks.append({
                "nom": "Backlog",
                "statut": "orange",
                "message": "Section 9 non trouvée"
            })
    else:
        checks.append({
            "nom": "Backlog",
            "statut": "rouge",
            "message": "PROJET_CONTEXTE absent"
        })
    
    # Check 7: Fraîcheur PROJET_CONTEXTE (< 30 jours)
    if projet_contexte_path.exists():
        try:
            mtime = datetime.fromtimestamp(projet_contexte_path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days
            if age_days < 30:
                checks.append({
                    "nom": "Fraîcheur",
                    "statut": "vert",
                    "message": f"Mis à jour il y a {age_days} jours"
                })
            else:
                checks.append({
                    "nom": "Fraîcheur",
                    "statut": "orange",
                    "message": f"Mis à jour il y a {age_days} jours (> 30j)"
                })
        except Exception:
            checks.append({
                "nom": "Fraîcheur",
                "statut": "orange",
                "message": "Impossible de déterminer la date"
            })
    else:
        checks.append({
            "nom": "Fraîcheur",
            "statut": "rouge",
            "message": "PROJET_CONTEXTE absent"
        })
    
    # Verdict global
    statuts = [c["statut"] for c in checks]
    if "rouge" in statuts:
        verdict_global = "rouge"
    elif "orange" in statuts:
        verdict_global = "orange"
    else:
        verdict_global = "vert"
    
    return {
        "verdict_global": verdict_global,
        "checks": checks
    }
