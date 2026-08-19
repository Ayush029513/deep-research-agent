import re
from html import unescape
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


# =====================================================
# Text Cleaning
# =====================================================

def clean_text(text):

    if not text:
        return ""

    text = unescape(str(text))

    # Remove HTML
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =====================================================
# URL Normalization
# =====================================================

def normalize_url(url):

    if not url:
        return ""

    try:

        parsed = urlparse(
            url.strip()
        )

        # Remove common tracking parameters
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
        }

        query_params = [
            (key, value)
            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True
            )
            if key.lower() not in tracking_params
        ]

        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",
                urlencode(query_params),
                "",
            )
        )

        return normalized

    except Exception:

        return url.strip().lower().rstrip("/")


# =====================================================
# Source Domain
# =====================================================

def get_domain(url):

    if not url:
        return ""

    try:

        return urlparse(
            url
        ).netloc.lower().replace(
            "www.",
            ""
        )

    except Exception:

        return ""


# =====================================================
# Deduplicate Results
# =====================================================

def deduplicate_results(results):

    seen_urls = set()

    unique = []

    for result in results:

        if not isinstance(
            result,
            dict
        ):
            continue

        url = result.get(
            "url",
            ""
        )

        if not url:
            continue

        normalized_url = normalize_url(
            url
        )

        if not normalized_url:
            continue

        if normalized_url in seen_urls:
            continue

        seen_urls.add(
            normalized_url
        )

        cleaned = result.copy()

        cleaned["url"] = url

        unique.append(
            cleaned
        )

    return unique


# =====================================================
# Query Tokenization
# =====================================================

def get_query_words(query):

    query = clean_text(
        query
    ).lower()

    words = re.findall(
        r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
        query
    )

    # Ignore extremely small words
    return [
        word
        for word in words
        if len(word) > 2
    ]


# =====================================================
# Source Quality
# =====================================================

def source_quality(result):

    source = clean_text(
        result.get(
            "source",
            ""
        )
    ).lower()

    url = result.get(
        "url",
        ""
    )

    domain = get_domain(
        url
    )

    score = 0

    # -----------------------------------------------
    # Search source
    # -----------------------------------------------

    source_scores = {

        "tavily": 5,

        "arxiv": 7,

        "github": 4,

        "google news": 3,

        "duckduckgo": 3,
    }

    score += source_scores.get(
        source,
        0
    )

    # -----------------------------------------------
    # High-value domains
    # -----------------------------------------------

    high_quality_domains = (

        ".gov",

        ".edu",

        ".ac.",

        "arxiv.org",

        "nature.com",

        "science.org",

        "ieee.org",

        "acm.org",

        "who.int",

        "nih.gov",

        "nasa.gov",
    )

    if any(
        domain.endswith(
            suffix
        )
        or suffix in domain
        for suffix in high_quality_domains
    ):

        score += 6

    # -----------------------------------------------
    # Known documentation / technical sources
    # -----------------------------------------------

    technical_domains = (

        "github.com",

        "python.org",

        "pytorch.org",

        "tensorflow.org",

        "huggingface.co",

        "scikit-learn.org",
    )

    if any(
        item in domain
        for item in technical_domains
    ):

        score += 4

    return score


# =====================================================
# Relevance Score
# =====================================================

def relevance_score(
    result,
    query
):

    title = clean_text(
        result.get(
            "title",
            ""
        )
    ).lower()

    content = clean_text(
        result.get(
            "content",
            ""
        )
    ).lower()

    query_words = get_query_words(
        query
    )

    if not query_words:
        return 0

    score = 0

    # -----------------------------------------------
    # Exact query match
    # -----------------------------------------------

    normalized_query = clean_text(
        query
    ).lower()

    if normalized_query in title:

        score += 25

    elif normalized_query in content:

        score += 10

    # -----------------------------------------------
    # Word-level relevance
    # -----------------------------------------------

    for word in query_words:

        # Title is much more important
        if word in title:

            score += 10

        # Content match
        if word in content:

            score += 3

    # -----------------------------------------------
    # Coverage
    # -----------------------------------------------

    matched_words = sum(
        1
        for word in query_words
        if word in title
        or word in content
    )

    coverage = (
        matched_words
        / len(query_words)
    )

    score += coverage * 20

    return score


