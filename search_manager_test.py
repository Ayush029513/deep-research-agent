from app.tools.search.search_manager import search_manager


results = search_manager(
    "latest developments in generative AI",
    max_results=3
)


for i, result in enumerate(results, 1):

    print("\n" + "=" * 80)
    print(f"RESULT {i}")
    print("=" * 80)

    print("Title:", result.get("title"))
    print("Source:", result.get("source"))
    print("URL:", result.get("url"))
    print("Content:", result.get("content", "")[:300])