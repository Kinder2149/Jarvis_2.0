from pydantic import BaseModel
from enum import Enum

class SessionStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_VALIDATION = "WAITING_VALIDATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_VALIDATION = "WAITING_VALIDATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class Session(BaseModel):
    id: int
    project_id: int
    workflow_type: str
    status: SessionStatus
    current_step_index: int
    created_at: str

class PipelineStep(BaseModel):
    id: int
    session_id: int
    step_index: int
    step_name: str
    step_display_name: str
    model_type: str
    model_used: str | None
    status: StepStatus
    input_data: str | None
    output_data: str | None
    requires_validation: bool
    validated_at: str | None
    created_at: str

class StepValidation(BaseModel):
    approved: bool
    edited_output: str | None = None

class StartPipeline(BaseModel):
    project_id: int
    workflow_type: str
    initial_input: str | None = None
