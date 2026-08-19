from ddgs import DDGS


def duckduckgo_search(query, max_results=5):

    results = []

    try:

        with DDGS() as ddgs:

            search_results = ddgs.text(
                query,
                max_results=max_results
            )

            for result in search_results:

                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "content": result.get("body", ""),
                        "source": "DuckDuckGo",
                    }
                )

    except Exception as e:

        print(f"DuckDuckGo search failed: {e}")

    return results