from langfuse import Langfuse
from app.core.config import get_settings
import logging

logger=logging.getLogger(__name__)
settings=get_settings()

langfuse=Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)

def create_trace(query:str):
    return langfuse.trace(
        name="rag-pipeline",
        input={"query": query},
    )