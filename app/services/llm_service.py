from google import genai
from google.genai import types
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

client = genai.Client(api_key=settings.gemini_api_key)


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


def generate_with_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=512,
        ),
    )
    return response.text.strip()


def generate_with_groq(prompt: str) -> str:
    from groq import Groq
    groq_client = Groq(api_key=settings.groq_api_key)
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


def generate_reply(user_query: str, retrieved_tickets: list[dict]) -> tuple[str, bool]:
    prompt = build_prompt(user_query, retrieved_tickets)

    # Try Groq first (reliable free tier)
    try:
        reply = generate_with_groq(prompt)
        logger.info("[LLM] Reply generated using Groq")
        return reply, False
    except Exception as e:
        logger.warning(f"[LLM] Groq failed: {e} — switching to Gemini")

    # Fallback to Gemini
    try:
        reply = generate_with_gemini(prompt)
        logger.info("[LLM] Reply generated using Gemini (fallback)")
        return reply, True
    except Exception as e:
        logger.error(f"[LLM] Both failed: {e}")
        raise RuntimeError("Both LLM providers failed. Please try again later.")