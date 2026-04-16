from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    path: str
    type: str
    local_path: str | None = None

class Project(BaseModel):
    id: int
    name: str
    path: str
    type: str
    local_path: str | None = None
    has_projet_contexte: bool
    created_at: str
