from pathlib import Path
import re
from backend.services.file_service import get_sections, list_project_files, read_file, write_file

CONTEXTS_DIR = Path(__file__).parent.parent / "data" / "contexts"

def build_global_rules_context() -> str:
    """Charge profil_utilisateur et regles_globales depuis les fichiers .md.
    
    Returns:
        Contexte formaté ou "" si absent
    """
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    
    parts = []
    
    regles_file = CONTEXTS_DIR / "regles_globales.md"
    if regles_file.exists():
        try:
            regles_value = regles_file.read_text(encoding="utf-8")
            if regles_value and regles_value.strip():
                parts.append("=== RÈGLES MÉTHODE ===\n" + regles_value)
        except Exception as e:
            _logger.warning(f"Erreur lecture regles_globales.md : {e}")
    
    profil_file = CONTEXTS_DIR / "profil_utilisateur.md"
    if profil_file.exists():
        try:
            profil_value = profil_file.read_text(encoding="utf-8")
            if profil_value and profil_value.strip():
                parts.append("=== PROFIL UTILISATEUR ===\n" + profil_value)
        except Exception as e:
            _logger.warning(f"Erreur lecture profil_utilisateur.md : {e}")
    
    return "\n\n".join(parts)

async def build_context_envelope(step_config: dict, project_path: str, previous_outputs: dict, user_input: str = "", workflow_type: str = "", instructions: str = "") -> dict:
    # Branche atelier si workflow_type commence par "atelier_"
    if workflow_type and workflow_type.startswith("atelier_"):
        return await _build_atelier_context(step_config, previous_outputs, user_input)
    
    envelope = {}
    context_config = step_config.get("context_envelope", {})
    
    envelope["instructions"] = instructions
    
    # Couche globale : règles méthode
    if context_config.get("inject_global_rules", False):
        envelope["global_rules"] = build_global_rules_context()
        
        # Ajouter aussi les clés séparées pour injection dans templates
        profil_file = CONTEXTS_DIR / "profil_utilisateur.md"
        envelope["profil_utilisateur"] = profil_file.read_text(encoding="utf-8") if profil_file.exists() else ""
        
        regles_file = CONTEXTS_DIR / "regles_globales.md"
        envelope["regles_globales"] = regles_file.read_text(encoding="utf-8") if regles_file.exists() else ""
    else:
        envelope["global_rules"] = ""
        envelope["profil_utilisateur"] = ""
        envelope["regles_globales"] = ""
    
    projet_contexte_sections = context_config.get("projet_contexte_sections", [])
    if projet_contexte_sections:
        envelope["projet_contexte"] = get_sections(project_path, projet_contexte_sections)
    else:
        envelope["projet_contexte"] = ""
    
    stack_standard = context_config.get("stack_standard", False)
    if stack_standard:
        stack_path = Path(project_path) / "STACK_CODE.md"
        if stack_path.exists():
            envelope["stack_standard"] = read_file(str(stack_path))
        else:
            envelope["stack_standard"] = ""
    else:
        envelope["stack_standard"] = ""
    
    previous_steps_output = context_config.get("previous_steps_output", [])
    envelope["previous_outputs"] = {}
    for step_name in previous_steps_output:
        if step_name in previous_outputs:
            envelope["previous_outputs"][step_name] = previous_outputs[step_name]
    
    include_user_input = context_config.get("user_input", False)
    if include_user_input:
        envelope["user_input"] = user_input
    else:
        envelope["user_input"] = ""
    
    include_file_list = context_config.get("include_file_list", False)
    if include_file_list:
        files = list_project_files(project_path)
        envelope["file_list"] = "\n".join(files)
    else:
        envelope["file_list"] = ""
    
    if context_config.get("graphify_report", False):
        graphify_path = Path(project_path) / "graphify-out" / "GRAPH_REPORT.md"
        if graphify_path.exists():
            envelope["graphify_report"] = read_file(str(graphify_path))
        else:
            envelope["graphify_report"] = ""
    else:
        envelope["graphify_report"] = ""
    
    if context_config.get("read_targeted_files", False) and user_input:
        try:
            from backend.services.mission_parser import parse_mission_prompt as _parse_mission
            parsed = _parse_mission(user_input)
            files_parts = []
            for fi in parsed.get("fichiers_concernes", []):
                fpath = fi.get("path", "")
                if not fpath:
                    continue
                full = Path(project_path) / fpath.lstrip("/").lstrip("\\")
                if full.exists():
                    content = read_file(str(full))
                    files_parts.append(f"=== {fpath} ===\n{content}")
            envelope["selected_files_content"] = "\n\n".join(files_parts)
        except Exception:
            envelope["selected_files_content"] = ""
    elif context_config.get("read_selected_files", False) and "selection_fichiers" in previous_outputs:
        try:
            import json as _json_sf
            sel = _json_sf.loads(previous_outputs["selection_fichiers"])
            files_parts = []
            for fpath in sel.get("files_to_read", []):
                full = Path(project_path) / fpath.lstrip("/").lstrip("\\")
                if full.exists():
                    content = read_file(str(full))
                    files_parts.append(f"=== {fpath} ===\n{content}")
            envelope["selected_files_content"] = "\n\n".join(files_parts)
        except Exception:
            envelope["selected_files_content"] = ""
    else:
        envelope["selected_files_content"] = ""
    
    return envelope

