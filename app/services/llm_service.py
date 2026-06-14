from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.config import get_settings
import logging
from typing import Generator

logger = logging.getLogger(__name__)
settings = get_settings()

groq_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=settings.groq_api_key,
    temperature=0.3,
    max_tokens=512,
)


gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.gemini_api_key,
    temperature=0.3,
    max_output_tokens=512,
)


def build_prompt(user_query: str, retrieved_tickets: list[dict]) -> str:
    context_block = ""
    for i, ticket in enumerate(retrieved_tickets, 1):
        context_block += f"""
--- Past Ticket #{i} (ID: {ticket['id']}) ---
Customer Query: {ticket['user_query']}
Agent Response: {ticket['agent_response']}
Category: {ticket.get('category', 'general')}
Similarity Score: {ticket.get('similarity_score', 0):.2f}
"""
    return f"""You are a helpful customer support assistant.
Your job is to suggest a reply to the customer's current query.
You MUST base your reply ONLY on the past support tickets provided below.
Do NOT use general knowledge. If the context is insufficient, say so clearly.

=== RETRIEVED PAST TICKETS ===
{context_block}

=== CURRENT CUSTOMER QUERY ===
{user_query}

=== YOUR TASK ===
Write a helpful, professional reply grounded in the past tickets above.
If no tickets are relevant, say: "I don't have enough past context. A human agent will assist you shortly."

Suggested Reply:"""


def generate_reply(user_query: str, retrieved_tickets: list[dict]) -> tuple[str, bool]:
    prompt = build_prompt(user_query, retrieved_tickets)
    message = [HumanMessage(content=prompt)]

    # Try Groq first
    try:
        response = groq_llm.invoke(message)
        logger.info("[LLM] Reply generated using Groq (LangChain)")
        return response.content.strip(), False
    except Exception as e:
        logger.warning(f"[LLM] Groq failed: {e} — switching to Gemini")

    # Fallback to Gemini
    try:
        response = gemini_llm.invoke(message)
        logger.info("[LLM] Reply generated using Gemini (LangChain fallback)")
        return response.content.strip(), True
    except Exception as e:
        logger.error(f"[LLM] Both failed: {e}")
        raise RuntimeError("Both LLM providers failed. Please try again later.")


def stream_reply(user_query: str, retrieved_tickets: list[dict]) -> Generator[str, None, None]:
    prompt = build_prompt(user_query, retrieved_tickets)
    message = [HumanMessage(content=prompt)]

    # Try Groq first
    try:
        for chunk in groq_llm.stream(message):
            yield chunk.content
        logger.info("[LLM] Streamed reply using Groq (LangChain)")
        return
    except Exception as e:
        logger.warning(f"[LLM] Groq streaming failed: {e} — switching to Gemini")

    # Fallback to Gemini
    try:
        for chunk in gemini_llm.stream(message):
            yield chunk.content
        logger.info("[LLM] Streamed reply using Gemini (LangChain fallback)")
    except Exception as e:
        logger.error(f"[LLM] Both streaming failed: {e}")
        raise RuntimeError("Both LLM providers failed. Please try again later.")