# =====================================================
# Content Quality
# =====================================================

def content_quality(result):

    title = clean_text(
        result.get(
            "title",
            ""
        )
    )

    content = clean_text(
        result.get(
            "content",
            ""
        )
    )

    score = 0

    # Title exists
    if title:
        score += 3

    # Useful content
    content_length = len(
        content
    )

    if content_length >= 200:
        score += 5

    elif content_length >= 100:
        score += 3

    elif content_length >= 50:
        score += 1

    # Avoid extremely short results
    if content_length < 30:
        score -= 3

    return score


# =====================================================
# Search Result Score
# =====================================================

def score_result(
    result,
    query
):

    relevance = relevance_score(
        result,
        query
    )

    quality = source_quality(
        result
    )

    content = content_quality(
        result
    )

    total = (
        relevance
        + quality
        + content
    )

    return total


# =====================================================
# Rank Results
# =====================================================

def rank_results(
    results,
    query
):

    scored = []

    for result in results:

        score = score_result(
            result,
            query
        )

        scored.append(
            (
                score,
                result
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    ranked = []

    for score, result in scored:

        result = result.copy()

        result["_score"] = round(
            score,
            2
        )

        ranked.append(
            result
        )

    return ranked


# =====================================================
# Source Diversity
# =====================================================

def diversify_results(
    results,
    max_per_domain=3
):

    selected = []

    domain_counts = {}

    for result in results:

        domain = get_domain(
            result.get(
                "url",
                ""
            )
        )

        if not domain:

            continue

        count = domain_counts.get(
            domain,
            0
        )

        if count >= max_per_domain:

            continue

        selected.append(
            result
        )

        domain_counts[domain] = (
            count + 1
        )

    return selected


# =====================================================
# Final Search Fusion
# =====================================================

def search_fusion(
    results,
    query,
    top_k=15
):

    print(
        "\n========== SEARCH FUSION =========="
    )

    print(
        f"Raw results: "
        f"{len(results)}"
    )

    # -------------------------------------------------
    # Remove invalid / duplicate results
    # -------------------------------------------------

    unique = deduplicate_results(
        results
    )

    print(
        f"After URL deduplication: "
        f"{len(unique)}"
    )

    if not unique:

        return []

    # -------------------------------------------------
    # Rank
    # -------------------------------------------------

    ranked = rank_results(
        unique,
        query
    )

    # -------------------------------------------------
    # Diversify domains
    # -------------------------------------------------

    diversified = diversify_results(
        ranked,
        max_per_domain=3
    )

    # -------------------------------------------------
    # If diversification removed too many results,
    # keep the strongest available results.
    # -------------------------------------------------

    if len(diversified) < top_k:

        used_urls = {
            normalize_url(
                r.get(
                    "url",
                    ""
                )
            )
            for r in diversified
        }

        for result in ranked:

            url = normalize_url(
                result.get(
                    "url",
                    ""
                )
            )

            if url in used_urls:
                continue

            diversified.append(
                result
            )

            used_urls.add(
                url
            )

            if len(diversified) >= top_k:
                break

    # -------------------------------------------------
    # Final top K
    # -------------------------------------------------

    final_results = []

    for result in diversified[:top_k]:

        cleaned_result = result.copy()

        cleaned_result["title"] = clean_text(
            result.get(
                "title",
                ""
            )
        )

        cleaned_result["content"] = clean_text(
            result.get(
                "content",
                ""
            )
        )

        # Keep URL unchanged
        cleaned_result["url"] = result.get(
            "url",
            ""
        )

        # Keep source
        cleaned_result["source"] = result.get(
            "source",
            ""
        )

        final_results.append(
            cleaned_result
        )

    # -------------------------------------------------
    # Debug
    # -------------------------------------------------

    print(
        f"Final fused results: "
        f"{len(final_results)}"
    )

    print(
        "\nTop Results:"
    )

    for i, result in enumerate(
        final_results,
        start=1
    ):

        print(
            f"{i}. "
            f"{result.get('title', '')}"
        )

        print(
            f"   Source: "
            f"{result.get('source', '')}"
        )

        print(
            f"   Domain: "
            f"{get_domain(result.get('url', ''))}"
        )

        print(
            f"   Score: "
            f"{result.get('_score', 0)}"
        )

    return final_results