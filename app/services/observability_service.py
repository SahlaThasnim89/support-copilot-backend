from langfuse import Langfuse
from app.core.config import get_settings
import logging

logger=logging.getLogger(__name__)
settings=get_settings()

try:
    langfuse = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url,
    )
    logger.info("[Langfuse] Client initialized successfully")
except Exception as e:
    logger.warning(f"[Langfuse] Init failed: {e}")
    langfuse = None


def get_langfuse():
    return langfuse