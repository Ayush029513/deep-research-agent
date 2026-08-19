from tavily import TavilyClient
from app.config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)


def tavily_search(query, max_results=5):
    results = client.search(
        query=query,
        max_results=max_results,
    )

    return results["results"]