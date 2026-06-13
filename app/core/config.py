from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str
 
    # LLM
    gemini_api_key: str = ""
    groq_api_key: str = ""
 
    # RAG
    top_k: int = 3
    similarity_threshold: float = 0.65
 
    class Config:
        env_file = ".env"
 
 
@lru_cache()
def get_settings() -> Settings:
    return Settings()