from app.tools.search.github_search import github_search

results = github_search("LangGraph")

for r in results:
    print("=" * 80)
    print(r["title"])
    print(r["url"])
    print(r["content"])