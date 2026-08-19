from app.tools.search.search_manager import search_manager
from app.tools.research_ingestion import ingest_search_results


query = "latest developments in generative AI"

print("\nSEARCHING...\n")

results = search_manager(
    query,
    max_results=3
)

print(f"Found {len(results)} search results")


print("\nINGESTING...\n")

documents = ingest_search_results(
    results,
    max_pages=3
)


print("\n" + "=" * 80)
print("INGESTION COMPLETE")
print("=" * 80)

print("Documents stored:", len(documents))