from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.gemini_api_key,
    task_type="retrieval_document",
)

query_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.gemini_api_key,
    task_type="retrieval_query",
)


def get_embedding(text: str) -> list[float]:
    try:
        return embeddings.embed_query(text.replace("\n", " ").strip())
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise RuntimeError(f"Embedding generation failed: {str(e)}")


def get_query_embedding(text: str) -> list[float]:
    try:
        return query_embeddings.embed_query(text.replace("\n", " ").strip())
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise RuntimeError(f"Query embedding generation failed: {str(e)}")