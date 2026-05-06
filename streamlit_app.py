"""
streamlit_app.py
Fraud Compliance RAG — Streamlit UI
Two modes:
  1. Ask a regulation question
  2. Paste fraud API output and get regulatory explanation
"""

import os
import sys
import streamlit as st

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.chain import ask, explain

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fraud Compliance RAG",
    page_icon="🏦",
    layout="wide"
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏦 Fraud Compliance RAG")
st.markdown(
    "**Answers fraud regulation questions using RBI, PCI-DSS, FATF, and SEBI guidelines.**  \n"
    "Also explains why your fraud detection model flagged a transaction — with regulatory citations."
)
st.divider()

# ── API Key check ─────────────────────────────────────────────────────────────
groq_key = os.environ.get("GROQ_API_KEY", "")
if not groq_key:
    st.warning(
        "⚠️ GROQ_API_KEY not set. "
        "Set it before running: `$env:GROQ_API_KEY='your_key'`",
        icon="⚠️"
    )

# ── Mode selector ─────────────────────────────────────────────────────────────
mode = st.radio(
    "Choose mode:",
    ["💬 Ask a Regulation Question", "🔍 Explain a Flagged Transaction"],
    horizontal=True
)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 — Ask a regulation question
# ══════════════════════════════════════════════════════════════════════════════
if mode == "💬 Ask a Regulation Question":

    st.subheader("Ask a Fraud Regulation Question")
    st.markdown(
        "Ask anything about fraud regulations. "
        "The system retrieves relevant excerpts from RBI, PCI-DSS, FATF, and SEBI documents "
        "and generates a cited answer."
    )

    # Example questions
    st.markdown("**Example questions:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What makes a transaction suspicious under RBI?"):
            st.session_state["question"] = "What makes a transaction suspicious under RBI guidelines?"
    with col2:
        if st.button("What is structuring in financial fraud?"):
            st.session_state["question"] = "What is structuring in financial fraud?"
    with col3:
        if st.button("What are PCI-DSS fraud monitoring requirements?"):
            st.session_state["question"] = "What are PCI-DSS fraud monitoring requirements?"

    question = st.text_area(
        "Your question:",
        value=st.session_state.get("question", ""),
        height=100,
        placeholder="e.g. What is the regulatory definition of money laundering?"
    )

    k = st.slider("Number of regulation chunks to retrieve", min_value=1, max_value=5, value=3)

    if st.button("Get Answer", type="primary", disabled=not groq_key):
        if not question.strip():
            st.error("Please enter a question.")
        else:
            with st.spinner("Searching regulations and generating answer..."):
                try:
                    result = ask(question.strip(), k=k)

                    st.success("Answer generated")

                    st.markdown("### 📋 Answer")
                    st.markdown(result["answer"])

                    st.markdown("### 📚 Sources Cited")
                    for i, citation in enumerate(result["citations"], 1):
                        st.markdown(f"**{i}.** {citation}")

                    with st.expander("View retrieved regulation chunks"):
                        for i, chunk in enumerate(result["retrieved_chunks"], 1):
                            st.markdown(
                                f"**Chunk {i} — {chunk['source']} / {chunk['section']}**"
                            )
                            st.text(chunk["content"])
                            st.divider()

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 — Explain a flagged transaction
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.subheader("🔍 Explain a Flagged Transaction")
    st.markdown(
        "Paste the output from your **Fraud Detection API** and get a full regulatory explanation — "
        "which regulations are triggered, what obligations apply, and what a compliance officer should do next."
    )

    st.info(
        "💡 Get a fraud prediction first from the "
        "[Fraud Detection API](https://fraud-api-ul6d.onrender.com/docs), "
        "then paste the result here.",
        icon="💡"
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Transaction Result**")
        fraud_probability = st.number_input(
            "Fraud Probability (0.0 – 1.0)",
            min_value=0.0, max_value=1.0,
            value=0.999, step=0.001, format="%.3f"
        )
        prediction = st.selectbox("Prediction", ["FRAUD", "LEGITIMATE"])
        risk_level = st.selectbox("Risk Level", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        amount = st.number_input("Transaction Amount", min_value=0.0, value=0.0, step=0.01)

    with col_right:
        st.markdown("**Top Risk Indicators** (from fraud API response)")
        st.markdown("Enter the top features flagged by the model:")

        f1_name = st.text_input("Feature 1 name", value="V14")
        f1_val = st.number_input("Feature 1 value", value=-4.2893, format="%.4f")

        f2_name = st.text_input("Feature 2 name", value="V12")
        f2_val = st.number_input("Feature 2 value", value=-2.8999, format="%.4f")

        f3_name = st.text_input("Feature 3 name", value="V10")
        f3_val = st.number_input("Feature 3 value", value=-2.7723, format="%.4f")

    # Load example button
    if st.button("Load example from fraud API"):
        st.session_state["load_example"] = True
        st.rerun()

    if st.button("Generate Regulatory Explanation", type="primary", disabled=not groq_key):
        indicators = [
            {"feature": f1_name, "value": f1_val},
            {"feature": f2_name, "value": f2_val},
            {"feature": f3_name, "value": f3_val},
        ]
        indicators = [i for i in indicators if i["feature"].strip()]

        if not indicators:
            st.error("Please enter at least one risk indicator.")
        else:
            with st.spinner("Retrieving regulations and generating compliance report..."):
                try:
                    result = explain(
                        fraud_probability=fraud_probability,
                        prediction=prediction,
                        risk_level=risk_level,
                        top_risk_indicators=indicators,
                        amount=amount
                    )

                    # Risk level badge
                    badge_color = {
                        "CRITICAL": "🔴", "HIGH": "🟠",
                        "MEDIUM": "🟡", "LOW": "🟢"
                    }.get(risk_level, "⚪")

                    st.markdown(
                        f"### {badge_color} {prediction} — "
                        f"{fraud_probability * 100:.1f}% fraud probability"
                    )
                    st.divider()

                    st.markdown("### 📋 Regulatory Explanation")
                    st.markdown(result["explanation"])

                    st.divider()

                    col_obl, col_cit = st.columns(2)

                    with col_obl:
                        st.markdown("### ⚖️ Regulatory Obligations")
                        for obligation in result["regulatory_obligations"]:
                            st.markdown(f"- {obligation}")

                    with col_cit:
                        st.markdown("### 📚 Sources Cited")
                        seen = set()
                        for citation in result["citations"]:
                            if citation not in seen:
                                st.markdown(f"- {citation}")
                                seen.add(citation)

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center; color:gray; font-size:13px;'>"
    "Built by <b>Ghanashyam T V</b> · "
    "<a href='https://github.com/shyam16843'>GitHub</a> · "
    "<a href='https://fraud-api-ul6d.onrender.com/docs'>Fraud Detection API</a>"
    "</div>",
    unsafe_allow_html=True
)