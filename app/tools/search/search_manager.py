from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from app.tools.search.tavily_search import tavily_search
from app.tools.search.duckduckgo_search import duckduckgo_search
from app.tools.search.github_search import github_search
from app.tools.search.news_search import news_search
from app.tools.search.arxiv_search import arxiv_search

from app.tools.search.search_fusion import search_fusion


# =====================================================
# Trusted / Higher Quality Domains
# =====================================================

TRUSTED_DOMAINS = (
    "arxiv.org",
    "github.com",
    "mit.edu",
    "stanford.edu",
    "berkeley.edu",
    "openai.com",
    "anthropic.com",
    "google.com",
    "deepmind.google",
    "microsoft.com",
    "nature.com",
    "science.org",
    "ieee.org",
    "acm.org",
)


# =====================================================
# URL Validation
# =====================================================

def valid_url(url):

    if not url:
        return False

    return url.startswith(("http://", "https://"))


# =====================================================
# Domain Extraction
# =====================================================

def get_domain(url):

    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


# =====================================================
# Result Cleaning
# =====================================================

def clean_results(results):

    cleaned = []
    seen_urls = set()

    for result in results:

        if not isinstance(result, dict):
            continue

        url = result.get("url", "")
        title = result.get("title", "")
        content = result.get("content", "")

        # Invalid URL
        if not valid_url(url):
            continue

        # Duplicate URL
        normalized_url = url.rstrip("/")

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)

        # Ignore almost empty results
        if not title and not content:
            continue

        # Add domain metadata
        result["domain"] = get_domain(url)

        # Add trust metadata
        result["trusted"] = any(
            domain in result["domain"]
            for domain in TRUSTED_DOMAINS
        )

        cleaned.append(result)

    return cleaned


# =====================================================
# Search Manager
# =====================================================

def search_manager(query, max_results=5):

    search_functions = [
        ("Tavily", tavily_search),
        ("DuckDuckGo", duckduckgo_search),
        ("GitHub", github_search),
        ("Google News", news_search),
        ("arXiv", arxiv_search),
    ]

    all_results = []

    print("\n" + "=" * 70)
    print("STARTING PARALLEL SEARCH")
    print("=" * 70)

    # -------------------------------------------------
    # Parallel Search
    # -------------------------------------------------

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = {
            executor.submit(
                search_function,
                query,
                max_results
            ): name
            for name, search_function in search_functions
        }

        for future in as_completed(futures):

            source = futures[future]

            try:

                results = future.result()

                if not results:
                    results = []

                print(
                    f"[OK] {source}: "
                    f"{len(results)} results"
                )

                # Ensure source exists
                for result in results:

                    if isinstance(result, dict):
                        result.setdefault(
                            "source",
                            source
                        )

                all_results.extend(results)

            except Exception as e:

                print(
                    f"[FAIL] {source} failed: {e}"
                )

    # -------------------------------------------------
    # Raw Results
    # -------------------------------------------------

    print("\n" + "=" * 70)
    print(
        f"TOTAL RAW RESULTS: "
        f"{len(all_results)}"
    )
    print("=" * 70)

    # -------------------------------------------------
    # Clean Results
    # -------------------------------------------------

    cleaned_results = clean_results(
        all_results
    )

    print(
        f"CLEAN RESULTS: "
        f"{len(cleaned_results)}"
    )

    # -------------------------------------------------
    # Search Fusion
    # -------------------------------------------------

    final_results = search_fusion(
        cleaned_results,
        query,
        top_k=15
    )

    # -------------------------------------------------
    # Prioritize Trusted Sources
    # -------------------------------------------------

    trusted_results = [
        result
        for result in final_results
        if result.get("trusted")
    ]

    other_results = [
        result
        for result in final_results
        if not result.get("trusted")
    ]

    final_results = (
        trusted_results +
        other_results
    )

    # -------------------------------------------------
    # Final Debug Output
    # -------------------------------------------------

    print("\n" + "=" * 70)
    print(
        f"FINAL RESULTS AFTER FUSION: "
        f"{len(final_results)}"
    )
    print("=" * 70)

    for i, result in enumerate(
        final_results,
        start=1
    ):

        trust = (
            "TRUSTED"
            if result.get("trusted")
            else "NORMAL"
        )

        print(
            f"{i}. [{trust}] "
            f"{result.get('title', '')[:70]}"
        )

    return final_results