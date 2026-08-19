from app.tools.vector_search import (
    reset_database,
    store_documents,
    search_documents,
    count_documents,
    debug_database,
)

from langchain_core.documents import Document


reset_database()

documents = [
    Document(
        page_content=(
            "Generative AI uses machine learning models "
            "to generate text, images, code and other content."
        ),
        metadata={
            "source": "https://example.com/ai",
            "title": "Generative AI",
            "query": "generative AI",
        },
    ),
    Document(
        page_content=(
            "Large language models are used for natural "
            "language understanding and generation."
        ),
        metadata={
            "source": "https://example.com/llm",
            "title": "Large Language Models",
            "query": "LLM",
        },
    ),
]


stored = store_documents(
    documents
)

print(
    f"\nStored: {stored}"
)

print(
    f"Database count: "
    f"{count_documents()}"
)

debug_database()


results = search_documents(
    "What is generative AI?",
    k=2
)

print(
    "\n========== FINAL RESULTS =========="
)

for i, doc in enumerate(
    results,
    start=1
):

    print(
        f"\nResult {i}"
    )

    print(
        "Title:",
        doc.metadata.get(
            "title",
            ""
        )
    )

    print(
        "Source:",
        doc.metadata.get(
            "source",
            ""
        )
    )

    print(
        "Content:",
        doc.page_content
    )