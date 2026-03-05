"""
Orchestration adaptative — JARVIS 2.0
Détecte les marqueurs de délégation dans les réponses de Jarvis_maitre
et sollicite les agents spécialisés (CODEUR, BASE).

Flux adaptatif :
1. Jarvis_maitre planifie et délègue via [DEMANDE_CODE_CODEUR: ...]
2. Boucle CODEUR/BASE : production itérative avec vérification
3. Jarvis_maitre valide le résultat final (max 2 relances complètes)

Garde-fous : estimation dynamique des passes, détection de stagnation,
maximum absolu de 20 passes par délégation.
"""

import logging
import math
import re
from pathlib import Path

from backend.agents.agent_factory import get_agent
from backend.models.session_state import Mode, ProjectState, SessionState
from backend.services.file_writer import parse_code_blocks, write_files_to_project
from backend.services.safety_service import SafetyService
from backend.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

# Marqueurs de délégation détectés dans les réponses de Jarvis_maitre
PATTERN_CODE = re.compile(r"\[DEMANDE_CODE_CODEUR:\s*(.*?)\]", re.DOTALL)
PATTERN_VALIDATION = re.compile(r"\[DEMANDE_VALIDATION_BASE:\s*(.*?)\]", re.DOTALL)
PATTERN_VALIDATION_VALIDATEUR = re.compile(r"\[DEMANDE_VALIDATION_VALIDATEUR:\s*(.*?)\]", re.DOTALL)


