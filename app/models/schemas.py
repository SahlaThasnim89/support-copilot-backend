from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ── Ingest ────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    user_query: str
    agent_response: str
    category: Optional[str] = "general"
    metadata: Optional[dict] = {}


class TicketResponse(BaseModel):
    id: str
    user_query: str
    agent_response: str
    category: str
    created_at: datetime


# ── Suggest Reply ─────────────────────────────────────────────────────────────

class SuggestRequest(BaseModel):
    message: str


class Citation(BaseModel):
    ticket_id: str
    snippet: str
    similarity_score: float
    category: Optional[str] = None


class SuggestResponse(BaseModel):
    suggested_reply: str
    citations: List[Citation]
    retrieved_count: int          


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    query: str
    suggested_reply: str
    ticket_ids: List[str]
    rating: int                    # 1 = thumbs up, -1 = thumbs down


class FeedbackResponse(BaseModel):
    message: str
    recorded: bool