"""
Retrieval Service
-----------------
Searches Supabase for the most semantically similar past support tickets.
"""

import logging
from typing import Optional
from app.core.supabase import get_supabase
from app.core.config import get_settings
from app.services.embedding_service import get_query_embedding

logger = logging.getLogger(__name__)
settings = get_settings()


def retrieve_similar_tickets(
    query: str,
    top_k: int = None,
    category: Optional[str] = None,
) -> list[dict]:
    top_k = top_k or settings.top_k
    logger.info(f"[Retrieval] Embedding query: '{query[:60]}'")
    query_vector = get_query_embedding(query)

    supabase = get_supabase()
    rpc_params = {
        "query_embedding": query_vector,
        "match_threshold": settings.similarity_threshold,
        "match_count": top_k,
    }
    if category:
        rpc_params["filter_category"] = category

    response = supabase.rpc("match_tickets", rpc_params).execute()
    tickets = response.data or []

    logger.info(f"[Retrieval] Found {len(tickets)} tickets above threshold {settings.similarity_threshold}")
    for i, t in enumerate(tickets):
        logger.debug(f"[Retrieval] #{i+1} score={t.get('similarity',0):.3f} id={t.get('id')} q='{t.get('user_query','')[:50]}'")

    return [
        {
            "id": str(t["id"]),
            "user_query": t["user_query"],
            "agent_response": t["agent_response"],
            "category": t.get("category", "general"),
            "similarity_score": round(float(t.get("similarity", 0)), 3),
            "created_at": t.get("created_at"),
        }
        for t in tickets
    ]