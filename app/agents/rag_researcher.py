from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


# =====================================================
# Research Prompt
# =====================================================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are the Research Analyst in a Deep Research Agent.

Your task is to analyze ONLY the retrieved source documents
and produce evidence-grounded research findings.

You MUST follow these rules.

====================================================
EVIDENCE RULES
====================================================

1. Use ONLY the provided retrieved documents.

2. Do NOT use outside knowledge.

3. Do NOT invent facts, statistics, dates, names,
   organizations, URLs, or research findings.

4. Every important factual claim MUST have at least
   one source citation.

5. Use the source identifiers exactly as provided:
   [S1], [S2], [S3], etc.

6. Never create a source identifier that does not exist.

7. Never cite [S1] for information that only appears
   in [S2].

8. If multiple sources support the same claim,
   cite all relevant sources.

Example:
[S1][S3]

9. If a claim cannot be supported by the retrieved
   documents, explicitly mark it as:

   INSUFFICIENT EVIDENCE

10. Do not treat search-result snippets as strong evidence
    when the actual source content is unavailable.

11. Clearly distinguish:
    - Direct evidence
    - Comparison
    - Interpretation
    - Research gap

12. Do not exaggerate conclusions.

13. Preserve source URLs exactly.

14. Do not create fake URLs.

====================================================
SOURCE MAPPING
====================================================

Each source is provided in this format:

[S1]
Title: ...
URL: ...
Content: ...

Use the exact source ID when citing evidence.

====================================================
OUTPUT FORMAT
====================================================

Return ONLY the following Markdown structure:

# Research Findings

## Overview

Briefly explain what the retrieved evidence says about
the research topic.

## Key Findings

For every important finding use:

### Finding 1

**Claim:** ...

**Evidence:** ...

**Sources:** [S1]

**Evidence Strength:** Strong / Moderate / Weak /
Insufficient Evidence

Repeat for each important finding.

## Comparative Analysis

Compare findings from different sources when relevant.

For example:

- Source [S1] reports ...
- Source [S2] reports ...
- The sources agree/disagree because ...

Do not create comparisons when the sources do not
contain enough information.

## Important Evidence

List the strongest evidence available.

Each item MUST contain a citation.

- Evidence statement [S1]
- Evidence statement [S2]

## Unsupported or Insufficient Claims

List claims that cannot be reliably established
from the retrieved documents.

If none exist, write:

"No major unsupported claims were identified."

## Research Gaps

Identify information that is missing from the
retrieved evidence.

Do not fill these gaps with outside knowledge.

## Source List

List every source actually used.

Use exactly this format:

### [S1] Source Title

URL: https://example.com

### [S2] Source Title

URL: https://example.com

Do NOT write:

URL: Not provided

If a URL is missing from the retrieved document,
write:

URL: Unavailable in retrieved source

====================================================
QUALITY CONTROL
====================================================

Before returning the answer, internally check:

- Does every important claim have a citation?
- Does every citation correspond to an actual source?
- Did I use only retrieved evidence?
- Did I invent any facts?
- Did I invent any URLs?
- Did I distinguish weak evidence?
- Did I preserve source URLs?
- Did I identify research gaps?

If evidence is weak, say so explicitly.
"""
        ),
        (
            "human",
            """
Research Topic:

{topic}


Retrieved Source Documents:

{context}


Analyze the retrieved documents and produce
evidence-grounded research findings.

Remember:

- Use ONLY the provided documents.
- Use [S1], [S2], [S3] exactly as provided.
- Do not invent citations.
- Do not invent URLs.
- Do not use outside knowledge.
- Mark unsupported claims as INSUFFICIENT EVIDENCE.
"""
        ),
    ]
)


chain = prompt | llm


# =====================================================
# Convert LLM Response To Text
# =====================================================

def response_to_text(response):

    content = response.content

    if isinstance(content, str):

        return content

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, dict):

                parts.append(
                    item.get(
                        "text",
                        ""
                    )
                )

            else:

                parts.append(
                    str(item)
                )

        return "".join(parts)

    return str(content)


# =====================================================
# Build Source Context
# =====================================================

def build_context(documents):

    context_parts = []

    for i, document in enumerate(
        documents,
        start=1
    ):

        metadata = document.metadata or {}

        title = metadata.get(
            "title",
            ""
        )

        source = metadata.get(
            "source",
            ""
        )

        query = metadata.get(
            "query",
            ""
        )

        content = (
            document.page_content
            or ""
        )

        context_parts.append(
            f"""
====================================================
[S{i}]
====================================================

Title:
{title}

URL:
{source}

Original Search Query:
{query}

Content:
{content}
"""
        )

    return "\n".join(
        context_parts
    )


# =====================================================
# Research Function
# =====================================================

def research(
    topic: str,
    documents: list
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RAG RESEARCHER"
    )

    print(
        "=" * 70
    )

    # -------------------------------------------------
    # Validate documents
    # -------------------------------------------------

    if not documents:

        print(
            "[Research] No documents available."
        )

        return (
            "# Research Findings\n\n"
            "## Overview\n\n"
            "No relevant source documents were "
            "retrieved.\n\n"
            "## Key Findings\n\n"
            "INSUFFICIENT EVIDENCE\n\n"
            "## Research Gaps\n\n"
            "No source evidence was available."
        )

    print(
        f"[Research] Documents received: "
        f"{len(documents)}"
    )

    # -------------------------------------------------
    # Build source context
    # -------------------------------------------------

    context = build_context(
        documents
    )

    print(
        f"[Research] Context length: "
        f"{len(context)} characters"
    )

    # -------------------------------------------------
    # Show source mapping
    # -------------------------------------------------

    print(
        "\n========== SOURCE MAPPING =========="
    )

    for i, document in enumerate(
        documents,
        start=1
    ):

        metadata = document.metadata or {}

        print(
            f"[S{i}] "
            f"{metadata.get('title', '')}"
        )

        print(
            f"     "
            f"{metadata.get('source', '')}"
        )

    # -------------------------------------------------
    # Invoke LLM
    # -------------------------------------------------

    try:

        response = chain.invoke(
            {
                "topic": topic,
                "context": context,
            }
        )

    except Exception as e:

        print(
            f"[Research] LLM Error: {e}"
        )

        return (
            "# Research Findings\n\n"
            "Research generation failed.\n\n"
            f"Error: {e}"
        )

    # -------------------------------------------------
    # Extract response
    # -------------------------------------------------

    result = response_to_text(
        response
    )

    # -------------------------------------------------
    # Validate output
    # -------------------------------------------------

    if not result.strip():

        return (
            "# Research Findings\n\n"
            "The research model returned no findings."
        )

    # -------------------------------------------------
    # Debug information
    # -------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RESEARCH COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"Research output length: "
        f"{len(result)} characters"
    )

    print(
        "\nPreview:"
    )

    print(
        result[:2000]
    )

    return result