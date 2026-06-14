from fastapi import APIRouter, HTTPException
from app.models.schemas import SuggestRequest, SuggestResponse, Citation, FeedbackRequest, FeedbackResponse
from app.services.retrieval_service import retrieve_similar_tickets
from app.services.llm_service import generate_reply
from app.core.supabase import get_supabase
from app.services.cache_service import get_cached, set_cache, get_cache_stats
import logging
from app.services.observability_service import create_trace
 
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/suggest-reply", response_model=SuggestResponse)
async def suggest_reply(request: SuggestRequest):
    """
    Main RAG endpoint.
 
    Flow:
    1. Embed the incoming message
    2. Retrieve top-k similar past tickets from Supabase
    3. If no tickets found → return fallback message
    4. Build prompt with retrieved tickets as context
    5. Generate reply via Groq (Gemini fallback)
    6. Return reply + citations
    """
    query = request.message.strip()

    trace = create_trace(query)

    # Cache check
    cached = get_cached(query)
    if cached:
        trace.update(output={"source": "cache"})
        logger.info("[API] Returning cached response")
        return SuggestResponse(**cached)
 
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
 
    logger.info(f"[API] New query: '{query[:80]}'")

 
    # ── Retrieve similar tickets ────────────────────────────────────
    try:
        retrieval_span = trace.span(name="retrieval")
        tickets = retrieve_similar_tickets(query)
        retrieval_span.end(output={"tickets_found": len(tickets)})
    except Exception as e:
        trace.update(output={"error": str(e)})
        logger.error(f"[API] Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")
 
    # ── No tickets found edge case ────────────────────────────────────
    if not tickets:
        trace.update(output={"source": "fallback"})
        logger.warning("[API] No similar tickets found above threshold")
        return SuggestResponse(
            suggested_reply=(
                "I don't have enough past context to suggest a reply for this query. "
                "Please handle this manually or escalate to a senior agent."
            ),
            citations=[],
            retrieved_count=0,
            fallback_used=False,
        )
 
    # ── Generate reply with retrieved context ───────────────────────
    try:
        llm_span = trace.span(name="llm-generation")
        suggested_reply, fallback_used = generate_reply(query, tickets)
    except Exception as e:
        trace.update(output={"error": str(e)})
        logger.error(f"[API] LLM generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
 
    # ── Build citations ────────────────────────────────────────────────
    citations = [
        Citation(
            ticket_id=t["id"],
            snippet=f"Q: {t['user_query'][:100]} | A: {t['agent_response'][:150]}",
            similarity_score=t["similarity_score"],
            category=t.get("category"),
        )
        for t in tickets
    ]
 
    logger.info(f"[API] Reply generated | tickets={len(tickets)} | fallback={fallback_used}")
 
    # ── Store in cache ────────────────────────────────────────────────────────────
    set_cache(query, {
        "suggested_reply": suggested_reply,
        "citations": [c.model_dump() for c in citations],
        "retrieved_count": len(tickets),
        "fallback_used": fallback_used,
    })

    trace.update(output={
        "suggested_reply": suggested_reply,
        "retrieved_count": len(tickets),
        "fallback_used": fallback_used,
        "source": "rag",
    })

    return SuggestResponse(
        suggested_reply=suggested_reply,
        citations=citations,
        retrieved_count=len(tickets),
        fallback_used=fallback_used,
    )



@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Bonus: Thumbs up (1) / Thumbs down (-1) feedback.
    Stores feedback in Supabase for future retrieval improvement.
    """
    supabase = get_supabase()
    try:
        supabase.table("feedback").insert({
            "query": request.query,
            "suggested_reply": request.suggested_reply,
            "ticket_ids": request.ticket_ids,
            "rating": request.rating,
        }).execute()
        return FeedbackResponse(message="Feedback recorded. Thank you!", recorded=True)
    except Exception as e:
        logger.error(f"[Feedback] Failed to save: {e}")
        return FeedbackResponse(message="Failed to record feedback.", recorded=False)
 

@router.get("/cache/stats")
def cache_stats():
    """Returns number of cached queries."""
    return get_cache_stats()