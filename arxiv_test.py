from app.tools.search.arxiv_search import arxiv_search


results = arxiv_search(
    "generative artificial intelligence",
    max_results=5
)


for i, result in enumerate(results, 1):

    print("=" * 80)
    print(f"RESULT {i}")
    print("=" * 80)

    print("Title:", result["title"])
    print("URL:", result["url"])
    print("Source:", result["source"])
    print("Content:", result["content"][:500])

    print()