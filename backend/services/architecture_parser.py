"""
Parser pour les réponses ARCHITECTE (JSON + Markdown)
"""

import json
import re
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ArchitectureParser:
    """Parse les réponses ARCHITECTE (JSON + Markdown)."""
    
    def parse(self, response: str) -> Optional[Dict]:
        """
        Extrait le JSON de la réponse ARCHITECTE.
        
        Args:
            response: Réponse complète ARCHITECTE
        
        Returns:
            Dict avec files_to_create, stack, patterns, file_specs, justification
            None si parsing échoue
        """
        # Chercher bloc JSON entre ```json et ```
        json_pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if not match:
            logger.error("Architecture: Aucun bloc JSON trouvé")
            return None
        
        json_str = match.group(1)
        
        try:
            architecture = json.loads(json_str)
            
            # Valider structure minimale
            required_keys = ["files_to_create", "stack", "file_specs"]
            for key in required_keys:
                if key not in architecture:
                    logger.error(f"Architecture: Clé manquante '{key}'")
                    return None
            
            logger.info(f"Architecture: Parsé avec succès ({len(architecture['files_to_create'])} fichiers)")
            return architecture
            
        except json.JSONDecodeError as e:
            logger.error(f"Architecture: JSON invalide - {e}")
            return None
    
    def extract_markdown(self, response: str) -> Optional[str]:
        """
        Extrait le document Markdown de la réponse ARCHITECTE.
        
        Args:
            response: Réponse complète ARCHITECTE
        
        Returns:
            Document Markdown ou None si non trouvé
        """
        # Chercher après "### PARTIE 2" ou "Document architecture.md"
        markdown_pattern = r'(?:### PARTIE 2|Document architecture\.md).*?\n\n```markdown\s*\n(.*?)```'
        match = re.search(markdown_pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        logger.warning("Architecture: Document Markdown non trouvé")
        return None
