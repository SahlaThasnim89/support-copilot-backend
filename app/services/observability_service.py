from langfuse import Langfuse
from app.core.config import get_settings
import logging

logger=logging.getLogger(__name__)
settings=get_settings()

try:
    langfuse = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
except Exception as e:
    logger.warning(f"[Langfuse] Init failed: {e}")
    langfuse = None

class NoOpTrace:
    """Fallback when Langfuse is unavailable"""
    def span(self, **kwargs): return self
    def end(self, **kwargs): return self
    def update(self, **kwargs): return self


def create_trace(query: str):
    try:
        if langfuse is None:
            return NoOpTrace()
        trace = langfuse.start_trace(
            name="rag-pipeline",
            input={"query": query},
        )
        return trace
    except Exception as e:
        logger.warning(f"[Langfuse] Trace creation failed: {e}")
        return NoOpTrace()