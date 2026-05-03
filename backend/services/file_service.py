from pathlib import Path
import difflib
import shutil
import logging

logger = logging.getLogger(__name__)

def read_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def write_file(file_path: str, content: str) -> bool:
    path = Path(file_path)
    tmp_path = path.parent / f".jarvis_tmp_{path.name}"
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(path)
        return True
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        return False

def apply_files(changes: list[dict]) -> bool:
    file_paths = []
    tmp_paths = []
    backup_paths = []
    
    # PHASE 1 — Vérification préalable (aucune écriture)
    try:
        for change in changes:
            file_path = Path(change["path"])
            
            if not file_path.name:
                raise ValueError(f"Nom de fichier invalide : {change['path']}")
            
            if ".." in file_path.parts:
                raise ValueError(f"Chemin non sécurisé : {change['path']}")
            
            parent_dir = file_path.parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise ValueError(f"Impossible de créer le dossier {parent_dir} : {e}")
            
            tmp_path = parent_dir / f".jarvis_tmp_{file_path.name}"
            
            file_paths.append(file_path)
            tmp_paths.append(tmp_path)
            
            if file_path.exists():
                backup_path = parent_dir / f".jarvis_backup_{file_path.name}"
                backup_paths.append(backup_path)
            else:
                backup_paths.append(None)
    
    except Exception as e:
        logger.error(f"Vérification échouée : {e}")
        raise Exception(f"Vérification échouée : {e}")
    
    # PHASE 2 — Écriture des fichiers temporaires
    written_tmp = []
    try:
        for i, change in enumerate(changes):
            content = change["content"]
            tmp_path = tmp_paths[i]
            
            tmp_path.write_text(content, encoding="utf-8")
            written_tmp.append(tmp_path)
            logger.info(f"Fichier tmp créé : {tmp_path}")
    
    except Exception as e:
        logger.error(f"Écriture tmp échouée : {e}")
        for tmp_path in written_tmp:
            if tmp_path.exists():
                tmp_path.unlink()
                logger.info(f"Nettoyage tmp : {tmp_path}")
        raise Exception(f"Écriture tmp échouée : {e}")
    
    # PHASE 3 — Rename atomique avec rollback si échec
    renamed_files = []
    try:
        for i, (tmp_path, file_path, backup_path) in enumerate(zip(tmp_paths, file_paths, backup_paths)):
            if backup_path and file_path.exists():
                file_path.rename(backup_path)
                logger.info(f"Backup créé : {backup_path}")
            
            tmp_path.replace(file_path)
            renamed_files.append((file_path, backup_path))
            logger.info(f"Fichier appliqué : {file_path}")
        
        for backup_path in backup_paths:
            if backup_path and backup_path.exists():
                backup_path.unlink()
                logger.info(f"Backup supprimé : {backup_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Rename échoué : {e} — Rollback en cours")
        
        for file_path, backup_path in renamed_files:
            try:
                if backup_path and backup_path.exists():
                    if file_path.exists():
                        file_path.unlink()
                    backup_path.rename(file_path)
                    logger.info(f"Rollback : {file_path} restauré depuis backup")
                elif file_path.exists():
                    file_path.unlink()
                    logger.info(f"Rollback : {file_path} supprimé (nouveau fichier)")
            except Exception as rollback_error:
                logger.error(f"Erreur rollback sur {file_path} : {rollback_error}")
        
        for tmp_path in tmp_paths:
            if tmp_path.exists():
                tmp_path.unlink()
                logger.info(f"Nettoyage tmp après rollback : {tmp_path}")
        
        for backup_path in backup_paths:
            if backup_path and backup_path.exists():
                backup_path.unlink()
                logger.info(f"Nettoyage backup après rollback : {backup_path}")
        
        raise Exception(f"Rollback effectué — aucun fichier modifié : {e}")

def compute_diff(original: str, modified: str, filename: str) -> str:
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    )
    
    return "".join(diff)

def list_project_files(project_path: str, extensions: list = None) -> list[str]:
    if extensions is None:
        extensions = [".py", ".ts", ".js", ".dart", ".md", ".json", ".yaml"]
    
    path = Path(project_path)
    if not path.exists():
        return []
    
    exclude_dirs = {"node_modules", ".git", "__pycache__", "_archives", "graphify-out"}
    files = []
    
    for ext in extensions:
        for file in path.rglob(f"*{ext}"):
            if any(excluded in file.parts for excluded in exclude_dirs):
                continue
            if file.name.startswith(".jarvis_tmp"):
                continue
            files.append(str(file.relative_to(path)))
    
    return sorted(files)

def archive_docs(project_path: str) -> list[str]:
    path = Path(project_path)
    allowed_docs = {"PROJET_CONTEXTE.md", "STACK_CODE.md", "CHANGELOG.md", "BUGS.md", "README.md"}
    archive_dir = path / "_archives"
    
    archived = []
    
    for md_file in path.rglob("*.md"):
        if md_file.name in allowed_docs:
            continue
        if "_archives" in md_file.parts:
            continue
        
        archive_dir.mkdir(parents=True, exist_ok=True)
        relative_path = md_file.relative_to(path)
        target = archive_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(md_file), str(target))
        archived.append(str(relative_path))
    
    return archived

def run_graphify(project_path: str, update_only: bool = False) -> dict:
    import subprocess
    
    if shutil.which("graphify") is None:
        return {"status": "skipped", "message": "graphify non installé"}
    
    try:
        cmd = ["graphify", "update", "."] if update_only else ["graphify", "."]
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {"status": "success", "message": "Graphify exécuté"}
        else:
            return {"status": "error", "message": result.stderr or result.stdout}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

def parse_projet_contexte(project_path: str) -> dict:
    path = Path(project_path) / "PROJET_CONTEXTE.md"
    if not path.exists():
        return {}
    
    content = path.read_text(encoding="utf-8")
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_section is not None:
                sections[current_section] = "\n".join(current_content)
            
            section_num = line[3:].split(".")[0].strip()
            if section_num.isdigit():
                current_section = section_num
                current_content = [line]
            else:
                current_section = None
                current_content = []
        elif current_section is not None:
            current_content.append(line)
    
    if current_section is not None:
        sections[current_section] = "\n".join(current_content)
    
    return sections

def get_sections(project_path: str, section_numbers: list[int]) -> str:
    sections = parse_projet_contexte(project_path)
    result = []
    
    for num in section_numbers:
        section_key = str(num)
        if section_key in sections:
            result.append(sections[section_key])
    
    return "\n\n".join(result)
