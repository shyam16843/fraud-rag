"""
chain.py
Combines retrieval + Groq LLaMA 3 to generate cited answers.
Two functions:
  - ask()     : general regulation question
  - explain() : paste fraud API output, get regulatory explanation
"""

import os
from groq import Groq
from rag.retriever import retrieve_with_metadata

# Initialise Groq client — reads GROQ_API_KEY from environment
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def _format_context(chunks: list[dict]) -> str:
    """Formats retrieved chunks into a readable context block for the LLM."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(
            f"[Source {i}] {chunk['source']} — {chunk['section']}\n"
            f"{chunk['content']}\n"
        )
    return "\n".join(lines)


def _format_citations(chunks: list[dict]) -> list[str]:
    """Returns a clean list of citation strings for the API response."""
    return [
        f"{chunk['source']} — {chunk['section']}"
        for chunk in chunks
    ]


def ask(question: str, k: int = 3) -> dict:
    """
    Answers a general fraud regulation question using RAG.

    Args:
        question: The user's question about fraud regulations.
        k: Number of regulation chunks to retrieve.

    Returns:
        dict with 'answer', 'citations', and 'retrieved_chunks'.
    """
    chunks = retrieve_with_metadata(question, k=k)
    context = _format_context(chunks)

    prompt = f"""You are a fraud compliance expert with deep knowledge of 
Indian banking regulations (RBI), international payment standards (PCI-DSS), 
and financial crime guidelines (FATF, SEBI).

Answer the question using ONLY the regulation excerpts provided below.
Always cite your sources by referring to the source name and section.
Be specific and practical. If the context doesn't contain enough information,
say so clearly rather than guessing.

REGULATION EXCERPTS:
{context}

QUESTION: {question}

ANSWER (cite sources explicitly):"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600
    )

    answer = response.choices[0].message.content.strip()
    citations = _format_citations(chunks)

    return {
        "answer": answer,
        "citations": citations,
        "retrieved_chunks": chunks
    }


def explain(
    fraud_probability: float,
    prediction: str,
    risk_level: str,
    top_risk_indicators: list[dict],
    amount: float = None
) -> dict:
    """
    Takes output from the fraud detection API and returns a regulatory
    explanation of why those features triggered a fraud flag.

    Args:
        fraud_probability: e.g. 0.999
        prediction: "FRAUD" or "LEGITIMATE"
        risk_level: "CRITICAL", "HIGH", "MEDIUM", "LOW"
        top_risk_indicators: list of {"feature": "V14", "value": -4.28}
        amount: transaction amount (optional)

    Returns:
        dict with 'explanation', 'citations', 'regulatory_obligations'.
    """
    # Format the fraud API output for the LLM
    indicators_text = "\n".join([
        f"  - {r['feature']}: {r['value']}"
        for r in top_risk_indicators
    ])

    amount_text = f"Transaction Amount: {amount}" if amount is not None else ""

    # Build a targeted query from the flagged features
    feature_names = [r["feature"] for r in top_risk_indicators]
    query = (
        f"fraud indicators {' '.join(feature_names)} suspicious transaction "
        f"regulatory explanation high risk"
    )
    chunks = retrieve_with_metadata(query, k=4)
    context = _format_context(chunks)

    prompt = f"""You are a fraud compliance officer explaining why an automated 
fraud detection system flagged a transaction. Your explanation must reference 
specific regulations so the decision can be audited.

FRAUD DETECTION RESULT:
  Prediction: {prediction}
  Risk Level: {risk_level}
  Fraud Probability: {fraud_probability * 100:.1f}%
  {amount_text}
  Top Risk Indicators (statistical anomalies from normal behaviour):
{indicators_text}

RELEVANT REGULATION EXCERPTS:
{context}

TASK: Explain in plain language:
1. What these risk indicators suggest about the transaction behaviour
2. Which specific regulations are triggered by this pattern
3. What compliance obligations the institution now has (e.g. STR filing)
4. What the next steps should be for a compliance officer

Be specific. Cite the regulation source and section for each obligation.
Keep the explanation practical and audit-ready."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800
    )

    explanation = response.choices[0].message.content.strip()
    citations = _format_citations(chunks)

    # Extract regulatory obligations as a separate field
    obligations_prompt = f"""Based on this fraud detection result:
Prediction: {prediction}, Risk Level: {risk_level}

List ONLY the specific regulatory obligations that apply, 
one per line, in the format: "[Regulation] — [Obligation]"
Maximum 4 obligations. Be concise."""

    obligations_response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": obligations_prompt}],
        temperature=0.1,
        max_tokens=200
    )

    obligations_text = obligations_response.choices[0].message.content.strip()
    obligations = [
        line.strip()
        for line in obligations_text.split("\n")
        if line.strip()
    ]

    return {
        "explanation": explanation,
        "citations": citations,
        "regulatory_obligations": obligations
    }


if __name__ == "__main__":
    import sys

    # Check for API key
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable not set.")
        print("Run: $env:GROQ_API_KEY='your_key_here'")
        sys.exit(1)

    print("=" * 55)
    print("Chain Test — ask()")
    print("=" * 55)

    result = ask("What makes a transaction suspicious under RBI guidelines?")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nCitations:")
    for c in result["citations"]:
        print(f"  - {c}")

    print("\n" + "=" * 55)
    print("Chain Test — explain()")
    print("=" * 55)

    # Simulate a fraud API response
    result2 = explain(
        fraud_probability=0.999,
        prediction="FRAUD",
        risk_level="CRITICAL",
        top_risk_indicators=[
            {"feature": "V14", "value": -4.2893},
            {"feature": "V12", "value": -2.8999},
            {"feature": "V10", "value": -2.7723}
        ],
        amount=0.0
    )
    print(f"\nExplanation:\n{result2['explanation']}")
    print(f"\nRegulatory Obligations:")
    for o in result2["regulatory_obligations"]:
        print(f"  - {o}")
    print(f"\nCitations:")
    for c in result2["citations"]:
        print(f"  - {c}")