import feedparser
from urllib.parse import quote


def news_search(query, max_results=5):
    url = (
        f"https://news.google.com/rss/search?"
        f"q={quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    feed = feedparser.parse(url)

    results = []

    for entry in feed.entries[:max_results]:
        results.append(
            {
                "title": entry.title,
                "url": entry.link,
                "content": entry.get("summary", ""),
                "source": "Google News",
            }
        )

    return results