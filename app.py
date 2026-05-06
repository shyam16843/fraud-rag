"""
app.py
Fraud Compliance RAG — Gradio UI for HuggingFace Spaces
Two modes:
  1. Ask a fraud regulation question
  2. Explain a flagged transaction using fraud API output
"""

import os
import sys
import gradio as gr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.chain import ask, explain


# ── Mode 1 — Ask a regulation question ───────────────────────────────────────

def ask_question(question: str, k: int) -> tuple[str, str]:
    if not question.strip():
        return "Please enter a question.", ""
    if not os.environ.get("GROQ_API_KEY"):
        return "GROQ_API_KEY not configured.", ""
    try:
        result = ask(question.strip(), k=int(k))
        citations_text = "\n".join(
            f"{i+1}. {c}" for i, c in enumerate(result["citations"])
        )
        return result["answer"], citations_text
    except Exception as e:
        return f"Error: {str(e)}", ""


# ── Mode 2 — Explain a flagged transaction ────────────────────────────────────

def explain_transaction(
    fraud_probability, prediction, risk_level,
    f1_name, f1_val, f2_name, f2_val, f3_name, f3_val,
    amount
) -> tuple[str, str, str]:
    if not os.environ.get("GROQ_API_KEY"):
        return "GROQ_API_KEY not configured.", "", ""
    try:
        indicators = []
        for name, val in [(f1_name, f1_val), (f2_name, f2_val), (f3_name, f3_val)]:
            if name.strip():
                indicators.append({"feature": name.strip(), "value": float(val)})

        if not indicators:
            return "Please enter at least one risk indicator.", "", ""

        result = explain(
            fraud_probability=float(fraud_probability),
            prediction=prediction,
            risk_level=risk_level,
            top_risk_indicators=indicators,
            amount=float(amount)
        )

        obligations_text = "\n".join(f"• {o}" for o in result["regulatory_obligations"])
        seen = set()
        citations_text = ""
        for c in result["citations"]:
            if c not in seen:
                citations_text += f"• {c}\n"
                seen.add(c)

        return result["explanation"], obligations_text, citations_text.strip()

    except Exception as e:
        return f"Error: {str(e)}", "", ""


# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(
    title="Fraud Compliance RAG",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown("""
# 🏦 Fraud Compliance RAG
**Answers fraud regulation questions using RBI, PCI-DSS, FATF, and SEBI guidelines.**
Also explains why your fraud detection model flagged a transaction — with regulatory citations.

🔗 [Fraud Detection API](https://fraud-api-ul6d.onrender.com/docs) · 
👨‍💻 [GitHub](https://github.com/shyam16843/fraud-rag) ·
Built by **Ghanashyam T V**
""")

    with gr.Tabs():

        # ── Tab 1: Ask ────────────────────────────────────────────────────────
        with gr.TabItem("💬 Ask a Regulation Question"):
            gr.Markdown("""
Ask anything about fraud regulations. The system retrieves relevant excerpts
from RBI, PCI-DSS, FATF, and SEBI documents and generates a cited answer.
            """)

            with gr.Row():
                with gr.Column(scale=2):
                    question_input = gr.Textbox(
                        label="Your question",
                        placeholder="e.g. What is the regulatory definition of money laundering?",
                        lines=3
                    )
                    k_slider = gr.Slider(
                        minimum=1, maximum=5, value=3, step=1,
                        label="Number of regulation chunks to retrieve"
                    )
                    ask_btn = gr.Button("Get Answer", variant="primary")

                    gr.Examples(
                        examples=[
                            ["What makes a transaction suspicious under RBI guidelines?", 3],
                            ["What is structuring in financial fraud?", 3],
                            ["What are PCI-DSS fraud monitoring requirements?", 3],
                            ["What is the regulatory definition of money laundering?", 3],
                            ["What is a Suspicious Transaction Report (STR)?", 3],
                        ],
                        inputs=[question_input, k_slider],
                        label="Example questions — click to load"
                    )

            with gr.Row():
                with gr.Column(scale=2):
                    answer_output = gr.Textbox(
                        label="📋 Answer",
                        lines=12,
                        interactive=False
                    )
                with gr.Column(scale=1):
                    citations_output = gr.Textbox(
                        label="📚 Sources Cited",
                        lines=6,
                        interactive=False
                    )

            ask_btn.click(
                fn=ask_question,
                inputs=[question_input, k_slider],
                outputs=[answer_output, citations_output]
            )

        # ── Tab 2: Explain ────────────────────────────────────────────────────
        with gr.TabItem("🔍 Explain a Flagged Transaction"):
            gr.Markdown("""
Paste the output from your **[Fraud Detection API](https://fraud-api-ul6d.onrender.com/docs)**
and get a full regulatory explanation — which regulations are triggered, what obligations apply,
and what a compliance officer should do next.
            """)

            with gr.Row():
                with gr.Column():
                    gr.Markdown("**Transaction Result**")
                    fraud_prob = gr.Slider(
                        minimum=0.0, maximum=1.0, value=0.999, step=0.001,
                        label="Fraud Probability"
                    )
                    prediction = gr.Dropdown(
                        choices=["FRAUD", "LEGITIMATE"],
                        value="FRAUD",
                        label="Prediction"
                    )
                    risk_level = gr.Dropdown(
                        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                        value="CRITICAL",
                        label="Risk Level"
                    )
                    amount = gr.Number(value=0.0, label="Transaction Amount")

                with gr.Column():
                    gr.Markdown("**Top Risk Indicators** (from fraud API response)")
                    f1_name = gr.Textbox(value="V14", label="Feature 1 name")
                    f1_val = gr.Number(value=-4.2893, label="Feature 1 value")
                    f2_name = gr.Textbox(value="V12", label="Feature 2 name")
                    f2_val = gr.Number(value=-2.8999, label="Feature 2 value")
                    f3_name = gr.Textbox(value="V10", label="Feature 3 name")
                    f3_val = gr.Number(value=-2.7723, label="Feature 3 value")

            explain_btn = gr.Button("Generate Regulatory Explanation", variant="primary")

            with gr.Row():
                explanation_output = gr.Textbox(
                    label="📋 Regulatory Explanation",
                    lines=14,
                    interactive=False
                )

            with gr.Row():
                with gr.Column():
                    obligations_output = gr.Textbox(
                        label="⚖️ Regulatory Obligations",
                        lines=6,
                        interactive=False
                    )
                with gr.Column():
                    explain_citations_output = gr.Textbox(
                        label="📚 Sources Cited",
                        lines=6,
                        interactive=False
                    )

            explain_btn.click(
                fn=explain_transaction,
                inputs=[
                    fraud_prob, prediction, risk_level,
                    f1_name, f1_val, f2_name, f2_val, f3_name, f3_val,
                    amount
                ],
                outputs=[explanation_output, obligations_output, explain_citations_output]
            )

    gr.Markdown("""
---
*Regulation sources: RBI Master Directions on KYC · PCI-DSS · FATF Fraud Typologies · SEBI Regulations*
""")


if __name__ == "__main__":
    demo.launch()