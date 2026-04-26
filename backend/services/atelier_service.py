from pathlib import Path
import json
import zipfile
import io
import re
import httpx
import shutil as _shutil
import re as _re

RESOURCES_PATH = Path(__file__).parent.parent / "data" / "atelier" / "resources"
DEMOS_PATH = Path(__file__).parent.parent / "data" / "atelier" / "demos"
CLIENTS_BASE_DIR = Path("C:/DEV/PROJETS/Clients")


def load_resource(filename: str) -> str:
    """Charge un fichier de ressource. Ex: load_resource('CADRAGE_STRATEGIQUE.md')"""
    path = RESOURCES_PATH / filename
    if not path.exists():
        return f"[RESSOURCE MANQUANTE: {filename}]"
    return path.read_text(encoding="utf-8")


def load_tool_spec(tool_name: str) -> str:
    """Charge la spec d'un outil. Ex: load_tool_spec('reservations')"""
    filename = f"TOOL_{tool_name.upper()}_SPEC.md"
    path = RESOURCES_PATH / "tools" / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def get_activated_tools(saisie_data: dict) -> list:
    """Retourne la liste des outils activés depuis les données du formulaire SAISIE."""
    outils = saisie_data.get("outils", {})
    activated = ["reservations", "menu_ardoise"]  # toujours obligatoires
    for tool in ["evenements", "avis", "emporter"]:
        if outils.get(tool, False):
            activated.append(tool)
    return activated


