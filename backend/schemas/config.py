from pydantic import BaseModel
from typing import Optional

class ApiKeys(BaseModel):
    openrouter_key: str = ""
    anthropic_key: str = ""
    google_key: str = ""
    web_search_key: str = ""
    fal_key: str = ""

class ModelPreferences(BaseModel):
    routing: str = "google/gemini-flash-2.0"
    structuring: str = "anthropic/claude-haiku-4-5"
    code: str = "anthropic/claude-sonnet-4-5"
    analysis: str = "anthropic/claude-opus-4"

class ChatConfig(BaseModel):
    model: str = "anthropic/claude-sonnet-4.5"
    methodo_path: str = "C:\\DEV\\METHODO"
    session_note: str = ""
    system_prompt_preset: str = ""

class Config(BaseModel):
    api_keys: ApiKeys
    model_preferences: ModelPreferences
    chat: Optional[ChatConfig] = None
