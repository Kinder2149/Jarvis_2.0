"""
Modèles Pydantic pour API Missions
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class MissionStartRequest(BaseModel):
    """Requête démarrage mission"""
    user_request: str = Field(..., min_length=1, max_length=5000, description="Demande utilisateur")
    project_name: str = Field(..., min_length=1, max_length=100, description="Nom projet")
    project_path: str = Field(..., description="Chemin projet")


class MissionStartResponse(BaseModel):
    """Réponse démarrage mission"""
    success: bool
    mission_id: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    requires_user_validation: Optional[bool] = None
    architecture_doc: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    user_message: Optional[str] = None


class MissionValidateRequest(BaseModel):
    """Requête validation architecture"""
    approved: bool = Field(..., description="True si validé, False si rejeté")
    feedback: Optional[str] = Field(None, description="Feedback utilisateur (optionnel)")


class MissionValidateResponse(BaseModel):
    """Réponse validation architecture"""
    success: bool
    message: str
    mission_status: Optional[str] = None


class MissionContinueResponse(BaseModel):
    """Réponse continuation mission"""
    success: bool
    mode: str
    files_created: List[str]
    files_updated: Optional[List[str]] = None
    validation_result: str
    error: Optional[str] = None
    correction_attempts: Optional[int] = None


class MissionStatusResponse(BaseModel):
    """Réponse statut mission"""
    mission_id: str
    user_request: str
    project_path: str
    status: str
    current_phase: Optional[str] = None
    architecture_validated: bool
    code_validated: bool
    tests_validated: bool
    files_created: List[str]
    files_modified: List[str]
    error_count: int
    last_error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    pending_validation: Optional[dict] = None
