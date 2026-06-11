from google import genai
from google.genai import types
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

client = genai.Client(api_key=settings.gemini_api_key)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 3072


def get_embedding(text: str) -> list[float]:
    try:
        text = text.replace("\n", " ").strip()
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return result.embeddings[0].values
    except Exception as e:
        logger.error(f"Gemini embedding failed: {e}")
        raise RuntimeError(f"Embedding generation failed: {str(e)}")


def get_query_embedding(text: str) -> list[float]:
    try:
        text = text.replace("\n", " ").strip()
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return result.embeddings[0].values
    except Exception as e:
        logger.error(f"Gemini query embedding failed: {e}")
        raise RuntimeError(f"Query embedding generation failed: {str(e)}")