def inject_into_template(template: str, envelope: dict) -> str:
    result = template

    # Substitution des variables Module Code (clés fixes)
    result = result.replace("{{projet_contexte}}", envelope.get("projet_contexte", ""))
    result = result.replace("{{stack_standard}}", envelope.get("stack_standard", ""))
    result = result.replace("{{user_input}}", envelope.get("user_input", ""))
    result = result.replace("{{file_list}}", envelope.get("file_list", ""))
    result = result.replace("{{graphify_report}}", envelope.get("graphify_report", ""))
    result = result.replace("{{global_rules}}", envelope.get("global_rules", ""))

    for step_name, output in envelope.get("previous_outputs", {}).items():
        result = result.replace(f"{{{{previous_output_{step_name}}}}}", output)

    # Substitution générique — couvre les workflows atelier (contexte flat)
    # et toute extension future avec des clés arbitraires
    for key, value in envelope.items():
        if isinstance(value, str):
            result = result.replace("{{" + key + "}}", value)

    # Nettoyer les variables non substituées restantes
    import re as _re
    result = _re.sub(r'\{\{[^}]+\}\}', '', result)

    return result

def _append_changelog(changelog_line: str, project_path: str):
    """Ajoute une ligne au CHANGELOG.md après l'en-tête."""
    changelog_path = str(Path(project_path) / "CHANGELOG.md")
    changelog_content = read_file(changelog_path)
    
    if not changelog_content:
        changelog_content = "# CHANGELOG\n\n| Date | Mission | Description | Fichiers |\n|------|---------|-------------|----------|\n"
    
    lines = changelog_content.split('\n')
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith('|') and 'Date' in line:
            header_end = i + 2
            break
    
    if header_end > 0:
        lines.insert(header_end, changelog_line)
        write_file(changelog_path, '\n'.join(lines))

