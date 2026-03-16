"""
CodeParser - JARVIS 2.0
Parse réponses agents et extrait code pour écriture fichiers
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CodeBlock:
    """Représente un bloc de code extrait"""
    
    def __init__(
        self,
        filepath: str,
        content: str,
        language: str = "python"
    ):
        self.filepath = filepath
        self.content = content
        self.language = language
    
    def __repr__(self):
        return f"CodeBlock(filepath='{self.filepath}', language='{self.language}', {len(self.content)} chars)"


class CodeParser:
    """
    Parser pour extraire code depuis réponses agents
    
    Responsabilités :
    - Détecter blocs code markdown (```python, ```javascript, etc.)
    - Extraire chemins fichiers depuis commentaires ou contexte
    - Nettoyer code (retirer commentaires inutiles)
    - Valider structure fichiers
    """
    
    # Patterns regex
    CODE_BLOCK_PATTERN = r'```(\w+)?\n(.*?)```'
    FILEPATH_PATTERNS = [
        # Pattern prioritaire : # chemin/fichier.ext (format CODEUR)
        r'#\s+([a-zA-Z0-9_/\\.-]+\.(?:py|js|ts|jsx|tsx|html|css|json|md|txt|yaml|yml|toml|ini|sh|bat))\s*$',
        # Patterns avec préfixes explicites
        r'#\s*(?:File|Fichier|Path|Chemin)\s*:\s*([^\n]+)',
        r'//\s*(?:File|Fichier|Path|Chemin)\s*:\s*([^\n]+)',
        r'<!--\s*(?:File|Fichier|Path|Chemin)\s*:\s*([^\n]+)\s*-->',
        # Pattern backticks
        r'`([^`]+\.(?:py|js|ts|jsx|tsx|html|css|json|md|txt))`',
    ]
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[CodeBlock]:
        """
        Extrait tous les blocs de code depuis texte
        
        Args:
            text: Texte contenant blocs code markdown
        
        Returns:
            Liste CodeBlock extraits
        """
        blocks = []
        
        print(f"🔍 [CODE_PARSER] Recherche blocs code dans texte ({len(text)} chars)...")
        
        # Trouver tous les blocs ```language\ncode```
        matches = re.finditer(
            CodeParser.CODE_BLOCK_PATTERN,
            text,
            re.DOTALL | re.MULTILINE
        )
        
        matches_list = list(matches)
        print(f"📊 [CODE_PARSER] {len(matches_list)} blocs markdown trouvés")
        
        for idx, match in enumerate(matches_list):
            language = match.group(1) or "python"
            content = match.group(2).strip()
            
            print(f"🔎 [CODE_PARSER] Bloc {idx+1}: language={language}, {len(content)} chars")
            
            # Chercher filepath dans le contenu ou contexte
            filepath = CodeParser._extract_filepath(content, text, match.start())
            
            if filepath:
                blocks.append(CodeBlock(
                    filepath=filepath,
                    content=content,
                    language=language
                ))
                print(f"✅ [CODE_PARSER] Bloc {idx+1} extrait: {filepath}")
                logger.debug(f"Bloc code extrait: {filepath} ({language}, {len(content)} chars)")
            else:
                print(f"⚠️  [CODE_PARSER] Bloc {idx+1}: Aucun filepath trouvé, bloc ignoré")
        
        print(f"📋 [CODE_PARSER] Total blocs extraits avec filepath: {len(blocks)}")
        return blocks
    
    @staticmethod
    def _extract_filepath(content: str, full_text: str, block_start: int) -> Optional[str]:
        """
        Extrait chemin fichier depuis contenu ou contexte
        
        Cherche dans cet ordre :
        1. Commentaire dans le code (# File: path/to/file.py)
        2. Ligne précédant le bloc (Créer `path/to/file.py`)
        3. Détection extension dans contexte
        
        Args:
            content: Contenu bloc code
            full_text: Texte complet
            block_start: Position début bloc dans full_text
        
        Returns:
            Chemin fichier ou None
        """
        # 1. Chercher dans le contenu du bloc
        for pattern in CodeParser.FILEPATH_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                filepath = match.group(1).strip()
                # Nettoyer filepath (retirer quotes, espaces)
                filepath = filepath.strip('\'"` \t')
                if filepath:
                    return filepath
        
        # 2. Chercher dans les 200 chars précédant le bloc
        context_before = full_text[max(0, block_start - 200):block_start]
        for pattern in CodeParser.FILEPATH_PATTERNS:
            match = re.search(pattern, context_before, re.IGNORECASE)
            if match:
                filepath = match.group(1).strip()
                filepath = filepath.strip('\'"` \t')
                if filepath:
                    return filepath
        
        return None
    
    @staticmethod
    def write_code_blocks(
        blocks: List[CodeBlock],
        project_path: str,
        dry_run: bool = False
    ) -> Dict[str, List[str]]:
        """
        Écrit blocs code sur disque
        
        Args:
            blocks: Liste CodeBlock à écrire
            project_path: Chemin projet
            dry_run: Si True, simule sans écrire
        
        Returns:
            Dict avec files_created, files_updated, errors
        """
        project_root = Path(project_path)
        files_created = []
        files_updated = []
        errors = []
        
        # Détecter doublons de filepath
        filepath_counts = {}
        for block in blocks:
            filepath_counts[block.filepath] = filepath_counts.get(block.filepath, 0) + 1
        
        # Alerter sur doublons
        duplicates = {fp: count for fp, count in filepath_counts.items() if count > 1}
        if duplicates:
            print(f" [CODE_PARSER] Doublons détectés:")
            for fp, count in duplicates.items():
                print(f"   - {fp}: {count} blocs")
            logger.warning(f"Doublons filepath détectés: {duplicates}")
        
        # Grouper blocs par filepath pour concaténation
        blocks_by_filepath = {}
        for block in blocks:
            if block.filepath not in blocks_by_filepath:
                blocks_by_filepath[block.filepath] = []
            blocks_by_filepath[block.filepath].append(block)
        
        # Écrire un fichier par filepath (en concaténant si doublons)
        for filepath, file_blocks in blocks_by_filepath.items():
            try:
                # Construire chemin complet
                file_path = project_root / filepath
                
                # Créer dossiers parents si nécessaire
                if not dry_run:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Vérifier si fichier existe
                file_exists = file_path.exists()
                
                # Si plusieurs blocs pour le même fichier, prendre uniquement le premier
                # (évite écrasement par blocs markdown/README)
                if len(file_blocks) > 1:
                    print(f"⚠️  [CODE_PARSER] {len(file_blocks)} blocs pour {filepath}, utilisation du premier uniquement")
                    logger.warning(f"{len(file_blocks)} blocs pour {filepath}, utilisation du premier")
                
                # Utiliser le premier bloc (généralement le code, pas le README)
                content_to_write = file_blocks[0].content
                
                if dry_run:
                    logger.info(f"[DRY RUN] {'Mise à jour' if file_exists else 'Création'}: {filepath}")
                    if file_exists:
                        files_updated.append(str(file_path))
                    else:
                        files_created.append(str(file_path))
                else:
                    # Écrire fichier
                    file_path.write_text(content_to_write, encoding='utf-8')
                    
                    if file_exists:
                        files_updated.append(str(file_path))
                        print(f"📝 [CODE_PARSER] Fichier mis à jour: {file_path}")
                        logger.info(f"Fichier mis à jour: {file_path}")
                    else:
                        files_created.append(str(file_path))
                        print(f"✅ [CODE_PARSER] Fichier créé: {file_path}")
                        logger.info(f"Fichier créé: {file_path}")
            
            except Exception as e:
                error_msg = f"Erreur écriture {filepath}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            "files_created": files_created,
            "files_updated": files_updated,
            "errors": errors,
            "total_files": len(files_created) + len(files_updated)
        }
    
    @staticmethod
    def parse_and_write(
        agent_response: str,
        project_path: str,
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        Parse réponse agent et écrit fichiers (méthode tout-en-un)
        
        Args:
            agent_response: Réponse complète agent
            project_path: Chemin projet
            dry_run: Si True, simule sans écrire
        
        Returns:
            Dict avec files_created, files_updated, errors, blocks_found
        """
        logger.info(f"Parse réponse agent ({len(agent_response)} chars)")
        
        # Extraire blocs code
        blocks = CodeParser.extract_code_blocks(agent_response)
        
        logger.info(f"Blocs code trouvés: {len(blocks)}")
        for block in blocks:
            logger.debug(f"  - {block}")
        
        # Écrire fichiers
        result = CodeParser.write_code_blocks(blocks, project_path, dry_run)
        result["blocks_found"] = len(blocks)
        
        return result


# Fonction helper pour intégration facile
def parse_and_write_code(
    agent_response: str,
    project_path: str,
    dry_run: bool = False
) -> Dict[str, any]:
    """
    Helper function pour parser et écrire code
    
    Args:
        agent_response: Réponse agent
        project_path: Chemin projet
        dry_run: Simulation sans écriture
    
    Returns:
        Dict résultat
    """
    return CodeParser.parse_and_write(agent_response, project_path, dry_run)
