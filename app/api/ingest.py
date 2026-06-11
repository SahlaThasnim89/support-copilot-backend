from fastapi import APIRouter, HTTPException
from app.models.schemas import TicketCreate, TicketResponse
from app.services.embedding_service import get_embedding
from app.core.supabase import get_supabase
import logging
from datetime import datetime, timezone
 
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/ingest", response_model=TicketResponse)
async def ingest_ticket(ticket: TicketCreate):
    """
    Store a single support ticket with its embedding.
 
    What happens:
    1. Combine user_query + agent_response into one text for embedding
    2. Generate a 372-dim vector from gemini-embedding-001
    3. Store ticket + vector in Supabase support_tickets table
    """
    supabase = get_supabase()
 
    # Combine both sides of the conversation for a richer embedding
    combined_text = f"Customer: {ticket.user_query}\nAgent: {ticket.agent_response}"
 
    try:
        embedding = get_embedding(combined_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")
 
    try:
        result = supabase.table("support_tickets").insert({
            "user_query": ticket.user_query,
            "agent_response": ticket.agent_response,
            "category": ticket.category or "general",
            "metadata": ticket.metadata or {},
            "embedding": embedding,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
 
        data = result.data[0]
        logger.info(f"[Ingest] Ticket stored: id={data['id']}")
 
        return TicketResponse(
            id=str(data["id"]),
            user_query=data["user_query"],
            agent_response=data["agent_response"],
            category=data["category"],
            created_at=data["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase insert failed: {str(e)}")


@router.post("/ingest/bulk")
async def ingest_bulk(tickets: list[TicketCreate]):
    """Store multiple tickets at once. Used for initial data seeding."""
    results = []
    errors = []
 
    for i, ticket in enumerate(tickets):
        try:
            combined_text = f"Customer: {ticket.user_query}\nAgent: {ticket.agent_response}"
            embedding = get_embedding(combined_text)
 
            supabase = get_supabase()
            result = supabase.table("support_tickets").insert({
                "user_query": ticket.user_query,
                "agent_response": ticket.agent_response,
                "category": ticket.category or "general",
                "metadata": ticket.metadata or {},
                "embedding": embedding,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
 
            results.append(result.data[0]["id"])
            logger.info(f"[Ingest Bulk] {i+1}/{len(tickets)} done")
 
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
            logger.error(f"[Ingest Bulk] Failed at index {i}: {e}")
 
    return {
        "inserted": len(results),
        "failed": len(errors),
        "ids": results,
        "errors": errors,
    }
 
 
@router.get("/tickets")
async def list_tickets(limit: int = 20, category: str = None):
    """List stored tickets (without embeddings for readability)."""
    supabase = get_supabase()
    query = supabase.table("support_tickets").select(
        "id, user_query, agent_response, category, created_at"
    ).order("created_at", desc=True).limit(limit)
 
    if category:
        query = query.eq("category", category)
 
    result = query.execute()
    return {"tickets": result.data, "count": len(result.data)}
 
