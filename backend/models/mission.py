"""
Modèle Mission - JARVIS 2.0
Gestion des missions avec phases et états asynchrones
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MissionStatus(str, Enum):
    """États possibles d'une mission"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"  # Attente validation USER
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionPhase(str, Enum):
    """Phases du workflow mission"""
    ANALYSE = "analyse"              # JARVIS_Maître analyse demande
    ARCHITECTURE = "architecture"    # ARCHITECTE propose architecture
    VALIDATION_ARCHI = "validation_architecture"  # Attente validation USER
    GENERATION_CODE = "generation_code"  # CODEUR génère code
    GENERATION_TESTS = "generation_tests"  # TESTEUR génère tests
    VALIDATION_CODE = "validation_code"  # VALIDATEUR valide
    CORRECTION = "correction"        # CODEUR corrige si INVALIDE
    FINALISATION = "finalisation"    # JARVIS_Maître finalise


class Mission(BaseModel):
    """
    Modèle Mission avec gestion états asynchrones
    
    Workflow complet :
    1. ANALYSE → JARVIS_Maître analyse demande
    2. ARCHITECTURE → ARCHITECTE propose
    3. VALIDATION_ARCHI → Attente validation USER (status=VALIDATING)
    4. GENERATION_CODE → CODEUR génère
    5. GENERATION_TESTS → TESTEUR génère tests
    6. VALIDATION_CODE → VALIDATEUR valide
    7. CORRECTION → Si INVALIDE, CODEUR corrige
    8. FINALISATION → Mission complétée
    """
    
    mission_id: str = Field(..., description="ID unique mission")
    user_request: str = Field(..., description="Demande utilisateur originale")
    project_path: str = Field(..., description="Chemin projet")
    
    status: MissionStatus = Field(default=MissionStatus.PENDING)
    current_phase: Optional[MissionPhase] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    
    # Flags validation
    architecture_validated: bool = False
    code_validated: bool = False
    tests_validated: bool = False
    
    # Données en attente validation USER
    pending_validation: Optional[dict] = None
    
    # Gestion erreurs
    error_count: int = 0
    last_error: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Vérifie si mission est complète"""
        return (
            self.architecture_validated and
            self.code_validated and
            self.tests_validated and
            len(self.files_created) > 0
        )
    
    def mark_completed(self):
        """Marque mission comme complétée"""
        self.status = MissionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.current_phase = MissionPhase.FINALISATION
    
    def mark_failed(self, reason: str):
        """Marque mission comme échouée"""
        self.status = MissionStatus.FAILED
        self.error_count += 1
        self.last_error = reason
    
    def request_validation(self, validation_type: str, data: dict):
        """Demande validation utilisateur"""
        self.status = MissionStatus.VALIDATING
        self.pending_validation = {
            "type": validation_type,
            "data": data,
            "requested_at": datetime.now().isoformat()
        }
    
    def approve_validation(self):
        """Approuve validation en attente"""
        if self.pending_validation:
            validation_type = self.pending_validation.get("type")
            
            if validation_type == "architecture":
                self.architecture_validated = True
                self.current_phase = MissionPhase.GENERATION_CODE
            elif validation_type == "code":
                self.code_validated = True
                self.current_phase = MissionPhase.GENERATION_TESTS
            
            self.pending_validation = None
            self.status = MissionStatus.IN_PROGRESS
    
    def reject_validation(self):
        """Rejette validation en attente"""
        if self.pending_validation:
            validation_type = self.pending_validation.get("type")
            
            if validation_type == "architecture":
                self.current_phase = MissionPhase.ARCHITECTURE
            elif validation_type == "code":
                self.current_phase = MissionPhase.CORRECTION
            
            self.pending_validation = None
            self.status = MissionStatus.IN_PROGRESS
