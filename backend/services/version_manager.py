"""
VersionManager - JARVIS 2.0
Gestion versioning sémantique automatique des projets
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class VersionManager:
    """
    Gestionnaire de versions avec versioning sémantique
    
    Responsabilités :
    - Récupérer version actuelle projet
    - Incrémenter version selon type changement
    - Sauvegarder version + métadonnées
    - Détecter type changement depuis demande utilisateur
    
    Format version : MAJOR.MINOR.PATCH
    - MAJOR : Refonte complète, breaking changes
    - MINOR : Nouvelle fonctionnalité, rétrocompatible
    - PATCH : Correction bug, rétrocompatible
    """
    
    VERSION_FILE = ".jarvis_version.json"
    
    def get_project_version(self, project_path: str) -> str:
        """
        Récupère version actuelle du projet
        
        Args:
            project_path: Chemin projet
        
        Returns:
            Version au format "MAJOR.MINOR.PATCH" (défaut: "0.1.0")
        """
        version_file = Path(project_path) / self.VERSION_FILE
        
        if not version_file.exists():
            return "0.1.0"  # Version initiale
        
        try:
            data = json.loads(version_file.read_text(encoding='utf-8'))
            return data.get("version", "0.1.0")
        except Exception:
            return "0.1.0"
    
    def increment_version(self, current_version: str, change_type: str) -> str:
        """
        Incrémente version selon type de changement
        
        Args:
            current_version: Version actuelle (ex: "1.2.3")
            change_type: Type changement ("major", "minor", "patch")
        
        Returns:
            Nouvelle version
        """
        try:
            major, minor, patch = map(int, current_version.split("."))
        except ValueError:
            # Version invalide → reset
            major, minor, patch = 0, 1, 0
        
        if change_type == "major":
            return f"{major + 1}.0.0"
        elif change_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif change_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            # Par défaut : minor
            return f"{major}.{minor + 1}.0"
    
    def save_version(
        self,
        project_path: str,
        version: str,
        mission_id: str,
        files_modified: Optional[list[str]] = None
    ):
        """
        Sauvegarde version + métadonnées
        
        Args:
            project_path: Chemin projet
            version: Nouvelle version
            mission_id: ID mission associée
            files_modified: Liste fichiers modifiés (optionnel)
        """
        version_file = Path(project_path) / self.VERSION_FILE
        
        data = {
            "version": version,
            "mission_id": mission_id,
            "updated_at": datetime.now().isoformat(),
            "files_modified": files_modified or [],
            "created_by": "JARVIS 2.0"
        }
        
        version_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def detect_change_type(self, user_request: str) -> str:
        """
        Détecte type de changement depuis demande utilisateur
        
        Args:
            user_request: Demande utilisateur
        
        Returns:
            Type changement ("major", "minor", "patch")
        """
        request_lower = user_request.lower()
        
        # Mots-clés refonte (MAJOR)
        major_keywords = [
            "refonte", "réécrire", "recommencer", "from scratch",
            "complètement", "entièrement", "breaking change"
        ]
        if any(word in request_lower for word in major_keywords):
            return "major"
        
        # Mots-clés correction (PATCH)
        patch_keywords = [
            "corrige", "bug", "erreur", "fix", "répare",
            "hotfix", "patch", "typo"
        ]
        if any(word in request_lower for word in patch_keywords):
            return "patch"
        
        # Mots-clés nouvelle fonctionnalité (MINOR)
        minor_keywords = [
            "ajoute", "nouvelle", "feature", "améliore",
            "étend", "implémente", "crée"
        ]
        if any(word in request_lower for word in minor_keywords):
            return "minor"
        
        # Par défaut : minor (nouvelle fonctionnalité)
        return "minor"
    
    def get_version_history(self, project_path: str) -> dict:
        """
        Récupère historique version du projet
        
        Args:
            project_path: Chemin projet
        
        Returns:
            Dict avec version, mission_id, updated_at, files_modified
        """
        version_file = Path(project_path) / self.VERSION_FILE
        
        if not version_file.exists():
            return {
                "version": "0.1.0",
                "mission_id": None,
                "updated_at": None,
                "files_modified": []
            }
        
        try:
            return json.loads(version_file.read_text(encoding='utf-8'))
        except Exception:
            return {
                "version": "0.1.0",
                "mission_id": None,
                "updated_at": None,
                "files_modified": []
            }
