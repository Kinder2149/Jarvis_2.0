from pydantic import BaseModel, field_validator
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    path: str
    type: str
    local_path: str | None = None
    instructions: str = ""
    module_type: str = "dossier"
    category: Optional[str] = None
    parent_dossier_id: Optional[int] = None
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v, info):
        module_type = info.data.get('module_type')
        if module_type == 'code' and v is None:
            raise ValueError("category est obligatoire si module_type='code'")
        if v is not None and v not in ['applications_mobile', 'applications_web', 'Clients', 'intelligence_artificielle']:
            raise ValueError(f"category doit être l'une de: applications_mobile, applications_web, Clients, intelligence_artificielle")
        return v

class Project(BaseModel):
    id: int
    name: str
    path: str
    type: str
    local_path: str | None = None
    instructions: str = ""
    module_type: str = "dossier"
    category: Optional[str] = None
    parent_dossier_id: Optional[int] = None
    has_projet_contexte: bool
    created_at: str

class ProjectUpdate(BaseModel):
    local_path: str | None = None
    instructions: str | None = None
    parent_dossier_id: Optional[int] = None
