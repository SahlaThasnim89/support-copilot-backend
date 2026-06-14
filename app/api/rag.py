from fastapi import APIRouter, HTTPException
from app.models.schemas import SuggestRequest, SuggestResponse, Citation, FeedbackRequest, FeedbackResponse
from app.services.retrieval_service import retrieve_similar_tickets
from app.services.llm_service import generate_reply, stream_reply
from app.core.supabase import get_supabase
from app.services.cache_service import get_cached, set_cache, get_cache_stats
import logging
from app.services.observability_service import get_langfuse
import time
import json
 
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

    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info(f"[API] New query: '{query[:80]}'")

    # Cache check
    cached = get_cached(query)
    if cached:
        logger.info("[API] Returning cached response")
        return SuggestResponse(**cached)

    
    lf = get_langfuse()
    trace_start = time.time()
 

    # ── Retrieve similar tickets ────────────────────────────────────
    retrieval_start = time.time()
    try:
        tickets = retrieve_similar_tickets(query)
    except Exception as e:
        logger.error(f"[API] Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")
    retrieval_time = round(time.time() - retrieval_start, 2)
 
    # ── No tickets found edge case ────────────────────────────────────
    if not tickets:
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
    llm_start = time.time()
    try:
        suggested_reply, fallback_used = generate_reply(query, tickets)
    except Exception as e:
        logger.error(f"[API] LLM generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    llm_time = round(time.time() - llm_start, 2)
    total_time = round(time.time() - trace_start, 2)
 
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
 

    try:
        if lf:
            with lf.start_as_current_observation(
                name="rag-pipeline",
                input={"query": query},
            ) as span:
                with span.start_as_current_observation(
                    name="retrieval",
                    input={"query": query},
                ) as retrieval_span:
                    retrieval_span.update(
                        output={"tickets_found": len(tickets)},
                        metadata={"latency_seconds": retrieval_time}
                    )
                with span.start_as_current_observation(
                    name="llm-generation",
                    input={"query": query},
                ) as llm_span:
                    llm_span.update(
                        output={"reply": suggested_reply, "fallback_used": fallback_used},
                        metadata={"latency_seconds": llm_time}
                    )
                span.update(
                    output={"suggested_reply": suggested_reply, "retrieved_count": len(tickets)},
                    metadata={"total_latency_seconds": total_time}
                )
    except Exception as e:
        logger.warning(f"[Langfuse] Tracing failed: {e}")


    # ── Store in cache ────────────────────────────────────────────────────────────
    set_cache(query, {
        "suggested_reply": suggested_reply,
        "citations": [c.model_dump() for c in citations],
        "retrieved_count": len(tickets),
        "fallback_used": fallback_used,
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


@router.post("/suggest-reply/stream")
async def suggest_reply_stream(request: SuggestRequest):
    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info(f"[API] Stream query: '{query[:80]}'")

    try:
        tickets = retrieve_similar_tickets(query)
    except Exception as e:
        logger.error(f"[API] Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

    citations = [
        Citation(
            ticket_id=t["id"],
            snippet=f"Q: {t['user_query'][:100]} | A: {t['agent_response'][:150]}",
            similarity_score=t["similarity_score"],
            category=t.get("category"),
        )
        for t in tickets
    ]

    if not tickets:
        async def fallback_stream():
            yield f"data: {json.dumps({'token': 'I dont have enough past context. A human agent will assist you shortly.', 'done': False})}\n\n"
            yield f"data: {json.dumps({'done': True, 'citations': [], 'retrieved_count': 0})}\n\n"
        return StreamingResponse(fallback_stream(), media_type="text/event-stream")

    async def generate():
        full_reply = ""
        try:
            for token in stream_reply(query, tickets):
                full_reply += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

            # Send final event with citations
            yield f"data: {json.dumps({'done': True, 'citations': [c.model_dump() for c in citations], 'retrieved_count': len(tickets)})}\n\n"

            # Cache the full reply
            set_cache(query, {
                "suggested_reply": full_reply,
                "citations": [c.model_dump() for c in citations],
                "retrieved_count": len(tickets),
                "fallback_used": False,
            })
            logger.info(f"[API] Stream complete | tokens={len(full_reply)} | tickets={len(tickets)}")

        except Exception as e:
            logger.error(f"[API] Stream failed: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
