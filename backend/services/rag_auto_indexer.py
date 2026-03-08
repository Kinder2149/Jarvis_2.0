"""
RAGAutoIndexer - JARVIS 2.0
Auto-indexation projets complétés dans RAG avec anti-doublon
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import hashlib


class RAGAutoIndexer:
    """
    Indexation automatique projets dans RAG
    
    Responsabilités :
    - Détecter fin de mission
    - Générer documents projet (architecture, décisions, leçons)
    - Indexer dans ChromaDB avec métadonnées uniques
    - Éviter doublons (même projet indexé plusieurs fois)
    - Versioning automatique
    """
    
    def __init__(self, rag_projects_path: str = "RAG/projects"):
        self.projects_path = Path(rag_projects_path)
        self.projects_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.projects_path / "index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """Crée fichier index s'il n'existe pas"""
        if not self.index_file.exists():
            self.index_file.write_text(
                json.dumps({"projects": []}, indent=2),
                encoding='utf-8'
            )
    
    def _load_index(self) -> Dict:
        """Charge index projets"""
        try:
            return json.loads(self.index_file.read_text(encoding='utf-8'))
        except Exception:
            return {"projects": []}
    
    def _save_index(self, index_data: Dict):
        """Sauvegarde index projets"""
        self.index_file.write_text(
            json.dumps(index_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def _generate_project_hash(self, project_path: str) -> str:
        """
        Génère hash unique pour projet (anti-doublon)
        
        Args:
            project_path: Chemin projet
        
        Returns:
            Hash MD5 du chemin normalisé
        """
        normalized_path = Path(project_path).resolve().as_posix()
        return hashlib.md5(normalized_path.encode()).hexdigest()[:12]
    
    def is_project_indexed(self, project_path: str) -> bool:
        """
        Vérifie si projet déjà indexé
        
        Args:
            project_path: Chemin projet
        
        Returns:
            True si déjà indexé
        """
        project_hash = self._generate_project_hash(project_path)
        index_data = self._load_index()
        
        return any(
            p.get("hash") == project_hash
            for p in index_data.get("projects", [])
        )
    
    def index_completed_mission(
        self,
        mission_id: str,
        project_path: str,
        project_name: str,
        user_request: str,
        files_created: List[str],
        architecture_doc: Optional[str] = None
    ) -> Dict:
        """
        Indexe mission complétée dans RAG
        
        Args:
            mission_id: ID mission
            project_path: Chemin projet
            project_name: Nom projet
            user_request: Demande utilisateur originale
            files_created: Liste fichiers créés
            architecture_doc: Document architecture (optionnel)
        
        Returns:
            Dict avec success, project_hash, indexed_at
        """
        project_hash = self._generate_project_hash(project_path)
        
        # Créer dossier projet dans RAG
        rag_project_dir = self.projects_path / project_name
        rag_project_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Sauvegarder métadonnées
        metadata = {
            "project_hash": project_hash,
            "mission_id": mission_id,
            "project_name": project_name,
            "project_path": project_path,
            "user_request": user_request,
            "files_created": files_created,
            "indexed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        metadata_file = rag_project_dir / "metadata.json"
        metadata_file.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        # 2. Sauvegarder architecture si fournie
        if architecture_doc:
            arch_file = rag_project_dir / "architecture.md"
            arch_file.write_text(architecture_doc, encoding='utf-8')
        
        # 3. Générer lessons_learned.md (template)
        lessons_file = rag_project_dir / "lessons_learned.md"
        if not lessons_file.exists():
            lessons_content = f"""# Leçons Apprises — {project_name}

**Date** : {datetime.now().strftime("%d/%m/%Y")}  
**Mission** : {mission_id}

## Demande Utilisateur

{user_request}

## Fichiers Générés

{chr(10).join(f"- `{f}`" for f in files_created)}

## Points Clés

- [À compléter lors de futures itérations]

## Améliorations Possibles

- [À compléter lors de futures itérations]

## Patterns Utilisés

- [À identifier automatiquement]
"""
            lessons_file.write_text(lessons_content, encoding='utf-8')
        
        # 4. Mettre à jour index
        index_data = self._load_index()
        
        # Vérifier si déjà indexé
        existing_idx = next(
            (i for i, p in enumerate(index_data["projects"])
             if p.get("hash") == project_hash),
            None
        )
        
        index_entry = {
            "hash": project_hash,
            "name": project_name,
            "path": str(rag_project_dir),
            "mission_id": mission_id,
            "indexed_at": datetime.now().isoformat(),
            "files_count": len(files_created)
        }
        
        if existing_idx is not None:
            # Mise à jour
            index_data["projects"][existing_idx] = index_entry
        else:
            # Nouveau
            index_data["projects"].append(index_entry)
        
        self._save_index(index_data)
        
        return {
            "success": True,
            "project_hash": project_hash,
            "indexed_at": datetime.now().isoformat(),
            "rag_path": str(rag_project_dir),
            "is_update": existing_idx is not None
        }
    
    def get_indexed_projects(self) -> List[Dict]:
        """
        Récupère liste projets indexés
        
        Returns:
            Liste projets avec métadonnées
        """
        index_data = self._load_index()
        return index_data.get("projects", [])
    
    def get_project_by_hash(self, project_hash: str) -> Optional[Dict]:
        """
        Récupère projet par hash
        
        Args:
            project_hash: Hash projet
        
        Returns:
            Métadonnées projet ou None
        """
        index_data = self._load_index()
        return next(
            (p for p in index_data.get("projects", [])
             if p.get("hash") == project_hash),
            None
        )
    
    def remove_project_from_index(self, project_hash: str) -> bool:
        """
        Retire projet de l'index
        
        Args:
            project_hash: Hash projet
        
        Returns:
            True si retiré, False si non trouvé
        """
        index_data = self._load_index()
        projects = index_data.get("projects", [])
        
        filtered = [p for p in projects if p.get("hash") != project_hash]
        
        if len(filtered) < len(projects):
            index_data["projects"] = filtered
            self._save_index(index_data)
            return True
        
        return False
