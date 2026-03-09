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
        - fichier.py ligne X : description
        
        OU
        
        Fichiers manquants: fichier1.py, fichier2.py
        
        Returns:
            Liste de {"file": str, "line": int, "description": str}
        """
        corrections = []
        
        # Pattern 1 : Fichiers manquants
        missing_pattern = r'Fichiers manquants:\s*(.+)'
        missing_match = re.search(missing_pattern, feedback, re.IGNORECASE)
        if missing_match:
            files_str = missing_match.group(1)
            # Split par virgule, backticks, ou espaces
            files = re.findall(r'`?([a-zA-Z0-9_/\\.-]+\.(?:py|js|ts|json|md|txt|yaml|yml))`?', files_str)
            for filepath in files:
                corrections.append({
                    "file": filepath.strip(),
                    "line": 0,
                    "description": f"Fichier manquant requis"
                })
        
        # Pattern 2 : Corrections ligne par ligne (nouveau format)
        # - fichier.py ligne X : description
        line_pattern = r'-\s+([a-zA-Z0-9_/\\.-]+\.(?:py|js|ts|json|md|txt|yaml|yml))\s+ligne\s+(\d+)\s*:\s*(.+)'
        
        for line in feedback.split('\n'):
            match = re.search(line_pattern, line)
            if match:
                corrections.append({
                    "file": match.group(1).strip(),
                    "line": int(match.group(2)),
                    "description": match.group(3).strip()
                })
        
        # Pattern 3 : Ancien format (rétrocompatibilité)
        # - [fichier] : ❌ INVALIDE
        #   • Ligne [X] : [description]
        file_pattern = r'-\s+\[([^\]]+)\]\s*:\s*❌\s*INVALIDE'
        old_line_pattern = r'•\s*Ligne\s+(\d+)\s*:\s*(.+)'
        
        current_file = None
        for line in feedback.split('\n'):
            # Détecter fichier invalide
            file_match = re.search(file_pattern, line)
            if file_match:
                current_file = file_match.group(1)
                continue
            
            # Détecter problème ligne
            if current_file:
                line_match = re.search(old_line_pattern, line)
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
