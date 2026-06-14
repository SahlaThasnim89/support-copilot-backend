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

    # RAG
    upstash_redis_rest_url: str = ""      
    upstash_redis_rest_token: str = "" 

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"   
 
    class Config:
        env_file = ".env"
 
 
@lru_cache()
def get_settings() -> Settings:
    return Settings()