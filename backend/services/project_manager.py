"""
ProjectManager - JARVIS 2.0
Gestion détection projets existants et conflits
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class ProjectManager:
    """
    Gestionnaire de projets avec détection conflits
    
    Responsabilités :
    - Détecter si projet existe déjà
    - Analyser contenu projet existant
    - Proposer actions utilisateur (modifier/nouveau/écraser)
    - Gérer conflits de noms
    """
    
    def __init__(self, base_projects_path: str = "projects"):
        self.base_path = Path(base_projects_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def detect_existing_project(self, project_name: str) -> Dict:
        """
        Détecte si un projet existe déjà
        
        Args:
            project_name: Nom du projet
        
        Returns:
            Dict avec exists, path, files_count, last_modified, action
        """
        project_path = self.base_path / project_name
        
        if not project_path.exists():
            return {
                "exists": False,
                "path": None,
                "files_count": 0,
                "last_modified": None,
                "action": "create_new"
            }
        
        # Projet existe → Analyser contenu
        files = [f for f in project_path.rglob("*") if f.is_file()]
        
        if not files:
            # Dossier vide
            return {
                "exists": True,
                "path": str(project_path),
                "files_count": 0,
                "last_modified": None,
                "action": "create_new"  # Dossier vide = comme nouveau
            }
        
        last_modified = max(f.stat().st_mtime for f in files)
        
        return {
            "exists": True,
            "path": str(project_path),
            "files_count": len(files),
            "last_modified": datetime.fromtimestamp(last_modified),
            "action": "ask_user"  # Demander à l'utilisateur
        }
    
    def propose_action_message(self, existing_info: Dict) -> str:
        """
        Génère message pour demander action à l'utilisateur
        
        Args:
            existing_info: Résultat de detect_existing_project
        
        Returns:
            Message formaté pour l'utilisateur
        """
        if not existing_info["exists"]:
            return ""
        
        if existing_info["files_count"] == 0:
            return ""
        
        last_mod = existing_info['last_modified']
        last_mod_str = last_mod.strftime("%d/%m/%Y %H:%M") if last_mod else "Inconnue"
        
        return f"""⚠️ Un projet existe déjà à l'emplacement '{existing_info['path']}' :
- **{existing_info['files_count']} fichiers**
- **Dernière modification** : {last_mod_str}

**Que veux-tu faire ?**
1. **Modifier le projet existant** (ajouter/corriger fonctionnalités)
2. **Créer un nouveau projet** avec un nom différent
3. **Écraser le projet existant** (⚠️ perte de données)

Réponds avec le numéro de ton choix (1, 2 ou 3)."""
    
    def generate_unique_name(self, base_name: str) -> str:
        """
        Génère nom unique si projet existe déjà
        
        Args:
            base_name: Nom de base du projet
        
        Returns:
            Nom unique (ex: calculator_v2, calculator_v3)
        """
        if not (self.base_path / base_name).exists():
            return base_name
        
        version = 2
        while (self.base_path / f"{base_name}_v{version}").exists():
            version += 1
        
        return f"{base_name}_v{version}"
    
    def get_project_path(self, project_name: str) -> Path:
        """
        Retourne chemin complet du projet
        
        Args:
            project_name: Nom du projet
        
        Returns:
            Path absolu du projet
        """
        return self.base_path / project_name
    
    def list_projects(self) -> list[Dict]:
        """
        Liste tous les projets existants
        
        Returns:
            Liste de dicts avec name, path, files_count, last_modified
        """
        if not self.base_path.exists():
            return []
        
        projects = []
        for project_dir in self.base_path.iterdir():
            if not project_dir.is_dir():
                continue
            
            files = [f for f in project_dir.rglob("*") if f.is_file()]
            
            if not files:
                last_modified = None
            else:
                last_modified = datetime.fromtimestamp(
                    max(f.stat().st_mtime for f in files)
                )
            
            projects.append({
                "name": project_dir.name,
                "path": str(project_dir),
                "files_count": len(files),
                "last_modified": last_modified
            })
        
        # Trier par dernière modification (plus récent en premier)
        projects.sort(
            key=lambda p: p["last_modified"] or datetime.min,
            reverse=True
        )
        
        return projects