async def fetch_url(url: str) -> dict:
    """Fetch HTTP d'une URL prospect, retourne le texte nettoyé + CSS + images absolues."""
    if not url or url.strip() in ("aucun site", "", "null"):
        return {"text": "", "title": "", "images": [], "css_inline": "", "css_external": "", "base_url": ""}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
        
        raw_html = response.text
        
        # Extraire le domaine de base
        base_url = ""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        except:
            base_url = ""
        
        # PROBLÈME 1 : Extraire le CSS inline AVANT nettoyage
        css_inline = ""
        try:
            style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', raw_html, re.DOTALL | re.IGNORECASE)
            css_inline = "\n".join(style_blocks)[:8000]
        except:
            css_inline = ""
        
        # PROBLÈME 3 : Fetch du premier CSS externe
        css_external = ""
        try:
            link_match = re.search(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', raw_html, re.IGNORECASE)
            if not link_match:
                link_match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\']', raw_html, re.IGNORECASE)
            
            if link_match:
                css_url = link_match.group(1)
                # Résoudre URL relative
                if css_url.startswith("//"):
                    css_url = f"https:{css_url}"
                elif css_url.startswith("/"):
                    css_url = f"{base_url}{css_url}"
                elif not css_url.startswith("http"):
                    css_url = ""
                
                if css_url:
                    try:
                        css_response = await client.get(css_url, timeout=8.0)
                        css_external = css_response.text[:8000]
                    except:
                        css_external = ""
        except:
            css_external = ""
        
        # Nettoyage simple sans dépendance BS4 : supprimer les balises HTML
        text = re.sub(r'<script[^>]*>.*?</script>', '', raw_html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text[:15000]  # limiter le contexte injecté au LLM

        # Extraire le titre
        title_match = re.search(r'<title[^>]*>(.*?)</title>', raw_html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        # Extraire les URLs d'images
        images_raw = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)[:10]
        
        # PROBLÈME 2 : Résoudre les URLs d'images en absolues
        images = []
        for img_url in images_raw:
            try:
                if img_url.startswith("http"):
                    images.append(img_url)
                elif img_url.startswith("//"):
                    images.append(f"https:{img_url}")
                elif img_url.startswith("/") and base_url:
                    images.append(f"{base_url}{img_url}")
            except:
                pass

        return {
            "text": text,
            "title": title,
            "images": images,
            "raw_html": raw_html[:30000],
            "css_inline": css_inline,
            "css_external": css_external,
            "base_url": base_url
        }
    except Exception as e:
        return {
            "text": f"[Erreur fetch URL: {str(e)}]",
            "title": "",
            "images": [],
            "css_inline": "",
            "css_external": "",
            "base_url": ""
        }


def save_demo_files(prospect_slug: str, raw_outputs: dict, client_nom: str = None) -> Path:
    """
    Parse les outputs LLM des steps génération et écrit les 5 fichiers démo.
    raw_outputs = {
        "generation_css": "...",
        "generation_index": "...",
        "generation_admin": "..."
    }
    Format attendu pour generation_index et generation_admin :
    <<<FILE: index.html>>>
    [contenu]
    <<<FILE: script.js>>>
    [contenu]
    """
    import logging
    logger = logging.getLogger("jarvis")
    
    # Nom de dossier sécurisé depuis le nom client
    if client_nom:
        safe_name = _re.sub(r'[^\w\s-]', '', client_nom).strip()
        safe_name = _re.sub(r'[\s]+', '_', safe_name)
    else:
        safe_name = prospect_slug
    
    logger.info(f"📁 [ATELIER_EXPORT] Création dossier démo : {safe_name}")
    
    # Écrire dans C:\DEV\PROJETS\Clients\{nom_client}\
    demo_dir = CLIENTS_BASE_DIR / safe_name
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    # Garder aussi une copie dans le dossier interne pour le ZIP et la DB
    internal_dir = DEMOS_PATH / prospect_slug
    internal_dir.mkdir(parents=True, exist_ok=True)

    # styles.css — extraire entre ```css et ```
    css_raw = raw_outputs.get("generation_css", "")
    logger.info(f"🎨 [ATELIER_EXPORT] CSS raw length: {len(css_raw)} chars")
    css_content = _extract_code_block(css_raw, "css")
    logger.info(f"🎨 [ATELIER_EXPORT] CSS extracted: {len(css_content)} chars")
    (demo_dir / "styles.css").write_text(css_content, encoding="utf-8")
    logger.info(f"✅ [ATELIER_EXPORT] styles.css écrit")

    # index.html + script.js
    index_raw = raw_outputs.get("generation_index", "")
    logger.info(f"📄 [ATELIER_EXPORT] Index raw length: {len(index_raw)} chars")
    index_files = _parse_file_delimiters(index_raw)
    logger.info(f"📄 [ATELIER_EXPORT] Index files parsed: {list(index_files.keys())}")
    for filename, content in index_files.items():
        (demo_dir / filename).write_text(content, encoding="utf-8")
        logger.info(f"✅ [ATELIER_EXPORT] {filename} écrit ({len(content)} chars)")

    # admin.html + admin.js
    admin_raw = raw_outputs.get("generation_admin", "")
    logger.info(f"🔒 [ATELIER_EXPORT] Admin raw length: {len(admin_raw)} chars")
    admin_files = _parse_file_delimiters(admin_raw)
    logger.info(f"🔒 [ATELIER_EXPORT] Admin files parsed: {list(admin_files.keys())}")
    for filename, content in admin_files.items():
        (demo_dir / filename).write_text(content, encoding="utf-8")
        logger.info(f"✅ [ATELIER_EXPORT] {filename} écrit ({len(content)} chars)")

    # Validation : vérifier que tous les fichiers requis ont été générés
    required_files = {"index.html", "script.js", "admin.html", "admin.js"}
    generated_files = set(index_files.keys()) | set(admin_files.keys())
    missing = required_files - generated_files
    if missing:
        raise ValueError(
            f"Génération incomplète — fichiers manquants : {', '.join(sorted(missing))}. "
            f"Vérifier les outputs LLM des steps génération."
        )
    if not css_content.strip():
        raise ValueError(
            "Génération incomplète — styles.css est vide. "
            "Vérifier l'output du step generation_css."
        )

    # Copier tous les fichiers vers le dossier interne pour compatibilité ZIP
    for file_path in demo_dir.rglob("*"):
        if file_path.is_file():
            dest = internal_dir / file_path.relative_to(demo_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            _shutil.copy2(file_path, dest)
    
    return demo_dir


def export_as_zip(prospect_slug: str) -> bytes:
    """Compresse le dossier demo/{slug}/ en ZIP et retourne les bytes."""
    demo_dir = DEMOS_PATH / prospect_slug
    if not demo_dir.exists():
        raise FileNotFoundError(f"Dossier démo introuvable : {demo_dir}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in demo_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(demo_dir))
    return buf.getvalue()


def _extract_code_block(text: str, lang: str) -> str:
    pattern = rf"```{lang}\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def _parse_file_delimiters(text: str) -> dict:
    """
    Parse les fichiers depuis l'output LLM.
    Supporte 3 formats :
    1. <<<FILE: nom.ext>>> ... (ancien format)
    2. # FILENAME\n```lang\ncontent\n``` (format actuel)
    3. ```lang\n# filename\ncontent\n``` (format alternatif)
    """
    import logging
    logger = logging.getLogger("jarvis")
    
    files = {}
    logger.info(f"🔍 [PARSE] Début parsing, texte length: {len(text)} chars")
    
    # Essayer d'abord le format <<<FILE: >>>
    parts = _re.split(r'<<<FILE:\s*(.+?)>>>', text)
    if len(parts) > 1:
        logger.info(f"✅ [PARSE] Format <<<FILE:>>> détecté, {len(parts)//2} fichiers")
        for i in range(1, len(parts), 2):
            filename = parts[i].strip()
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            files[filename] = content
            logger.info(f"📄 [PARSE] Fichier trouvé: {filename} ({len(content)} chars)")
        return files
    
    # Format actuel : # FILENAME\n\n```lang\ncontent\n```
    # Chercher les patterns "# FILENAME" (éventuellement suivi de texte) avant un bloc markdown
    pattern = r'#\s+([A-Za-z_][A-Za-z0-9_.-]*)[^\n]*\n\s*```[a-zA-Z]*\s*\n(.*?)```'
    matches = _re.findall(pattern, text, _re.DOTALL | _re.IGNORECASE)
    
    if matches:
        logger.info(f"✅ [PARSE] Format # FILENAME détecté, {len(matches)} fichiers")
    
    for filename, content in matches:
        # Normaliser le nom de fichier (INDEX.HTML -> index.html)
        filename = filename.lower()
        files[filename] = content.strip()
        logger.info(f"📄 [PARSE] Fichier trouvé: {filename} ({len(content)} chars)")
    
    # Si aucun fichier trouvé, essayer le format alternatif (# filename dans le bloc)
    if not files:
        logger.info(f"⚠️ [PARSE] Aucun fichier avec format standard, essai format alternatif...")
        blocks = _re.findall(r'```[a-zA-Z]*\s*\n(.*?)```', text, _re.DOTALL)
        logger.info(f"🔍 [PARSE] {len(blocks)} blocs markdown trouvés")
        
        for idx, block in enumerate(blocks):
            lines = block.strip().split('\n')
            if not lines:
                continue
            
            first_line = lines[0].strip()
            filename = None
            
            # Détecter le nom de fichier (# filename ou // filename)
            for prefix in ('#', '//'):
                if first_line.startswith(prefix):
                    candidate = first_line[len(prefix):].strip()
                    # Vérifier que c'est un nom de fichier valide (contient une extension)
                    if '.' in candidate and '/' not in candidate and '\\' not in candidate:
                        filename = candidate.lower()
                        logger.info(f"📄 [PARSE] Bloc {idx}: filename détecté = {filename}")
                        break
            
            if filename:
                content = '\n'.join(lines[1:])  # Tout sauf la première ligne
                files[filename] = content
            else:
                logger.warning(f"⚠️ [PARSE] Bloc {idx}: pas de filename détecté (first_line={first_line[:50]}...)")
    
    logger.info(f"🎯 [PARSE] Résultat final: {len(files)} fichiers parsés: {list(files.keys())}")
    return files
