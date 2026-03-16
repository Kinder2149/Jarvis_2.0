"""
MissionManager - JARVIS 2.0
Gestion du cycle de vie des missions avec persistance JSON
"""

from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime
from backend.models.mission import Mission, MissionStatus
from backend.models.mission_context import MissionContext


class MissionManager:
    """
    Gestionnaire missions avec persistance JSON
    
    Responsabilités :
    - Créer missions
    - Récupérer missions
    - Mettre à jour missions
    - Lister missions (par statut, par projet)
    - Persistance automatique
    """
    
    def __init__(self, storage_path: str = "backend/data/missions.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.missions: Dict[str, Mission] = self._load_missions()
    
    def _load_missions(self) -> Dict[str, Mission]:
        """Charge missions depuis JSON"""
        if not self.storage_path.exists():
            return {}
        
        try:
            data = json.loads(self.storage_path.read_text(encoding='utf-8'))
            return {mid: Mission(**mdata) for mid, mdata in data.items()}
        except Exception as e:
            print(f"Erreur chargement missions: {e}")
            return {}
    
    def _save_missions(self):
        """Sauvegarde missions vers JSON"""
        try:
            data = {
                mid: mission.model_dump(mode='json')
                for mid, mission in self.missions.items()
            }
            self.storage_path.write_text(
                json.dumps(data, indent=2, default=str, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"Erreur sauvegarde missions: {e}")
    
    def create_mission(
        self,
        mission_id: str,
        user_request: str,
        project_path: str
    ) -> Mission:
        """
        Crée nouvelle mission
        
        Args:
            mission_id: ID unique mission
            user_request: Demande utilisateur originale
            project_path: Chemin projet
        
        Returns:
            Mission créée
        """
        mission = Mission(
            mission_id=mission_id,
            user_request=user_request,
            project_path=project_path
        )
        self.missions[mission_id] = mission
        self._save_missions()
        return mission
    
    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """
        Récupère mission par ID
        
        Args:
            mission_id: ID mission
        
        Returns:
            Mission si trouvée, None sinon
        """
        return self.missions.get(mission_id)
    
    def update_mission(self, mission: Mission):
        """
        Met à jour mission existante
        
        Args:
            mission: Mission à mettre à jour
        """
        self.missions[mission.mission_id] = mission
        self._save_missions()
    
    def list_missions(
        self,
        status: Optional[MissionStatus] = None,
        project_path: Optional[str] = None
    ) -> List[Mission]:
        """
        Liste missions avec filtres optionnels
        
        Args:
            status: Filtrer par statut
            project_path: Filtrer par projet
        
        Returns:
            Liste missions filtrées
        """
        missions = list(self.missions.values())
        
        if status:
            missions = [m for m in missions if m.status == status]
        
        if project_path:
            missions = [m for m in missions if m.project_path == project_path]
        
        # Trier par date création (plus récent en premier)
        missions.sort(key=lambda m: m.created_at, reverse=True)
        
        return missions
    
    def delete_mission(self, mission_id: str) -> bool:
        """
        Supprime mission
        
        Args:
            mission_id: ID mission à supprimer
        
        Returns:
            True si supprimée, False si non trouvée
        """
        if mission_id in self.missions:
            del self.missions[mission_id]
            self._save_missions()
            return True
        return False
    
    def get_pending_validations(self) -> List[Mission]:
        """
        Récupère missions en attente validation
        
        Returns:
            Liste missions status=VALIDATING
        """
        return [
            m for m in self.missions.values()
            if m.status == MissionStatus.VALIDATING
        ]
    
    def get_missions_by_status(self, status: MissionStatus) -> List[Mission]:
        """
        Récupère missions par statut
        
        Args:
            status: Statut à filtrer
        
        Returns:
            Liste missions avec ce statut
        """
        return [m for m in self.missions.values() if m.status == status]
    
    def get_active_missions(self) -> List[Mission]:
        """
        Récupère missions actives (PENDING ou IN_PROGRESS)
        
        Returns:
            Liste missions actives
        """
        return [
            m for m in self.missions.values()
            if m.status in [MissionStatus.PENDING, MissionStatus.IN_PROGRESS]
        ]
    
    def get_mission_context(self, mission_id: str) -> Optional[MissionContext]:
        """
        Crée et retourne un MissionContext depuis une Mission
        
        Args:
            mission_id: ID mission
        
        Returns:
            MissionContext si mission trouvée, None sinon
        """
        mission = self.get_mission(mission_id)
        
        if not mission:
            return None
        
        # Créer MissionContext basique depuis Mission
        now = datetime.now()
        context = MissionContext(
            mission_id=mission.mission_id,
            user_request=mission.user_request,
            created_at=mission.created_at,
            updated_at=now
        )
        
        # Ajouter fichiers créés si disponibles
        for filepath in mission.files_created:
            context.files_created[filepath] = ""  # Contenu non stocké dans Mission
        
        return context
