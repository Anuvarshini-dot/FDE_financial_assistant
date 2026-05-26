# Finance Policy Assistant — AI-Powered RAG System

An enterprise-grade Retrieval-Augmented Generation (RAG) system that lets employees query
internal finance policy documents in natural language and receive accurate, grounded answers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FINANCE POLICY ASSISTANT                  │
├──────────────────────┬──────────────────────────────────────┤
│      FRONTEND        │            BACKEND                   │
│   (HTML/CSS/JS)      │          (FastAPI)                   │
│                      │                                      │
│  ┌──────────────┐    │   ┌──────────────────────────┐       │
│  │  Chat UI     │◄───┼───│   /query  endpoint       │       │
│  │  Source view │    │   │   /health endpoint       │       │
│  └──────────────┘    │   └────────────┬─────────────┘       │
│                      │                │                     │
└──────────────────────┘   ┌────────────▼─────────────┐       │
                           │   LangChain RAG Chain    │       │
                           │                          │       │
                           │  1. ConversationalChain  │       │
                           │  2. Memory (6-turn window│       │
                           │  3. Custom QA Prompt     │       │
                           └────────────┬─────────────┘       │
                                        │                     │
               ┌────────────────────────┼───────────────┐     │
               │                        │               │     │
   ┌───────────▼──────┐    ┌────────────▼──────┐  ┌─────▼───┐ │
   │  Document        │    │  FAISS Vector     │  │ OpenAI  │ │
   │  Processor       │    │  Store            │  │ GPT-4o  │ │
   │                  │    │                   │  │ mini    │ │
   │ • Load .txt docs │    │ • Similarity k=5  │  └─────────┘ │
   │ • Chunk 800/150  │    │ • Persisted index │              │
   │ • text-embed-3sm │    │                   │              │
   └──────────────────┘    └───────────────────┘              │
```

## Project Structure

```
Finanace assistant/
├── backend/
│   ├── app.py                  # FastAPI server & endpoints
│   ├── rag_pipeline.py         # LangChain RAG chain
│   ├── document_processor.py   # Chunking, embedding, FAISS
│   ├── requirements.txt
│   ├── .env                    # Your OpenAI key (create this)
│   └── vector_store/           # Auto-generated FAISS index
├── frontend/
│   ├── index.html              # Chat UI
│   ├── style.css               # Dark theme styles
│   └── app.js                  # API calls & rendering
├── documents/
│   ├── reimbursement_policy.txt
│   ├── travel_expense_rules.txt
│   ├── vendor_payment_procedures.txt
│   ├── tax_compliance_guidelines.txt
│   ├── procurement_approvals.txt
│   └── employee_finance_handbook.txt
├── start.ps1                   # PowerShell quick-start script
└── README.md
```

## Setup

### 1. Prerequisites
- Python 3.10+
- An OpenAI API key

### 2. Configure API Key
Create `backend/.env`:
```
OPENAI_API_KEY=sk-...your-key-here...
```

### 3. Install Dependencies
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start the Backend
```powershell
# From the backend/ folder (with venv active)
uvicorn app:app --reload --port 8000
```

Or use the quick-start script from the project root:
```powershell
.\start.ps1
```

### 5. Open the Frontend
Open `frontend/index.html` in your browser (no server needed — it calls the API directly).

---

## Technical Design Decisions

### Chunking Strategy
- **Chunk size**: 800 characters with 150-character overlap
- **Splitter**: `RecursiveCharacterTextSplitter` with separators `["\n\n", "\n", ". ", " "]`
- **Rationale**: Finance documents contain structured sections and numbered lists. This size captures
  complete policy clauses without exceeding the embedding model's context. The overlap ensures
  policy limits mentioned at section boundaries are not split across chunks.

### Retrieval Approach
- **Embedding model**: `text-embedding-3-small` (OpenAI) — high quality at low cost
- **Vector database**: FAISS (local, no infrastructure required, persisted to disk)
- **Search**: Similarity search with `k=5` top chunks per query
- **Multi-doc**: All 6 documents indexed together; source filename tracked in metadata

### Conversation Memory
- `ConversationBufferWindowMemory` with `k=6` turns — supports follow-up questions
- Condense prompt reformulates follow-up questions into standalone queries before retrieval

### Grounding & Hallucination Prevention
- System prompt explicitly instructs the LLM to answer **only** from retrieved context
- Fallback message directs users to the Finance team when context is insufficient
- `temperature=0.1` keeps responses factual and deterministic

### Limitations & Future Improvements
- **PDF support**: Current implementation handles `.txt` only; add `PyPDFLoader` for PDF ingestion
- **Hybrid search**: Combine dense (semantic) + sparse (BM25) retrieval for better keyword matching
- **Re-ranking**: Add a cross-encoder reranker after initial retrieval to improve precision
- **Multi-language**: Add translation layer for non-English queries
- **Auth**: Integrate SSO/OAuth for enterprise deployment
- **Analytics**: Log query patterns to identify coverage gaps in policy documents

## Sample Queries

| Query | Expected Source |
|-------|----------------|
| What is the meal reimbursement limit? | reimbursement_policy.txt |
| Can I fly business class internationally? | travel_expense_rules.txt |
| What approvals are needed for a $30,000 vendor payment? | vendor_payment_procedures.txt |
| What is the deadline to submit expense reports? | reimbursement_policy.txt |
| What documents are required for a $10,000 procurement? | procurement_approvals.txt |
| Are contractor payments subject to tax withholding? | tax_compliance_guidelines.txt |
| What is the hotel rate limit in New York? | travel_expense_rules.txt |
| How do I get a corporate purchase card? | employee_finance_handbook.txt |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check backend status |
| POST | `/query` | Submit a natural language question |
| POST | `/rebuild-index` | Force-rebuild the FAISS index |

### POST /query
**Request:**
```json
{ "question": "What is the reimbursement limit for client travel?" }
```
**Response:**
```json
{
  "answer": "The reimbursement limit for client entertainment meals is up to $150 per person...",
  "sources": [
    {
      "source": "reimbursement_policy.txt",
      "snippet": "Client entertainment meals: Up to $150 per person (requires manager pre-approval)..."
    }
  ]
}
```
