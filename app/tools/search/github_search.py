import os
import requests


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def github_search(query, max_results=5):
    headers = {
        "Accept": "application/vnd.github+json",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    url = (
        "https://api.github.com/search/repositories"
        f"?q={query}&sort=stars&order=desc&per_page={max_results}"
    )

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    results = []

    for repo in data.get("items", []):
        results.append(
            {
                "title": repo["full_name"],
                "url": repo["html_url"],
                "content": repo.get("description") or "",
                "source": "GitHub",
            }
        )

    return results