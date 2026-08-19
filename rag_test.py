from app.tools.search.search_manager import search_manager
from app.tools.research_ingestion import ingest_search_results
from app.tools.vector_search import reset_database, search_documents
from app.agents.rag_researcher import research


query = "What are the latest developments in generative AI?"

print("\n" + "=" * 80)
print("RAG RESEARCH TEST")
print("=" * 80)

print("\nSearching and ingesting...\n")

reset_database()

results = search_manager(query, max_results=3)
ingest_search_results(results, max_pages=3)

documents = search_documents(query, k=5)

print(f"\nRetrieved {len(documents)} documents for research\n")

answer = research(query, documents)

print("\n" + "=" * 80)
print("RESEARCH OUTPUT")
print("=" * 80)
print(answer)
