from app.tools.vector_search import search_documents


query = "What are the latest developments in generative AI?"

print("\n" + "=" * 80)
print("RAG RETRIEVAL TEST")
print("=" * 80)

results = search_documents(query, k=5)

print(f"\nRetrieved {len(results)} documents\n")

for i, doc in enumerate(results, 1):

    print("=" * 80)
    print(f"DOCUMENT {i}")
    print("=" * 80)

    print("Metadata:")
    print(doc.metadata)

    print("\nContent:")
    print(doc.page_content[:1000])

    print()