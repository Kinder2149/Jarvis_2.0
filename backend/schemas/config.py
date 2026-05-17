from pydantic import BaseModel
from typing import Optional

class ApiKeys(BaseModel):
    openrouter_key: str = ""
    anthropic_key: str = ""
    google_key: str = ""
    web_search_key: str = ""

class ModelPreferences(BaseModel):
    routing: str = "google/gemini-2.5-flash"
    structuring: str = "google/gemini-2.5-flash"
    code: str = "anthropic/claude-haiku-4.5"
    analysis: str = "anthropic/claude-sonnet-4.5"

class ChatConfig(BaseModel):
    model: str = "anthropic/claude-sonnet-4.5"
    methodo_path: str = "C:\\DEV\\METHODO"
    session_note: str = ""
    system_prompt_preset: str = ""

class Config(BaseModel):
    api_keys: ApiKeys
    model_preferences: ModelPreferences
    chat: Optional[ChatConfig] = None
