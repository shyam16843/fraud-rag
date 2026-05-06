"""
ingest.py
Loads fraud regulation documents, chunks them, embeds with HuggingFace,
and stores in ChromaDB. Run this once before starting the API or UI.
"""

import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── Document definitions ───────────────────────────────────────────────────────
# Regulation text embedded directly — no PDF downloads needed.
# Each document has: source name, section reference, and content.

DOCUMENTS = [
    {
        "source": "RBI Master Directions on KYC",
        "section": "Section 8 — Customer Due Diligence",
        "content": """
        The Reserve Bank of India requires all regulated entities to conduct Customer Due Diligence (CDD)
        before establishing a business relationship or carrying out any transaction.
        CDD includes identifying and verifying the identity of customers using reliable, independent source documents.
        Enhanced Due Diligence (EDD) must be applied to high-risk customers, including Politically Exposed Persons (PEPs),
        non-resident customers, and customers from high-risk jurisdictions.
        Regulated entities must monitor transactions on an ongoing basis to ensure they are consistent
        with the institution's knowledge of the customer, their business and risk profile.
        Suspicious transactions must be reported to the Financial Intelligence Unit India (FIU-IND)
        within seven working days of forming a suspicion.
        """
    },
    {
        "source": "RBI Master Directions on KYC",
        "section": "Section 12 — Suspicious Transaction Reporting",
        "content": """
        A suspicious transaction is one that gives rise to a reasonable ground of suspicion that it
        may involve the proceeds of crime or terrorism financing.
        Indicators of suspicious transactions include:
        - Transactions that are unusually large or complex without apparent economic purpose.
        - Transactions that do not match the customer's known business or financial profile.
        - Multiple transactions just below the reporting threshold, indicating structuring.
        - Rapid movement of funds through accounts with no clear business rationale.
        - Transactions involving high-risk countries or jurisdictions.
        - Large cash transactions that are inconsistent with the customer's normal activity.
        - Unusual patterns in transaction timing — multiple transactions in short succession.
        Regulated entities must not tip off the customer that a suspicious transaction report has been filed.
        """
    },
    {
        "source": "RBI Master Directions on KYC",
        "section": "Section 15 — High Risk Indicators",
        "content": """
        The following customer and transaction characteristics are classified as high risk under RBI guidelines:
        - Customers who provide insufficient or suspicious identification documents.
        - Accounts showing sudden unexplained increase in transaction volume or value.
        - Transactions where the customer appears nervous or in a hurry.
        - Cash transactions above INR 10 lakhs in a single day.
        - Wire transfers to or from high-risk jurisdictions without clear business purpose.
        - Transactions inconsistent with the declared source of funds.
        - Dormant accounts that suddenly become active with large transactions.
        - Customers reluctant to provide information required for KYC compliance.
        High-risk customers must be reviewed at least once every twelve months.
        """
    },
    {
        "source": "PCI-DSS Payment Security Standards",
        "section": "Requirement 10 — Transaction Monitoring",
        "content": """
        PCI-DSS Requirement 10 mandates that all access to system components and cardholder data
        must be tracked and monitored. Organisations must implement automated audit trails for all
        individual access to cardholder data.
        Suspicious transaction indicators under PCI-DSS include:
        - Transactions originating from unusual geographic locations inconsistent with the cardholder's history.
        - Multiple failed authentication attempts followed by a successful transaction.
        - High-value transactions at unusual hours, particularly between midnight and 5am.
        - Rapid successive transactions from the same card in different locations.
        - Card-not-present transactions with billing and shipping address mismatches.
        - Transactions significantly above the customer's average transaction amount.
        - Multiple transactions to the same merchant in a very short time window.
        Organisations must retain audit log history for at least twelve months.
        """
    },
    {
        "source": "PCI-DSS Payment Security Standards",
        "section": "Requirement 12 — Fraud Risk Management",
        "content": """
        Fraud risk management under PCI-DSS requires organisations to maintain a formal risk assessment process.
        Key fraud patterns identified in payment card environments include:
        - Card skimming: capturing card data at point of sale terminals.
        - Card-not-present fraud: using stolen card details for online transactions.
        - Account takeover: gaining unauthorised access to customer accounts.
        - Friendly fraud: customers falsely claiming transactions are unauthorised.
        - Velocity attacks: rapid sequential transactions to test card validity.
        Transaction amount anomalies are a primary fraud indicator. Transactions deviating
        significantly from a customer's historical average — particularly very small test amounts
        followed by large transactions — indicate card testing fraud patterns.
        The Amount feature in transaction data is one of the strongest predictors of fraudulent activity
        when combined with temporal and behavioural anomalies.
        """
    },
    {
        "source": "FATF Fraud Typologies",
        "section": "Chapter 3 — Payment Fraud Indicators",
        "content": """
        The Financial Action Task Force (FATF) identifies the following typologies for payment fraud:
        Money Mule Networks: Criminals recruit individuals to receive and transfer fraudulent funds,
        making tracing difficult. Transactions show unusual patterns of receiving and immediately
        forwarding funds to third parties.
        Structuring: Breaking large transactions into smaller amounts to avoid detection thresholds.
        Characteristic signature is multiple transactions just below reporting limits in a single day.
        Layering: Moving funds through multiple accounts or jurisdictions to obscure the origin.
        Transactions appear legitimate individually but form a suspicious pattern collectively.
        Integration: Introducing laundered funds back into the legitimate economy through
        real estate, luxury goods, or business investments.
        Principal components in credit card transaction data that show extreme negative values —
        particularly V14, V12, and V10 — are statistically associated with fraudulent transaction
        patterns identified in empirical fraud research. These components capture temporal,
        geographic, and behavioural anomalies that deviate from normal spending patterns.
        """
    },
    {
        "source": "FATF Fraud Typologies",
        "section": "Chapter 5 — Digital Payment Fraud",
        "content": """
        Digital payment fraud has grown significantly with the expansion of online commerce.
        FATF identifies the following high-risk indicators specific to digital payments:
        - Transactions initiated from IP addresses associated with known fraud networks.
        - Device fingerprint mismatches between registration and transaction time.
        - Unusual transaction velocity: more than three transactions per minute from one account.
        - Transactions involving newly created accounts with immediate high-value activity.
        - Geographic impossibility: transactions from two distant locations within minutes.
        - Zero or near-zero transaction amounts often indicate card validity testing before
          a larger fraudulent transaction is attempted. This is a critical early warning indicator.
        - Transactions at round amounts (e.g., exactly 100.00, 500.00) may indicate automated fraud.
        Financial institutions must implement real-time monitoring systems capable of identifying
        these patterns as they occur, not after the fact.
        """
    },
    {
        "source": "SEBI Insider Trading and Market Fraud Regulations",
        "section": "Regulation 6 — Suspicious Trading Patterns",
        "content": """
        SEBI regulations require market intermediaries to monitor and report suspicious trading patterns.
        Suspicious trading activity includes:
        - Trades executed immediately before significant price movements, indicating possible insider knowledge.
        - Circular trading: buy and sell orders between related parties to create artificial volume.
        - Pump and dump schemes: artificially inflating asset prices before selling.
        - Front running: executing orders on behalf of clients ahead of large client orders.
        - Layering: placing and cancelling large orders to create false impressions of market activity.
        Transaction monitoring systems must flag accounts where trading patterns deviate significantly
        from historical norms. Statistical anomalies in trading behaviour — equivalent to the
        principal component deviations seen in credit card fraud — are primary indicators of
        market manipulation. Extreme deviations in behavioural features, particularly those
        capturing timing and size relationships, are the strongest predictors of fraudulent activity.
        """
    },
]