def write_cloture_docs(output_json: dict, project_path: str) -> None:
    """Écrit PROJET_CONTEXTE.md section 8 et CHANGELOG.md après cloture.
    
    Args:
        output_json: Dict contenant 'section_8' et/ou 'changelog_line'
        project_path: Chemin absolu du projet
    """
    try:
        if "section_8" in output_json:
            projet_contexte_path = str(Path(project_path) / "PROJET_CONTEXTE.md")
            content = read_file(projet_contexte_path)
            
            if content:
                # Supprimer toute section 8 existante (de ## 8. jusqu'à ## 9. ou fin de fichier)
                content = re.sub(
                    r'\n## 8\.[^\n]*\n.*?(?=\n## 9\.|\Z)',
                    '',
                    content,
                    flags=re.DOTALL
                ).rstrip()
                
                # Insérer la nouvelle section 8 avant ## 9. si elle existe, sinon en fin de fichier
                section_9_match = re.search(r'\n## 9\.', content)
                if section_9_match:
                    insert_pos = section_9_match.start()
                    content = (
                        content[:insert_pos]
                        + "\n\n## 8. SESSION EN COURS\n\n"
                        + output_json["section_8"]
                        + "\n"
                        + content[insert_pos:]
                    )
                else:
                    content = content + "\n\n## 8. SESSION EN COURS\n\n" + output_json["section_8"] + "\n"
                
                write_file(projet_contexte_path, content)
        
        if "changelog_line" in output_json:
            _append_changelog(output_json["changelog_line"], project_path)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur écriture cloture : {e}")


async def _build_atelier_context(step_config: dict, previous_outputs: dict, user_input: str) -> dict:
    """Construit le contexte pour les workflows atelier."""
    from backend.services.atelier_service import load_resource, load_tool_spec, get_activated_tools, fetch_url
    import json

    envelope = step_config.get("context_envelope", {})
    context = {}

    # 1. Charger les fichiers ressources demandés
    for resource_name in envelope.get("atelier_resources", []):
        content = load_resource(f"{resource_name}.md")
        context[resource_name] = content

    # 2. Charger les outputs des steps précédents
    for step_name_ref in envelope.get("previous_steps_output", []):
        if step_name_ref in previous_outputs:
            context[f"{step_name_ref}_output"] = previous_outputs[step_name_ref]

    # 3. Fetch URL si demandé (step analyse_site uniquement)
    if envelope.get("fetch_url", False):
        saisie_raw = context.get("saisie_output", "{}")
        try:
            saisie_data = json.loads(saisie_raw) if isinstance(saisie_raw, str) else saisie_raw
            url = saisie_data.get("url", "")
            if url and url.strip() not in ("aucun site", "", "null"):
                site_data = await fetch_url(url)
                
                # Construire site_html avec raw_html + CSS inline + CSS externe
                site_html_parts = []
                
                # 1. Raw HTML (limité à 20000 chars)
                raw_html = site_data.get("raw_html", "")[:20000]
                if raw_html:
                    site_html_parts.append(raw_html)
                
                # 2. CSS inline
                css_inline = site_data.get("css_inline", "")
                if css_inline:
                    site_html_parts.append("\n\n--- CSS INLINE ---\n" + css_inline)
                
                # 3. CSS externe
                css_external = site_data.get("css_external", "")
                if css_external:
                    site_html_parts.append("\n\n--- CSS EXTERNE ---\n" + css_external)
                
                context["site_html"] = "".join(site_html_parts) if site_html_parts else ""
            else:
                context["site_html"] = "[Aucun site fourni — analyser uniquement les observations terrain]"
        except Exception:
            context["site_html"] = "[Erreur lors de l'extraction du site]"

    # 4. Injecter les specs des outils activés (steps génération uniquement)
    if envelope.get("inject_activated_tools", False):
        saisie_raw = context.get("saisie_output", "{}")
        try:
            saisie_data = json.loads(saisie_raw) if isinstance(saisie_raw, str) else saisie_raw
            activated = get_activated_tools(saisie_data)
            tool_specs = []
            for tool in activated:
                spec = load_tool_spec(tool)
                if spec:
                    tool_specs.append(f"=== OUTIL : {tool.upper().replace('_', ' ')} ===\n{spec}")
            context["TOOL_SPECS"] = "\n\n".join(tool_specs)
        except Exception:
            context["TOOL_SPECS"] = ""

    # 5. User input si demandé
    if envelope.get("user_input", False):
        context["user_input"] = user_input

    return context
