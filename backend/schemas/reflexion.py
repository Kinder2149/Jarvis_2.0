from enum import Enum
from pydantic import BaseModel
from typing import Optional, List


class LivrableType(str, Enum):
    MISSION_CODE = "mission_code"
    DECISION_FIGEE = "decision_figee"
    PLAN_MULTI_MISSIONS = "plan_multi_missions"


class ReflexionStatut(str, Enum):
    OUVERTE = "OUVERTE"
    EN_FIGEMENT = "EN_FIGEMENT"
    FIGEE = "FIGEE"
    ABANDONNEE = "ABANDONNEE"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    SANTE_CADRAGE = "sante_cadrage"


class CreateReflexion(BaseModel):
    project_id: int
    livrable_type: LivrableType


class ReflexionMessage(BaseModel):
    id: Optional[int] = None
    role: str
    content: str
    attachments: Optional[str] = None
    attachment_base64: Optional[str] = None
    attachment_filename: Optional[str] = None
    compacted: bool = False
    created_at: str


class SendMessage(BaseModel):
    content: str
    attachment_base64: Optional[str] = None
    attachment_filename: Optional[str] = None


class ProposerEdit(BaseModel):
    file_path: str
    new_content: str


class AppliquerEdit(BaseModel):
    file_path: str
    new_content: str
    confirmed: bool


class ReflexionSession(BaseModel):
    id: int
    project_id: int
    livrable_type: str
    titre: Optional[str] = None
    statut: str
    modele_utilise: str
    input_tokens_total: int
    output_tokens_total: int
    livrable_id: Optional[int] = None
    created_at: str
    updated_at: str
    frozen_at: Optional[str] = None


class ReflexionSessionWithMessages(ReflexionSession):
    messages: List[ReflexionMessage] = []


class CadrageHealth(BaseModel):
    verdict_global: str
    checks: List[dict]
