from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    path: str
    type: str

class Project(BaseModel):
    id: int
    name: str
    path: str
    type: str
    has_projet_contexte: bool
    created_at: str
