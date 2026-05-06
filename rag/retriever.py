"""
retriever.py
Loads the ChromaDB vector store and retrieves the most relevant
regulation chunks for a given query. Used by chain.py and main.py.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_retriever(k: int = 3):
    """
    Returns a LangChain retriever that fetches the top-k most
    relevant regulation chunks from ChromaDB.
    k=3 is the sweet spot — enough context, not too noisy.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )
    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )


def retrieve_with_metadata(query: str, k: int = 3) -> list[dict]:
    """
    Retrieves top-k relevant chunks for a query.
    Returns a list of dicts with 'content', 'source', and 'section'.
    This is what chain.py uses to build cited answers.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )
    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )

    docs = vector_store.similarity_search(query, k=k)

    results = []
    for doc in docs:
        results.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "section": doc.metadata.get("section", "Unknown")
        })
    return results


if __name__ == "__main__":
    # Quick test — run this to verify retrieval is working
    test_queries = [
        "What makes a transaction suspicious under RBI guidelines?",
        "Why is V14 a fraud indicator?",
        "What is structuring in financial fraud?"
    ]

    print("=" * 55)
    print("Retriever Test")
    print("=" * 55)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        results = retrieve_with_metadata(query, k=2)
        for i, r in enumerate(results, 1):
            print(f"  Result {i}: {r['source']} — {r['section']}")
            print(f"  Preview: {r['content'][:120]}...")
        print()