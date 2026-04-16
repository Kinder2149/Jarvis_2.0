from pathlib import Path
import re
from backend.services.file_service import get_sections, list_project_files, read_file, write_file

def build_context_envelope(step_config: dict, project_path: str, previous_outputs: dict, user_input: str = "") -> dict:
    envelope = {}
    context_config = step_config.get("context_envelope", {})
    
    projet_contexte_sections = context_config.get("projet_contexte_sections", [])
    if projet_contexte_sections:
        envelope["projet_contexte"] = get_sections(project_path, projet_contexte_sections)
    else:
        envelope["projet_contexte"] = ""
    
    stack_standard = context_config.get("stack_standard", False)
    if stack_standard:
        stack_path = Path(project_path) / "STACK_STANDARD.md"
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
    
    return envelope

def inject_into_template(template: str, envelope: dict) -> str:
    result = template
    
    result = result.replace("{{projet_contexte}}", envelope.get("projet_contexte", ""))
    result = result.replace("{{stack_standard}}", envelope.get("stack_standard", ""))
    result = result.replace("{{user_input}}", envelope.get("user_input", ""))
    result = result.replace("{{file_list}}", envelope.get("file_list", ""))
    result = result.replace("{{graphify_report}}", envelope.get("graphify_report", ""))
    
    for step_name, output in envelope.get("previous_outputs", {}).items():
        result = result.replace(f"{{{{previous_output_{step_name}}}}}", output)
    
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
                pattern = r'(## 8\. SESSION EN COURS\s*\n)(.*?)(\n## 9\.)'
                replacement = r'\1\n' + output_json["section_8"] + r'\n\3'
                updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                
                if updated_content == content:
                    updated_content = content.rstrip() + "\n\n## 8. SESSION EN COURS\n\n" + output_json["section_8"] + "\n"
                
                write_file(projet_contexte_path, updated_content)
        
        if "changelog_line" in output_json:
            _append_changelog(output_json["changelog_line"], project_path)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur écriture cloture : {e}")
