from app.core.supabase import get_supabase
from app.core.config import get_settings
from app.services.embedding_service import get_query_embedding
import logging

logger = logging.getLogger(__name__)
settings = get_settings()



def retrieve_similar_tickets(query: str, top_k: int = 3) -> list[dict]:
    """
    Uses LangChain SupabaseVectorStore to retrieve top-k similar tickets.
    Returns same dict format your existing router expects.
    """
    try:
        embedding = get_query_embedding(query.replace("\n", " ").strip())

        supabase = get_supabase()
        response = supabase.rpc("match_tickets", {
            "query_embedding": embedding,
            "match_threshold": 0.65,
            "match_count": top_k,
        }).execute()


        tickets = []
        for row in response.data:
            tickets.append({
                "id": row["id"],
                "user_query": row["user_query"],
                "agent_response": row["agent_response"],
                "category": row.get("category"),
                "similarity_score": row["similarity"],
            })

        logger.info(f"[Retrieval] Found {len(tickets)} tickets")
        return tickets

    except Exception as e:
        logger.error(f"[Retrieval] Failed: {e}")
        raise