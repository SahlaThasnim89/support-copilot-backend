# 🤖 Support Copilot — Backend API

RAG-based support agent backend that suggests replies to customer queries using past support tickets.
Built with **FastAPI + Supabase (pgvector) + Google Gemini + Groq**.

---

## 🌐 Live URLs

| | URL |
|---|---|
| ⚙️ Backend API | `https://your-backend.onrender.com` |
| 📖 Swagger Docs | `https://your-backend.onrender.com/docs` |
| 🖥️ Frontend Repo | `https://github.com/SahlaThasnim89/support-copilot-frontend.git` |
| 🖥️ Frontend Live | `https://your-frontend.vercel.app` |

> Replace with your actual deployed URLs after deployment.

---

## 🏗️ Architecture Overview

```
Customer Query
      │
      ▼
┌─────────────────────────────────────────┐
│            FastAPI Backend              │
│                                         │
│  1. Embed query                         │
│     Gemini gemini-embedding-001         │
│     → 3072-dim vector                   │
│           │                             │
│  2. Vector search in Supabase           │
│     pgvector cosine similarity          │
│     → Returns top-3 similar tickets     │
│           │                             │
│  3. Build RAG prompt                    │
│     query + retrieved tickets           │
│     as context                          │
│           │                             │
│  4. Generate reply                      │
│     Groq (primary, free tier)           │
│     Gemini (fallback)                   │
│           │                             │
│  5. Return suggested_reply + citations  │
└─────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Framework | FastAPI (Python 3.12) |
| Database | Supabase (Postgres + pgvector) |
| Embeddings | Google Gemini `gemini-embedding-001` |
| LLM Primary | Groq `llama-3.1-8b-instant` (free tier) |
| LLM Fallback | Google Gemini `gemini-2.0-flash-lite` |
| Hosting | Render |

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                   ← FastAPI app entry point
│   ├── api/
│   │   ├── rag.py                ← POST /suggest-reply, POST /feedback
│   │   └── ingest.py             ← POST /ingest, /ingest/bulk, GET /tickets
│   ├── services/
│   │   ├── embedding_service.py  ← Gemini embeddings (3072-dim vectors)
│   │   ├── retrieval_service.py  ← Supabase pgvector similarity search
│   │   └── llm_service.py        ← Groq primary + Gemini fallback
│   ├── models/
│   │   └── schemas.py            ← Pydantic request/response models
│   └── core/
│       ├── config.py             ← Settings loaded from .env
│       └── supabase.py           ← Supabase client singleton
├── scripts/
│   ├── supabase_schema.sql       ← Run this first in Supabase SQL Editor
│   └── seed_tickets.py           ← Seeds 11 sample support tickets
├── requirements.txt
└── .env.example
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- Supabase account (free) — [supabase.com](https://supabase.com)
- Gemini API key (free) — [aistudio.google.com](https://aistudio.google.com)
- Groq API key (free) — [console.groq.com](https://console.groq.com)

---

### Step 1 — Supabase Setup

1. Go to [supabase.com](https://supabase.com) → create a new project
2. Go to **SQL Editor** and run the full contents of `scripts/supabase_schema.sql`
3. Go to **Settings → API** and copy:
   - **Project URL** → used as `SUPABASE_URL`
   - **Service Role Key** → used as `SUPABASE_SERVICE_KEY`

---

### Step 2 — Clone and Install

```bash
git clone https://github.com/yourusername/support-copilot-backend.git
cd support-copilot-backend

# Create virtual environment
py -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3 — Configure Environment

```bash
cp .env.example .env
```

Fill in your `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
TOP_K=3
SIMILARITY_THRESHOLD=0.50
```

---

### Step 4 — Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` → should return:
```json
{ "status": "ok", "message": "Support Copilot API is running" }
```

Visit `http://localhost:8000/docs` for Swagger UI.

---

### Step 5 — Seed Sample Tickets

Open a new terminal:
```bash
venv\Scripts\activate
py scripts/seed_tickets.py
```

This inserts 11 sample support tickets with embeddings into Supabase.

---

## 📡 API Reference

### `POST /suggest-reply`
Main RAG endpoint — embeds query, retrieves similar tickets, generates grounded reply.

**Request:**
```json
{
  "message": "I was charged twice for my order"
}
```

