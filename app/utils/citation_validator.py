import re
from urllib.parse import urlparse


# =====================================================
# Extract Citation IDs
# =====================================================

def extract_citations(text: str):
    """
    Extract citations such as [S1], [S2], [S10].
    """

    if not text:
        return []

    citations = re.findall(
        r"\[S(\d+)\]",
        text
    )

    return sorted(
        set(int(c) for c in citations)
    )


# =====================================================
# Validate URL
# =====================================================

def valid_url(url: str):

    if not url:
        return False

    try:

        parsed = urlparse(url)

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:

        return False


# =====================================================
# Citation Validation
# =====================================================

def validate_citations(report: str, documents: list):

    print("\n========== CITATION VALIDATION ==========")

    citations = extract_citations(report)

    print(
        f"Citations found in report: "
        f"{len(citations)}"
    )

    # -------------------------------------------------
    # Build source mapping
    # -------------------------------------------------

    source_map = {}

    for i, doc in enumerate(documents or [], start=1):

        metadata = doc.metadata or {}

        source = metadata.get(
            "source",
            ""
        ).strip()

        title = metadata.get(
            "title",
            ""
        ).strip()

        if not valid_url(source):
            continue

        source_map[i] = {
            "title": title,
            "url": source,
        }

    # -------------------------------------------------
    # Validate citations
    # -------------------------------------------------

    valid = []
    invalid = []

    for citation in citations:

        if citation in source_map:

            valid.append(citation)

        else:

            invalid.append(citation)

    # -------------------------------------------------
    # Build result
    # -------------------------------------------------

    total = len(citations)

    valid_count = len(valid)
    invalid_count = len(invalid)

    if total == 0:

        score = 0

    else:

        score = round(
            (valid_count / total) * 100
        )

    result = {
        "citations_found": citations,
        "valid_citations": valid,
        "invalid_citations": invalid,
        "citation_score": score,
        "source_map": source_map,
    }

    # -------------------------------------------------
    # Debug
    # -------------------------------------------------

    print(
        f"Valid citations: "
        f"{valid_count}"
    )

    print(
        f"Invalid citations: "
        f"{invalid_count}"
    )

    print(
        f"Citation score: "
        f"{score}/100"
    )

    if invalid:

        print(
            f"Invalid citation IDs: "
            f"{invalid}"
        )

    return result