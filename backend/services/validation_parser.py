"""
Parser pour les feedbacks VALIDATEUR
"""

import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ValidationParser:
    """Parse les feedbacks VALIDATEUR."""
    
    def parse_corrections(self, feedback: str) -> List[Dict]:
        """
        Extrait corrections du feedback VALIDATEUR.
        
        Format attendu :
        - [chemin/fichier.ext] : ❌ INVALIDE
          PROBLÈMES DÉTECTÉS:
          • Ligne [X] : [description]
        
        Returns:
            Liste de {"file": str, "line": int, "description": str}
        """
        corrections = []
        
        # Pattern : - [fichier] : ❌ INVALIDE
        file_pattern = r'-\s+\[([^\]]+)\]\s*:\s*❌\s*INVALIDE'
        # Pattern : • Ligne [X] : [description]
        line_pattern = r'•\s*Ligne\s+(\d+)\s*:\s*(.+)'
        
        current_file = None
        
        for line in feedback.split('\n'):
            # Détecter fichier invalide
            file_match = re.search(file_pattern, line)
            if file_match:
                current_file = file_match.group(1)
                continue
            
            # Détecter problème ligne
            if current_file:
                line_match = re.search(line_pattern, line)
                if line_match:
                    corrections.append({
                        "file": current_file,
                        "line": int(line_match.group(1)),
                        "description": line_match.group(2).strip()
                    })
        
        logger.info(f"Validation: {len(corrections)} corrections extraites")
        return corrections
    
    def is_valid(self, feedback: str) -> bool:
        """
        Vérifie si le feedback indique un code VALIDE.
        
        Args:
            feedback: Feedback VALIDATEUR
        
        Returns:
            True si VALIDE, False si INVALIDE
        """
        # Chercher "STATUT: VALIDE" au début de la réponse
        response_start = feedback[:100].upper()
        return "STATUT: VALIDE" in response_start or "STATUT FINAL: VALIDE" in response_start