class SimpleOrchestrator:
    """
    Orchestrateur adaptatif v2.
    Détecte les marqueurs dans la réponse de Jarvis_maitre,
    sollicite les agents via une boucle itérative CODEUR/BASE,
    puis renvoie le résultat à Jarvis_maitre pour validation finale.

    Garde-fous :
    - Estimation dynamique du nombre de passes
    - Détection de stagnation (1 passe vide tolérée)
    - Maximum absolu de 20 passes par délégation
    - Maximum 2 relances complètes par Jarvis_maitre
    - Fallback : si l'agent échoue, retourne la réponse initiale
    """

    # Stockage temporaire actions bloquées (conversation_id -> action_data)
    _pending_actions = {}

    @staticmethod
    def detect_delegations(response: str) -> list[dict]:
        """
        Détecte les marqueurs de délégation dans une réponse.

        Returns:
            Liste de dicts {agent_name, instruction, marker}
        """
        delegations = []

        for match in PATTERN_CODE.finditer(response):
            delegations.append(
                {
                    "agent_name": "CODEUR",
                    "instruction": match.group(1).strip(),
                    "marker": match.group(0),
                }
            )

        for match in PATTERN_VALIDATION.finditer(response):
            delegations.append(
                {
                    "agent_name": "BASE",
                    "instruction": match.group(1).strip(),
                    "marker": match.group(0),
                }
            )

        for match in PATTERN_VALIDATION_VALIDATEUR.finditer(response):
            delegations.append(
                {
                    "agent_name": "VALIDATEUR",
                    "instruction": match.group(1).strip(),
                    "marker": match.group(0),
                }
            )

        return delegations

    # Constantes d'orchestration
    MAX_ABSOLU_PASSES = 20
    TOKENS_PAR_FICHIER = 800
    TOKENS_MAX_CODEUR = 4096
    MAX_RELANCES_MAITRE = 2
    STAGNATION_TOLERANCE = 1  # nombre de passes vides tolérées avant arrêt

    @staticmethod
    def estimate_passes(instruction: str) -> int:
        """
        Estime le nombre de passes nécessaires à partir de l'instruction.
        Compte les fichiers mentionnés et calcule le nombre de passes
        en fonction de la limite de tokens du CODEUR.

        Returns:
            Nombre de passes estimé (minimum 1)
        """
        file_patterns = re.findall(
            r"(?:^|\s|[-•])\s*(?:src/|tests/|config/)?\w+\.(?:py|txt|json|yaml|yml|toml|md|html|css|js|ts)",
            instruction,
            re.MULTILINE,
        )
        nb_fichiers = max(len(file_patterns), 1)
        passes = math.ceil(
            nb_fichiers
            * SimpleOrchestrator.TOKENS_PAR_FICHIER
            / SimpleOrchestrator.TOKENS_MAX_CODEUR
        )
        return max(passes, 1)

    @classmethod
    def compute_max_passes(cls, instruction: str) -> int:
        """
        Calcule le nombre maximum de passes autorisées.
        max_passes = min(estimation × 10, MAX_ABSOLU_PASSES)
        """
        estimated = cls.estimate_passes(instruction)
        computed = min(estimated * 10, cls.MAX_ABSOLU_PASSES)
        logger.info(
            "Orchestration: estimation %d fichier(s) → %d passes estimées → max %d passes",
            estimated,
            estimated,
            computed,
        )
        return computed

    @staticmethod
    def _extract_expected_files(instruction: str) -> list[str]:
        """
        Extrait les fichiers attendus depuis l'instruction.
        Utilise 4 stratégies pour maximiser la détection.
        """
        found = set()
        code_extensions = {
            "py",
            "txt",
            "json",
            "toml",
            "yaml",
            "yml",
            "cfg",
            "js",
            "ts",
            "html",
            "css",
        }

        # Stratégie 1 : Pattern général (existant)
        general_pattern = r"(?<!\w)([\w/\\]+\.(" + "|".join(code_extensions) + r"))(?!\w)"
        for match in re.finditer(general_pattern, instruction):
            path = match.group(1).replace("\\", "/")
            found.add(path)

        # Stratégie 2 : Détection listes explicites
        # "Fichiers à créer : src/api.py, src/models.py"
        list_pattern = r"(?:fichiers?|files?|créer|create|générer|generate)[:\s]+([^\n]+)"
        for match in re.finditer(list_pattern, instruction, re.IGNORECASE):
            items = match.group(1).split(",")
            for item in items:
                item = item.strip()
                if "." in item and any(item.endswith(f".{ext}") for ext in code_extensions):
                    found.add(item.replace("\\", "/"))

        # Stratégie 3 : Détection structure arborescence
        # "src/\n  api.py\n  models.py"
        tree_pattern = r"^\s*[\-\*]\s*([\w/\\]+\.(" + "|".join(code_extensions) + r"))"
        for match in re.finditer(tree_pattern, instruction, re.MULTILINE):
            path = match.group(1).replace("\\", "/")
            found.add(path)

        # Stratégie 4 : Détection mentions markdown
        # "`src/api.py`" ou "**src/models.py**"
        markdown_pattern = r"[`*]+([\w/\\]+\.(" + "|".join(code_extensions) + r"))[`*]+"
        for match in re.finditer(markdown_pattern, instruction):
            path = match.group(1).replace("\\", "/")
            found.add(path)

        result = sorted(found)
        logger.info(f"Extraction fichiers : {len(result)} fichiers détectés via 4 stratégies")
        return result

    @staticmethod
    async def _verify_completeness(
        instruction: str,
        codeur_result: str,
        files_written: list[dict],
        session_id: str | None = None,
    ) -> dict:
        """
        Vérifie si le CODEUR a produit tous les fichiers demandés.
        Utilise un comptage local d'abord, puis BASE en fallback.

        Returns:
            Dict {complete: bool, missing: str}
        """
        written_paths = [f["path"] for f in files_written if f["status"] == "written"]
        written_normalized = [p.replace("\\", "/") for p in written_paths]
        written_basenames = {p.split("/")[-1] for p in written_normalized}

        expected = SimpleOrchestrator._extract_expected_files(instruction)
        if expected:
            missing_local = []
            for exp in expected:
                exp_basename = exp.split("/")[-1]
                exp_normalized = exp.replace("\\", "/")

                # Validation locale renforcée : 3 types de matching
                matched = (
                    exp_normalized in written_normalized  # Chemin complet exact
                    or exp_basename in written_basenames  # Nom de fichier seul
                    or any(wp.endswith(exp_basename) for wp in written_normalized)  # Fin de chemin
                )

                if not matched:
                    missing_local.append(exp)

            if missing_local:
                missing_str = "INCOMPLET: " + ", ".join(missing_local)
                logger.info(
                    "Orchestration: comptage local → %d/%d fichiers, manquants: %s",
                    len(expected) - len(missing_local),
                    len(expected),
                    ", ".join(missing_local),
                )
                return {"complete": False, "missing": missing_str}

            logger.info(
                "Orchestration: comptage local → %d/%d fichiers, tous présents",
                len(written_paths),
                len(expected),
            )
            return {"complete": True, "missing": ""}

        verification_prompt = (
            "VÉRIFICATION DE COMPLÉTUDE — PROCÉDURE OBLIGATOIRE\n\n"
            "**Instruction originale** :\n"
            f"{instruction}\n\n"
            f"**Fichiers écrits sur le disque ({len(written_paths)})** :\n"
            + (
                "\n".join(f"- {p}" for p in written_paths)
                if written_paths
                else "- Aucun fichier écrit"
            )
            + "\n\n"
            "**PROCÉDURE EN 4 ÉTAPES (OBLIGATOIRE)** :\n\n"
            "1. EXTRACTION : Liste TOUS les fichiers mentionnés dans l'instruction (un par ligne)\n"
            "   Format : - fichier1.py\n"
            "            - fichier2.py\n\n"
            "2. COMPARAISON : Pour chaque fichier extrait, vérifie s'il est dans la liste des fichiers écrits\n"
            "   Accepte les variations : src/api.py == api.py (même nom de fichier)\n\n"
            "3. COMPTAGE : X fichiers demandés, Y fichiers écrits\n\n"
            "4. DÉCISION :\n"
            "   - Si X == Y et tous les fichiers correspondent → réponds : COMPLET\n"
            "   - Si X > Y ou des fichiers manquent → réponds : INCOMPLET: fichier1.py, fichier2.py\n\n"
            "**IMPORTANT** : Sois strict mais intelligent. Si l'instruction dit 'src/api.py' et le fichier écrit est 'api.py', c'est OK (même nom).\n"
            "Si tu as un doute, considère INCOMPLET."
        )

        try:
            base_agent = get_agent("BASE")
            messages = [{"role": "user", "content": verification_prompt}]
            base_response = await base_agent.handle(messages, session_id=session_id)

            logger.info("Orchestration: BASE vérification → %s", base_response[:100])

            if "COMPLET" in base_response and "INCOMPLET" not in base_response:
                return {"complete": True, "missing": ""}
            else:
                return {"complete": False, "missing": base_response}

        except Exception:
            logger.exception("Orchestration: échec vérification BASE")
            return {"complete": True, "missing": ""}

    @staticmethod
    async def _request_completion(
        original_instruction: str,
        missing_info: str,
        previous_result: str,
        session_id: str | None = None,
    ) -> str:
        """
        Relance le CODEUR pour compléter les fichiers manquants.

        Returns:
            Réponse du CODEUR (complétion)
        """
        completion_prompt = (
            "Tu as déjà produit une partie du code demandé. "
            "Il manque des fichiers. Produis UNIQUEMENT les fichiers manquants.\n\n"
            f"**Instruction originale** :\n{original_instruction}\n\n"
            f"**Fichiers manquants selon la vérification** :\n{missing_info}\n\n"
            "Produis chaque fichier manquant avec le format :\n"
            "# chemin/vers/fichier.ext\n"
            "```langage\n"
            "code complet du fichier\n"
            "```"
        )

        codeur = get_agent("CODEUR")
        messages = [{"role": "user", "content": completion_prompt}]
        return await codeur.handle(messages, session_id=session_id)

    @staticmethod
    def _read_project_files(
        project_path: str,
        files_written: list[dict],
        max_lines: int = 200,
    ) -> dict[str, str]:
        """
        Lit le contenu réel des fichiers source écrits sur le disque.
        Filtre les fichiers .py, .js, .ts, .html, .css uniquement.
        Tronque à max_lines lignes par fichier.

        Args:
            project_path: Chemin absolu du projet
            files_written: Liste de dicts {path, status, size}
            max_lines: Nombre max de lignes par fichier

        Returns:
            Dict {chemin_relatif: contenu} pour chaque fichier lu
        """
        readable_extensions = {".py", ".js", ".ts", ".html", ".css"}
        file_contents = {}

        for file_info in files_written:
            if file_info.get("status") != "written":
                continue

            rel_path = file_info["path"]
            suffix = Path(rel_path).suffix.lower()
            if suffix not in readable_extensions:
                continue

            abs_path = Path(project_path) / rel_path
            try:
                if abs_path.exists() and abs_path.is_file():
                    content = abs_path.read_text(encoding="utf-8")
                    lines = content.splitlines()
                    if len(lines) > max_lines:
                        content = "\n".join(lines[:max_lines])
                        content += f"\n# ... tronqué ({len(lines)} lignes total)"
                    file_contents[rel_path] = content
            except Exception:
                logger.warning("Orchestration: impossible de lire %s", abs_path)

        return file_contents

    @staticmethod
    async def _build_code_report(
        file_contents: dict[str, str],
        session_id: str | None = None,
    ) -> str:
        """
        Demande à BASE d'analyser les fichiers produits et de générer
        un rapport structuré (classes, fonctions, signatures, imports, routes).

        Ce rapport sera inclus dans le followup envoyé à Jarvis_maitre
        pour qu'il puisse donner des instructions précises au CODEUR
        lors des étapes suivantes.

        Args:
            file_contents: Dict {chemin_relatif: contenu} des fichiers lus
            session_id: ID de session pour traçabilité

        Returns:
            Rapport structuré (string) ou chaîne vide si échec
        """
        if not file_contents:
            return ""

        files_text = ""
        for path, content in file_contents.items():
            files_text += f"\n### {path}\n```\n{content}\n```\n"

        report_prompt = (
            "Analyse ces fichiers et produis un RAPPORT STRUCTURÉ.\n"
            "Pour chaque fichier, liste :\n"
            "- Chemin du fichier\n"
            "- Classes (nom + méthodes avec signatures)\n"
            "- Fonctions libres (nom + signatures)\n"
            "- Imports\n"
            "- Routes API (si FastAPI/Flask)\n"
            "- Dépendances externes (pip)\n\n"
            "Format OBLIGATOIRE :\n"
            "## chemin/fichier.py\n"
            "- Classes : ClassName(method1(args), method2(args))\n"
            "- Fonctions : func_name(args) -> return_type\n"
            "- Imports : module1, module2\n"
            "- Routes : GET /path, POST /path\n\n"
            "Sois CONCIS. Pas de code, pas d'explication. Juste le rapport.\n\n"
            f"--- FICHIERS À ANALYSER ---\n{files_text}"
        )

        try:
            base_agent = get_agent("BASE")
            messages = [{"role": "user", "content": report_prompt}]
            report = await base_agent.handle(messages, session_id=session_id)

            logger.info(
                "Orchestration: rapport BASE généré (%d chars)",
                len(report),
            )
            return report

        except Exception:
            logger.exception("Orchestration: échec génération rapport BASE")
            return ""

    async def execute_delegation(
        self,
        delegation: dict,
        session_id: str | None = None,
        project_path: str | None = None,
        user_prompt: str | None = None,
        function_executor=None,
        session_state=None,
    ) -> dict:
        """
        Exécute une délégation vers un agent.
        Si l'agent est CODEUR et project_path est fourni :
        1. Estime le nombre de passes nécessaires
        2. Boucle itérative CODEUR/BASE avec détection de stagnation
        3. Retourne le bilan complet

        Returns:
            Dict {agent_name, instruction, result, success, files_written,
                  passes_used, stagnation}
        """
        agent_name = delegation["agent_name"]
        instruction = delegation["instruction"]

        try:
            # 🔥 ENRICHISSEMENT RAG : Si CODEUR, enrichir l'instruction avec contexte Library
            if agent_name == "CODEUR":
                try:
                    rag_service = get_rag_service()
                    # Vérifier si l'API RAG est disponible
                    is_available = await rag_service.check_health()
                    if is_available:
                        logger.info("Orchestration: enrichissement RAG activé pour CODEUR")
                        instruction = await rag_service.enrich_instruction(
                            instruction,
                            n_results=3,  # Top 3 documents pertinents
                            filter_metadata={"agent": "CODEUR"}  # Filtrer sur agent CODEUR si disponible
                        )
                        logger.info("Orchestration: instruction CODEUR enrichie avec RAG")
                    else:
                        logger.warning("Orchestration: API RAG non disponible, instruction non enrichie")
                except Exception as e:
                    logger.warning(f"Orchestration: erreur enrichissement RAG: {e}")
                    # Continuer sans enrichissement en cas d'erreur
            
            agent = get_agent(agent_name)
            messages = [{"role": "user", "content": instruction}]
            result = await agent.handle(
                messages, session_id=session_id, function_executor=function_executor
            )

            logger.info("Orchestration: %s a répondu (%d chars)", agent_name, len(result))

            # Si CODEUR + projet : boucle adaptative CODEUR/BASE
            files_written = []
            passes_used = 1
            stagnation = False

            if agent_name == "CODEUR" and project_path:
                # 🔥 CRITIQUE : Passer en phase EXECUTION pour autoriser écriture disque
                if session_state and session_state.phase.value == "reflexion":
                    try:
                        session_state.transition_to_execution()
                        logger.info("Orchestration: transition phase REFLEXION → EXECUTION pour CODEUR")
                    except Exception as e:
                        logger.warning("Orchestration: échec transition phase: %s", str(e))
                
                # Combiner instruction du marqueur + prompt user pour extraire les fichiers
                combined_instruction = instruction
                if user_prompt:
                    combined_instruction = user_prompt + "\n\n" + instruction
                expected_files = self._extract_expected_files(combined_instruction)
                logger.info(
                    "Orchestration: instruction CODEUR (%d chars), fichiers attendus extraits: %s",
                    len(instruction),
                    expected_files or "(aucun — fallback BASE)",
                )
                max_passes = self.compute_max_passes(instruction)
                empty_passes = 0

                # Passe 1 : écriture initiale
                code_blocks = parse_code_blocks(result)
                if code_blocks:
                    files_written = write_files_to_project(project_path, code_blocks, session_state)
                written_count = sum(1 for f in files_written if f["status"] == "written")
                logger.info(
                    "Orchestration: passe 1 — %d fichier(s) écrit(s) dans %s",
                    written_count,
                    project_path,
                )

                # Boucle de vérification adaptative
                for pass_num in range(2, max_passes + 1):
                    verification = await self._verify_completeness(
                        combined_instruction,
                        result,
                        files_written,
                        session_id=session_id,
                    )

                    if verification["complete"]:
                        logger.info(
                            "Orchestration: vérification OK après %d passe(s)",
                            pass_num - 1,
                        )
                        break

                    logger.info(
                        "Orchestration: passe %d/%d — fichiers manquants détectés",
                        pass_num,
                        max_passes,
                    )

                    try:
                        completion_result = await self._request_completion(
                            instruction,
                            verification["missing"],
                            result,
                            session_id=session_id,
                        )
                        result += "\n\n" + completion_result

                        extra_blocks = parse_code_blocks(completion_result)
                        extra_count = 0
                        if extra_blocks:
                            extra_written = write_files_to_project(
                                project_path, extra_blocks, session_state
                            )
                            files_written.extend(extra_written)
                            extra_count = sum(1 for f in extra_written if f["status"] == "written")

                        passes_used = pass_num

                        # Détection de stagnation
                        if extra_count == 0:
                            empty_passes += 1
                            logger.warning(
                                "Orchestration: passe %d — 0 nouveau fichier (stagnation %d/%d)",
                                pass_num,
                                empty_passes,
                                self.STAGNATION_TOLERANCE + 1,
                            )
                            if empty_passes > self.STAGNATION_TOLERANCE:
                                logger.warning("Orchestration: stagnation détectée — arrêt")
                                stagnation = True
                                break
                        else:
                            empty_passes = 0
                            logger.info(
                                "Orchestration: passe %d — %d fichier(s) supplémentaire(s)",
                                pass_num,
                                extra_count,
                            )

                    except Exception:
                        logger.exception(
                            "Orchestration: échec complétion passe %d",
                            pass_num,
                        )
                        break

            # Validation automatique par VALIDATEUR après génération de code
            validation_result = None
            if agent_name == "CODEUR" and files_written and project_path:
                try:
                    # Lire fichiers écrits pour validation
                    file_contents = self._read_project_files(project_path, files_written)

                    if file_contents:
                        # Construire prompt validation
                        validation_prompt = "Vérifie ce code produit par le CODEUR :\n\n"
                        for path, content in file_contents.items():
                            validation_prompt += f"# {path}\n```\n{content}\n```\n\n"

                        # Appeler VALIDATEUR
                        validateur = get_agent("VALIDATEUR")
                        validation_result = await validateur.handle(
                            [{"role": "user", "content": validation_prompt}], session_id=session_id
                        )

                        logger.info("Orchestration: VALIDATEUR → %s", validation_result[:100])

                        # Si INVALIDE et passes restantes, relancer CODEUR avec corrections
                        if "INVALIDE" in validation_result and passes_used < max_passes:
                            logger.warning(
                                "Orchestration: VALIDATEUR a détecté des problèmes, relance CODEUR pour correction"
                            )

                            # Extraire recommandations du rapport VALIDATEUR
                            correction_prompt = (
                                f"Le VALIDATEUR a détecté des problèmes dans ton code. Corrige-les.\n\n"
                                f"RAPPORT VALIDATEUR :\n{validation_result}\n\n"
                                f"INSTRUCTION ORIGINALE :\n{instruction}\n\n"
                                "Régénère UNIQUEMENT les fichiers avec problèmes. Respecte le format de sortie."
                            )

                            # Relancer CODEUR
                            result = await agent.handle(
                                [{"role": "user", "content": correction_prompt}],
                                session_id=session_id,
                            )
                            passes_used += 1

                            # Parser et écrire fichiers corrigés
                            parsed = parse_code_blocks(result)
                            if parsed and project_path:
                                corrected_files = write_files_to_project(
                                    project_path, parsed, session_state
                                )
                                files_written.extend(corrected_files)
                                logger.info(
                                    "Orchestration: CODEUR correction → %d fichiers corrigés",
                                    len(corrected_files),
                                )
                        elif "INVALIDE" in validation_result:
                            logger.warning(
                                "Orchestration: VALIDATEUR a détecté des problèmes mais max passes atteint"
                            )

                except Exception:
                    logger.exception("Orchestration: échec validation VALIDATEUR")

            return {
                "agent_name": agent_name,
                "instruction": instruction,
                "result": result,
                "success": True,
                "files_written": files_written,
                "passes_used": passes_used,
                "stagnation": stagnation,
                "validation": validation_result,
            }

        except Exception as e:
            logger.exception("Orchestration: échec appel %s", agent_name)
            return {
                "agent_name": agent_name,
                "instruction": instruction,
                "result": f"[Erreur: {agent_name} n'a pas pu répondre — {e}]",
                "success": False,
                "files_written": [],
                "passes_used": 0,
                "stagnation": False,
                "validation": None,
            }

    @staticmethod
    def build_followup_message(
        original_response: str,
        delegation_results: list[dict],
        code_report: str = "",
    ) -> str:
        """
        Construit le message de suivi envoyé à Jarvis_maitre (VERSION COMPACTE).
        Réduit de 70% la taille pour éviter les timeouts.
        Inclut les erreurs critiques pour remontée à l'utilisateur.
        """
        parts = []
        errors = []  # Collecter les erreurs critiques

        for result in delegation_results:
            status = "✅" if result["success"] else "❌"
            files = result.get("files_written", [])
            written = [f for f in files if f["status"] == "written"]
            passes = result.get("passes_used", 0)
            stag = result.get("stagnation", False)
            validation = result.get("validation")

            # FORMAT ULTRA-COMPACT
            summary = f"{status} {result['agent_name']}: {len(written)} fichier(s)"
            if passes > 1:
                summary += f", {passes} passes"
            if stag:
                summary += " ⚠️ stagnation"

            # Erreur critique : aucun fichier généré
            if not result["success"]:
                errors.append(
                    f"❌ {result['agent_name']} a échoué : {result.get('result', 'Erreur inconnue')[:100]}"
                )
            elif len(written) == 0 and result["agent_name"] == "CODEUR":
                errors.append("⚠️ CODEUR n'a généré AUCUN fichier (parsing échoué ?)")

            # Erreur validation VALIDATEUR
            if validation and "INVALIDE" in validation:
                errors.append("⚠️ VALIDATEUR a détecté des problèmes dans le code")

            parts.append(summary)

            # Liste fichiers (noms seulement, pas de tailles)
            if written:
                file_list = ", ".join(f["path"] for f in written[:5])  # Max 5 fichiers
                if len(written) > 5:
                    file_list += f" (+{len(written) - 5} autres)"
                parts.append(f"  Fichiers: {file_list}")

        # Rapport BASE ultra-compact (500 chars max)
        if code_report:
            # Extraire seulement les noms de classes/fonctions
            compact_report = []
            for line in code_report.split("\n"):
                if (
                    line.startswith("## ")
                    or line.startswith("- Classes:")
                    or line.startswith("- Fonctions:")
                ):
                    compact_report.append(line[:100])  # Tronquer à 100 chars

            report_text = "\n".join(compact_report[:10])  # Max 10 lignes
            if len(report_text) > 500:
                report_text = report_text[:500] + "..."

            parts.append(f"\n📋 Structure: {len(compact_report)} éléments")
            parts.append(report_text)

        # Remonter les erreurs critiques en priorité
        if errors:
            parts.insert(0, "⚠️ ERREURS CRITIQUES DÉTECTÉES :")
            for error in errors:
                parts.insert(1, f"  {error}")
            parts.insert(len(errors) + 1, "")

        parts.append(
            "\n---\n"
            "Analyse résultats. Si complet, réponds à l'utilisateur. "
            "Si incomplet ou erreurs, indique ce qui manque/a échoué."
        )

        return "\n".join(parts)

    async def process_response(
        self,
        response: str,
        conversation_history: list[dict],
        session_id: str | None = None,
        project_path: str | None = None,
        function_executor=None,
        session_state: SessionState | None = None,
    ) -> tuple[str, list[dict]]:
        """
        Traite la réponse de Jarvis_maitre :
        1. Détecte les marqueurs de délégation
        2. Exécute les délégations (boucle adaptative CODEUR/BASE)
        3. Renvoie le bilan à Jarvis_maitre pour validation finale
        4. Si Jarvis_maitre relance une délégation, reboucle (max 2 relances)

        Args:
            response: Réponse initiale de Jarvis_maitre
            conversation_history: Historique de la conversation
            session_id: ID de session pour traçabilité
            project_path: Chemin du projet pour écriture fichiers
            function_executor: Executor pour les function calls

        Returns:
            (réponse_finale, all_delegation_results)
            Si aucune délégation détectée, retourne (response, [])
        """
        all_delegation_results = []
        current_response = response
        running_history = list(conversation_history)

        # Concaténer tous les messages user pour enrichir la vérification
        # Le prompt initial (avec les chemins de fichiers) n'est pas forcément le dernier
        user_messages = [
            msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"
        ]
        user_prompt = "\n\n".join(user_messages) if user_messages else None

        for relance_num in range(self.MAX_RELANCES_MAITRE + 1):
            delegations = self.detect_delegations(current_response)

            if not delegations:
                if relance_num == 0:
                    return current_response, []
                break

            logger.info(
                "Orchestration: %s%d délégation(s) détectée(s)",
                f"relance {relance_num} — " if relance_num > 0 else "",
                len(delegations),
            )

            # Classification SAFE/NON-SAFE avant délégation
            # Vérifier si action confirmée (bypass safety check)
            bypass_safety = SimpleOrchestrator._pending_actions.get(session_id, {}).get(
                "confirmed", False
            )

            if (
                session_state
                and session_state.mode == Mode.PROJECT
                and delegations
                and not bypass_safety
            ):
                user_message = conversation_history[-1]["content"] if conversation_history else ""
                classification = SafetyService.classify_action(
                    user_message,
                    session_state.project_state or ProjectState.NEW,
                    session_state.phase.value if session_state.phase else "reflexion",
                )

                # Si NON-SAFE et validation requise, stocker action et retourner challenge
                if not classification["is_safe"] and classification["requires_validation"]:
                    # Stocker action bloquée pour confirmation ultérieure
                    SimpleOrchestrator._pending_actions[session_id] = {
                        "user_message": user_message,
                        "original_response": current_response,  # Réponse IA originale avec marqueurs
                        "delegations": delegations,
                        "classification": classification,
                        "conversation_history": conversation_history,
                        "project_path": project_path,
                        "function_executor": function_executor,
                        "session_state": session_state,
                        "confirmed": False,
                    }

                    challenge = SafetyService.generate_challenge(
                        user_message, classification, session_state.project_state
                    )
                    challenge += "\n\n💡 **Pour confirmer cette action**, utilisez le bouton 'Confirmer' ou répondez 'CONFIRMER'."

                    logger.info(
                        "Orchestration: action NON-SAFE détectée, challenge généré et action stockée (%s)",
                        classification["reason"],
                    )
                    return challenge, []

            # Si bypass_safety activé, nettoyer le flag après exécution
            if bypass_safety and session_id in SimpleOrchestrator._pending_actions:
                del SimpleOrchestrator._pending_actions[session_id]
                logger.info("Orchestration: action confirmée exécutée, flag nettoyé")

            # Exécuter chaque délégation (max 1 par agent)
            seen_agents = set()
            delegation_results = []
            for delegation in delegations:
                if delegation["agent_name"] in seen_agents:
                    continue
                seen_agents.add(delegation["agent_name"])
                result = await self.execute_delegation(
                    delegation,
                    session_id=session_id,
                    project_path=project_path,
                    user_prompt=user_prompt,
                    function_executor=function_executor,
                    session_state=session_state,
                )
                delegation_results.append(result)

            all_delegation_results.extend(delegation_results)

            # Générer le rapport structuré BASE pour les délégations CODEUR
            code_report = ""
            if project_path:
                for result in delegation_results:
                    if (
                        result["agent_name"] == "CODEUR"
                        and result["success"]
                        and result.get("files_written")
                    ):
                        file_contents = self._read_project_files(
                            project_path, result["files_written"]
                        )
                        if file_contents:
                            code_report = await self._build_code_report(
                                file_contents, session_id=session_id
                            )
                        break  # 1 seul rapport par cycle de délégation

            # Construire le bilan et renvoyer à Jarvis_maitre
            followup = self.build_followup_message(
                current_response, delegation_results, code_report=code_report
            )

            try:
                maitre = get_agent("JARVIS_Maître")
                running_history += [
                    {"role": "assistant", "content": current_response},
                    {"role": "user", "content": followup},
                ]
                final_response = await maitre.handle(running_history, session_id=session_id)

                # Vérifier si Jarvis_maitre relance une délégation
                new_delegations = self.detect_delegations(final_response)
                if new_delegations and relance_num < self.MAX_RELANCES_MAITRE:
                    logger.info(
                        "Orchestration: Jarvis_maitre relance — "
                        "nouvelle délégation détectée (relance %d/%d)",
                        relance_num + 1,
                        self.MAX_RELANCES_MAITRE,
                    )
                    current_response = final_response
                    continue
                else:
                    return final_response, all_delegation_results

            except Exception:
                logger.exception(
                    "Orchestration: échec réponse Jarvis_maitre, retour réponse initiale"
                )
                return current_response, all_delegation_results

        return current_response, all_delegation_results
