"""
Modèle MissionContext - Contexte partagé entre agents
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class ArchitectureDecision(BaseModel):
    """Décision architecturale prise par ARCHITECTE."""
    files_to_create: List[str]
    stack: Dict[str, str]  # {"backend": "FastAPI", "storage": "JSON"}
    patterns: List[str]  # ["CRUD", "Storage JSON"]
    file_specs: Dict[str, Dict]  # Specs détaillées par fichier
    justification: str


class ValidationAttempt(BaseModel):
    """Tentative de validation."""
    attempt_number: int
    timestamp: datetime
    status: str  # "VALID" | "INVALID"
    errors: List[str]
    corrections_applied: List[str] = Field(default_factory=list)


class MissionContext(BaseModel):
    """Contexte partagé entre tous les agents d'une mission."""
    mission_id: str
    user_request: str
    
    # Phase ARCHITECTE
    architecture: Optional[ArchitectureDecision] = None
    
    # Phase CODEUR
    files_created: Dict[str, str] = Field(default_factory=dict)  # {filepath: content}
    files_pending: List[str] = Field(default_factory=list)
    
    # Phase TESTEUR
    tests_created: Dict[str, str] = Field(default_factory=dict)
    
    # Phase VALIDATEUR
    validation_history: List[ValidationAttempt] = Field(default_factory=list)
    current_status: str = "PENDING"  # "PENDING" | "IN_PROGRESS" | "VALID" | "INVALID"
    
    # Métadonnées
    created_at: datetime
    updated_at: datetime
    
    def add_file(self, filepath: str, content: str):
        """Ajoute un fichier créé."""
        self.files_created[filepath] = content
        if filepath in self.files_pending:
            self.files_pending.remove(filepath)
        self.updated_at = datetime.now()
    
    def add_validation_attempt(self, status: str, errors: List[str], corrections: List[str] = None):
        """Ajoute une tentative de validation."""
        attempt = ValidationAttempt(
            attempt_number=len(self.validation_history) + 1,
            timestamp=datetime.now(),
            status=status,
            errors=errors,
            corrections_applied=corrections or []
        )
        self.validation_history.append(attempt)
        self.current_status = status
        self.updated_at = datetime.now()
    
    def get_summary(self) -> str:
        """Résumé du contexte pour les agents."""
        arch_files = self.architecture.files_to_create if self.architecture else []
        arch_stack = self.architecture.stack if self.architecture else {}
        
        return f"""
MISSION : {self.mission_id}
DEMANDE : {self.user_request}

ARCHITECTURE :
- Fichiers prévus : {arch_files}
- Stack : {arch_stack}

PROGRESSION :
- Fichiers créés : {len(self.files_created)}/{len(arch_files)}
- Fichiers en attente : {self.files_pending}
- Tentatives validation : {len(self.validation_history)}
- Statut : {self.current_status}

HISTORIQUE VALIDATION :
{chr(10).join([f"  Tentative {v.attempt_number}: {v.status} - {len(v.errors)} erreurs" for v in self.validation_history])}
"""