def build_vector_store(persist_dir: str = "./chroma_db") -> Chroma:
    """
    Chunks all regulation documents, embeds them, and stores in ChromaDB.
    Returns the vector store object.
    """

    print("Step 1/4: Preparing documents...")
    texts = []
    metadatas = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "]
    )

    for doc in DOCUMENTS:
        chunks = splitter.split_text(doc["content"].strip())
        for chunk in chunks:
            texts.append(chunk)
            metadatas.append({
                "source": doc["source"],
                "section": doc["section"]
            })

    print(f"  Created {len(texts)} chunks from {len(DOCUMENTS)} documents.")

    print("Step 2/4: Loading embedding model (first run downloads ~90MB)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    print("  Embedding model loaded.")

    print("Step 3/4: Building ChromaDB vector store...")
    vector_store = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=persist_dir
    )
    print(f"  Vector store saved to: {persist_dir}")

    print("Step 4/4: Verifying store...")
    count = vector_store._collection.count()
    print(f"  {count} chunks stored and ready for retrieval.")

    return vector_store


def load_vector_store(persist_dir: str = "./chroma_db") -> Chroma:
    """
    Loads an existing ChromaDB vector store from disk.
    Call this in retriever.py and main.py instead of rebuilding every time.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )


if __name__ == "__main__":
    print("=" * 55)
    print("Fraud Compliance RAG — Document Ingestion")
    print("=" * 55)
    build_vector_store()
    print("=" * 55)
    print("Ingestion complete. You can now run the API or UI.")
    print("=" * 55)