import arxiv


def arxiv_search(query, max_results=5):

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    client = arxiv.Client()

    results = []

    for result in client.results(search):

        results.append(
            {
                "title": result.title,
                "url": result.entry_id,
                "content": result.summary,
                "source": "arXiv",
            }
        )

    return results