**Response:**
```json
{
  "suggested_reply": "I'm sorry for the inconvenience! A refund has been initiated and will reflect within 3-5 business days.",
  "citations": [
    {
      "ticket_id": "25bb2681-cdf3-4e00-a96a-fa8709411c59",
      "snippet": "Q: I was charged twice... | A: Refund within 3-5 days...",
      "similarity_score": 0.91,
      "category": "billing"
    }
  ],
  "retrieved_count": 3,
  "fallback_used": false
}
```

---

### `POST /ingest`
Store a single support ticket with its embedding.

**Request:**
```json
{
  "user_query": "I cannot log in to my account",
  "agent_response": "Please reset your password using the Forgot Password link.",
  "category": "account",
  "metadata": { "priority": "high", "source": "web_chat" }
}
```

---

### `POST /ingest/bulk`
Store multiple tickets at once. Accepts an array of ticket objects.

---

### `GET /tickets`
List all stored tickets.

| Query Param | Type | Description |
|---|---|---|
| `limit` | int | Number of tickets to return (default: 20) |
| `category` | string | Filter by category (billing, account, shipping, technical) |

---

### `POST /feedback`
Submit 👍/👎 feedback on a suggestion (bonus feature).

**Request:**
```json
{
  "query": "I was charged twice for my order",
  "suggested_reply": "A refund has been initiated...",
  "ticket_ids": ["25bb2681-cdf3-4e00-a96a-fa8709411c59"],
  "rating": 1
}
```

---

## 🚀 Deployment on Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** 3.12
5. Add all environment variables from your `.env`
6. Click **Deploy**

---

## 🎯 Design Decisions & Tradeoffs

**Why combine user_query + agent_response for embedding?**
Embedding both sides of the conversation gives richer semantic context than embedding just the query. This improves retrieval quality for paraphrased or partial queries.

**Why similarity threshold = 0.50?**
After testing, 0.70 was too strict for a small dataset — it missed valid paraphrased queries like "My order hasn't arrived" vs "My order has not arrived yet". 0.50 balances precision and recall at this scale. Fully tunable via `SIMILARITY_THRESHOLD` in `.env`.

**Why Groq as primary LLM?**
Gemini's free tier has strict per-minute quotas causing frequent `429 RESOURCE_EXHAUSTED` errors. Groq offers 14,400 free requests/day with higher rate limits — far more reliable for demos. Gemini remains as automatic fallback.

**Why no ivfflat index?**
The `ivfflat` index in pgvector supports a maximum of 2000 dimensions. Since `gemini-embedding-001` produces 3072-dim vectors, we use exact nearest-neighbor search. For a demo-scale dataset this has zero performance impact.

**Why true RAG instead of full-context prompting?**
The assignment explicitly requires embedding + retrieval. More importantly, RAG prevents hallucinations by grounding every response in real past tickets, making the system trustworthy and auditable via citations.

---

## ⚠️ Known Limitations

- **Small dataset** — Only 11 seed tickets; real systems need thousands for good coverage
- **No re-ranking** — Tickets ranked by cosine similarity only; a cross-encoder would improve precision
- **Single-turn** — No conversation history; each query is treated independently
- **Cold start** — Render free tier spins down after inactivity; first request may take ~30 seconds
- **Gemini quota** — Free tier has strict limits; Groq fallback handles this automatically

---

## 🌟 Bonus Features

- ✅ **👍 👎 Feedback system** — stores ratings in Supabase `feedback` table
- ✅ **Category-based metadata filtering** — filter retrieval by ticket category
- ✅ **Automatic LLM fallback** — Groq → Gemini, seamless to the user
- ✅ **Similarity score transparency** — every citation shows its match score
- ✅ **Debug logging** — all retrieved context logged server-side for debuggability

---

## 🧪 Sample Test Queries

```bash
# Using curl
curl -X POST http://localhost:8000/suggest-reply \
  -H "Content-Type: application/json" \
  -d '{"message": "I was charged twice for my order"}'
```

**Queries that work well with seed data:**
```
"I was charged twice for my order"
"My payment failed but money was deducted"
"I forgot my password and cannot log in"
"My order has not arrived yet"
"The app keeps crashing at checkout"
"I received the wrong item"
"How do I get a refund for my cancelled order"
```
