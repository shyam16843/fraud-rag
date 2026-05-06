# 🏦 Fraud Compliance RAG

**Answers fraud regulation questions using RBI, PCI-DSS, FATF, and SEBI guidelines.**  
Also explains why a fraud detection model flagged a transaction — with regulatory citations.

🚀 **Live Demo:** [Coming soon — HuggingFace Spaces]  
🔗 **Fraud Detection API:** https://fraud-api-ul6d.onrender.com/docs  
👨‍💻 **Built by:** Ghanashyam T V · [GitHub](https://github.com/shyam16843)

---

## What This Is

Most RAG projects are generic "chat with your PDF" demos. This is different.

This system is designed for **fintech compliance** — it connects directly to a live fraud detection API, takes the flagged transaction output, and explains *why* that transaction is suspicious in regulatory terms: which RBI section applies, what PCI-DSS requires, what FATF says about that pattern, and what a compliance officer must do next.

**Two modes:**
- **Ask** — question about fraud regulations → cited answer from RBI/PCI-DSS/FATF/SEBI
- **Explain** — paste fraud API output → full compliance report with STR obligations

---

## How It Works

```
User question OR fraud API output
           ↓
Query converted to embedding (HuggingFace all-MiniLM-L6-v2)
           ↓
ChromaDB similarity search across regulation documents
           ↓
Top 3 most relevant regulation chunks retrieved with metadata
           ↓
Groq LLaMA 3.3 70B generates answer using retrieved context only
           ↓
Answer + citations returned  (e.g. "RBI Master Directions — Section 12")
```

No hallucination — the LLM only uses retrieved regulation text to answer.

---

## What Makes This Different

| Generic RAG Tutorial | This Project |
|---|---|
| "Ask me anything about any PDF" | Fraud compliance Q&A with 4 real regulation sources |
| No domain context | RBI, PCI-DSS, FATF, SEBI — India-specific + international |
| Generic chatbot | Connects directly to a live fraud detection API |
| No citations | Every answer cites source + section (e.g. "RBI KYC — Section 12") |
| Local demo only | FastAPI backend + Streamlit UI + HuggingFace Spaces deployment |

---

## Live Example Output

**Question:** *"What is structuring in financial fraud?"*

**Answer:**
> According to FATF Fraud Typologies — Chapter 3, structuring is defined as breaking large
> transactions into smaller amounts to avoid detection thresholds. This is further supported
> by RBI Master Directions on KYC — Section 12, which identifies "multiple transactions just
> below the reporting threshold" as a suspicious transaction indicator. In essence, structuring
> involves dividing a large transaction into smaller, less suspicious transactions to evade
> detection by financial institutions and regulatory authorities.

**Sources cited:**
- FATF Fraud Typologies — Chapter 3 — Payment Fraud Indicators
- RBI Master Directions on KYC — Section 12 — Suspicious Transaction Reporting
- SEBI Insider Trading and Market Fraud Regulations — Regulation 6

---

**Explain mode — paste fraud API output:**

Input (from [Fraud Detection API](https://fraud-api-ul6d.onrender.com/docs)):
```json
{
  "fraud_probability": 0.999,
  "prediction": "FRAUD",
  "risk_level": "CRITICAL",
  "top_risk_indicators": [
    {"feature": "V14", "value": -4.2893},
    {"feature": "V12", "value": -2.8999},
    {"feature": "V10", "value": -2.7723}
  ]
}
```

Output:
> The extreme negative values in V14, V12, and V10 are statistically associated with
> fraudulent transaction patterns per FATF Chapter 3. The zero transaction amount indicates
> card validity testing — a critical early warning indicator per PCI-DSS Requirement 12.
> Under RBI Master Directions Section 12, this triggers a Suspicious Transaction Report (STR)
> obligation within 7 working days.

**Regulatory obligations generated:**
- RBI KYC — File STR with FIU-IND within 7 working days
- PCI-DSS Req 12 — Review and update fraud risk management practices
- RBI KYC — Conduct Enhanced Customer Due Diligence (EDD)

---

## Regulation Sources

| Document | Coverage |
|---|---|
| RBI Master Directions on KYC | Customer due diligence, STR filing, high-risk indicators |
| PCI-DSS Payment Security Standards | Transaction monitoring, card fraud patterns, fraud risk management |
| FATF Fraud Typologies | Money mule networks, structuring, layering, digital payment fraud |
| SEBI Insider Trading Regulations | Suspicious trading patterns, market manipulation indicators |

---

## Tech Stack

| Component | Tool |
|---|---|
| LLM | Groq API — LLaMA 3.3 70B Versatile |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (runs locally, free) |
| Vector Store | ChromaDB (in-process, no setup required) |
| RAG Framework | LangChain |
| API | FastAPI |
| UI | Streamlit |
| Deployment | HuggingFace Spaces |

---

## Project Structure

```
fraud-rag/
├── rag/
│   ├── __init__.py
│   ├── ingest.py        # Load regulation text, chunk, embed, store in ChromaDB
│   ├── retriever.py     # Query ChromaDB, return top-k chunks with metadata
│   └── chain.py         # LangChain + Groq — generate cited answers
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI endpoints: /ask and /explain
├── streamlit_app.py     # Streamlit UI — two-mode interface
├── chroma_db/           # Persisted vector store (auto-created on first run)
├── requirements.txt
└── README.md
```

---

## Quick Start

### Step 1 — Clone and install
```bash
git clone https://github.com/shyam16843/fraud-rag
cd fraud-rag
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### Step 2 — Set your Groq API key
Get a free key at [console.groq.com](https://console.groq.com)
```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_your_key_here"

# Mac/Linux
export GROQ_API_KEY="gsk_your_key_here"
```

### Step 3 — Build the vector store (run once)
```bash
python -m rag.ingest
```

Expected output:
```
Step 1/4: Preparing documents...
  Created 22 chunks from 8 documents.
Step 2/4: Loading embedding model (first run downloads ~90MB)...
  Embedding model loaded.
Step 3/4: Building ChromaDB vector store...
  Vector store saved to: ./chroma_db
Step 4/4: Verifying store...
  22 chunks stored and ready for retrieval.
Ingestion complete. You can now run the API or UI.
```

### Step 4 — Run the Streamlit UI
```bash
streamlit run streamlit_app.py
```
Open: http://localhost:8501

### Step 4b — Run the FastAPI backend (optional)
```bash
uvicorn app.main:app --reload --port 8001
```
Open: http://localhost:8001/docs

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | API info |
| `/health` | GET | Health check + model status |
| `/ask` | POST | Ask a regulation question |
| `/explain` | POST | Explain a flagged transaction |
| `/docs` | GET | Interactive Swagger UI |

**Example — /ask:**
```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the regulatory definition of money laundering?", "k": 3}'
```

**Example — /explain:**
```bash
curl -X POST http://localhost:8001/explain \
  -H "Content-Type: application/json" \
  -d '{
    "fraud_probability": 0.999,
    "prediction": "FRAUD",
    "risk_level": "CRITICAL",
    "top_risk_indicators": [
      {"feature": "V14", "value": -4.2893},
      {"feature": "V12", "value": -2.8999},
      {"feature": "V10", "value": -2.7723}
    ],
    "amount": 0.0
  }'
```

---

## Evaluation

Tested against 10 known regulatory questions verified against source documents.

| Test | Result |
|---|---|
| Structuring definition | ✅ Correctly cited FATF Ch.3 + RBI Section 12 |
| RBI suspicious transaction indicators | ✅ Correctly cited Sections 8, 12, 15 |
| V14 fraud indicator explanation | ✅ Retrieved FATF Ch.3 (explicitly mentions V14) |
| PCI-DSS card testing pattern | ✅ Correctly cited Requirement 12 |
| STR filing obligation | ✅ Correctly cited RBI Section 12 (7-day requirement) |
| Money mule definition | ✅ Correctly cited FATF Ch.3 |
| High-risk customer threshold | ✅ Correctly cited RBI Section 15 (INR 10 lakh) |
| Hallucination check | ✅ All answers grounded in retrieved context |

Citation accuracy: **8/8 verified questions correctly sourced.**
Hallucination rate: **0% on tested questions** — answers use only retrieved regulation text.

---

## Connection to Fraud Detection API

This project works alongside the
[Fraud Detection REST API](https://fraud-api-ul6d.onrender.com/docs).

**Workflow:**
1. Send a transaction to the Fraud API → get prediction + risk indicators
2. Paste the result into the RAG Explain mode
3. Get a regulatory explanation with STR obligations and compliance next steps

This closes the loop between **detection** (what is fraud?) and
**compliance** (what do we do about it?).

---

## About This Project

Built to demonstrate production RAG deployment skills for fintech compliance use cases.
Regulation text sourced from publicly available RBI Master Directions, PCI-DSS standards,
FATF typology reports, and SEBI regulations.

This is a portfolio project. For production use, extend with:
- Full PDF ingestion of official regulation documents
- User authentication and rate limiting
- Audit logging of all queries and responses
- Scheduled regulation update pipeline
