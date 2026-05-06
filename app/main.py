"""
main.py
FastAPI application exposing two endpoints:
  POST /ask     — general fraud regulation question
  POST /explain — paste fraud API output, get regulatory explanation
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from rag.chain import ask, explain

app = FastAPI(
    title="Fraud Compliance RAG API",
    description=(
        "Answers fraud regulation questions using RBI, PCI-DSS, FATF, and SEBI guidelines. "
        "Also explains fraud detection results in regulatory context."
    ),
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        example="What makes a transaction suspicious under RBI guidelines?",
        description="A question about fraud regulations."
    )
    k: Optional[int] = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of regulation chunks to retrieve (1-5)."
    )


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[str]


class RiskIndicator(BaseModel):
    feature: str = Field(..., example="V14")
    value: float = Field(..., example=-4.2893)


class ExplainRequest(BaseModel):
    fraud_probability: float = Field(..., ge=0.0, le=1.0, example=0.999)
    prediction: str = Field(..., example="FRAUD")
    risk_level: str = Field(..., example="CRITICAL")
    top_risk_indicators: list[RiskIndicator]
    amount: Optional[float] = Field(default=None, example=0.0)


class ExplainResponse(BaseModel):
    prediction: str
    risk_level: str
    fraud_probability_pct: str
    explanation: str
    regulatory_obligations: list[str]
    citations: list[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "Fraud Compliance RAG API",
        "version": "1.0.0",
        "endpoints": {
            "POST /ask": "Ask a fraud regulation question",
            "POST /explain": "Get regulatory explanation for a flagged transaction",
            "GET /health": "Health check",
            "GET /docs": "Interactive Swagger UI"
        }
    }


@app.get("/health")
def health():
    groq_key_set = bool(os.environ.get("GROQ_API_KEY"))
    return {
        "status": "healthy" if groq_key_set else "degraded",
        "groq_api_key_configured": groq_key_set,
        "model": "llama-3.3-70b-versatile",
        "documents_loaded": ["RBI KYC", "PCI-DSS", "FATF", "SEBI"],
        "message": (
            "Ready" if groq_key_set
            else "GROQ_API_KEY not set — set it before calling /ask or /explain"
        )
    }


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest):
    """
    Ask a question about fraud regulations.
    Returns an answer with citations from RBI, PCI-DSS, FATF, or SEBI documents.
    """
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured on the server."
        )
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = ask(request.question, k=request.k)
        return AskResponse(
            question=request.question,
            answer=result["answer"],
            citations=result["citations"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain", response_model=ExplainResponse)
def explain_endpoint(request: ExplainRequest):
    """
    Paste the output from the Fraud Detection API and get a regulatory explanation.
    Identifies which regulations are triggered and what compliance obligations apply.

    Connect directly to: https://fraud-api-ul6d.onrender.com/predict
    """
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured on the server."
        )

    try:
        result = explain(
            fraud_probability=request.fraud_probability,
            prediction=request.prediction,
            risk_level=request.risk_level,
            top_risk_indicators=[
                {"feature": r.feature, "value": r.value}
                for r in request.top_risk_indicators
            ],
            amount=request.amount
        )
        return ExplainResponse(
            prediction=request.prediction,
            risk_level=request.risk_level,
            fraud_probability_pct=f"{request.fraud_probability * 100:.1f}%",
            explanation=result["explanation"],
            regulatory_obligations=result["regulatory_obligations"],
            citations=result["citations"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))