from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


# =====================================================
# Reviewer Prompt
# =====================================================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are the FINAL QUALITY CONTROL EDITOR for a Deep Research Agent.

Your job is to review a research report that has already passed
through a research and verification stage.

Your responsibility is NOT to conduct new research.

You must ONLY work with the information already present in the
provided report.

=====================================================
CORE RULES
=====================================================

1. DO NOT introduce new facts.

2. DO NOT use outside knowledge.

3. DO NOT change factual meaning.

4. DO NOT strengthen weak claims.

5. DO NOT turn uncertain findings into confirmed facts.

6. Preserve verification language such as:
   - VERIFIED
   - PARTIALLY VERIFIED
   - UNSUPPORTED
   - CONTRADICTED
   - INSUFFICIENT EVIDENCE

7. If a claim is explicitly marked:
   - UNSUPPORTED
   - CONTRADICTED
   - INSUFFICIENT EVIDENCE

   it must NOT be presented elsewhere in the report as
   an established fact.

8. PARTIALLY VERIFIED claims must retain appropriate
   uncertainty language.

9. Preserve [S1], [S2], [S3], etc. citations exactly.

10. NEVER create a new citation identifier.

11. NEVER invent a source.

12. NEVER invent a URL.

13. NEVER modify source URLs.

14. NEVER remove a source from the Sources section.

15. NEVER add a source that was not already present.

16. Preserve the original source titles and URLs.

17. Remove obvious duplicated paragraphs only when doing so
    does not remove factual information or citations.

18. Improve:
    - grammar
    - readability
    - sentence structure
    - Markdown formatting
    - section organization

19. Keep the report focused on the original research topic.

20. The final conclusion must match the strength of the evidence.

21. If the report says that evidence is limited, the conclusion
    must not claim certainty.

22. Do not add recommendations, predictions, statistics,
    examples, case studies, or explanations that are not already
    present in the report.

=====================================================
CITATION RULE
=====================================================

Every citation such as [S1], [S2], [S3] must remain unchanged.

Do not convert:

[S1]

into:

[1]

Do not create:

[S6]

if [S6] did not already exist.

=====================================================
SOURCE SECTION RULE
=====================================================

The original Sources/References section is authoritative.

Preserve it EXACTLY.

Do not rewrite it.

Do not change:
- source identifiers
- source titles
- URLs
- ordering
- source text

If the report contains either:

## Sources

or:

## References

preserve that entire section exactly as provided.

=====================================================
FINAL REPORT STRUCTURE
=====================================================

Keep the existing report structure whenever possible.

If appropriate, use:

# Research Report

## Executive Summary

## Introduction

## Key Findings

## Detailed Analysis

## Evidence and Verification

## Limitations

## Conclusion

## Sources

Do not invent missing sections simply to make the report longer.

=====================================================
QUALITY CHECK
=====================================================

Before returning the report, internally check:

- Did I introduce any new fact?
- Did I change any factual claim?
- Did I remove uncertainty?
- Did I change any citation?
- Did I create a citation?
- Did I change any URL?
- Did I remove a source?
- Did I add a source?
- Did I make unsupported claims sound verified?
- Does the conclusion match the evidence?

If any answer is YES, correct it before returning the report.

Return ONLY the final Markdown report.
"""
        ),
        (
            "human",
            """
Here is the verified research report.

Review it according to ALL instructions above.

IMPORTANT:
The report itself is the only source of truth available to you.
Do not use outside knowledge.

VERIFIED RESEARCH REPORT:

{report}
"""
        ),
    ]
)


chain = prompt | llm


# =====================================================
# Response Extraction
# =====================================================

def extract_content(response):

    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        return "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    return str(content)


# =====================================================
# Preserve Sources / References
# =====================================================

def preserve_source_section(
    original: str,
    reviewed: str
):

    # -------------------------------------------------
    # Find Sources section
    # -------------------------------------------------

    source_headers = [
        "## Sources",
        "## References",
    ]

    original_header = None
    original_source_content = None

    for header in source_headers:

        if header in original:

            original_header = header

            original_source_content = (
                original.split(
                    header,
                    1
                )[1]
            )

            break

    # -------------------------------------------------
    # No source section
    # -------------------------------------------------

    if original_header is None:

        return reviewed

    # -------------------------------------------------
    # Remove generated source section
    # -------------------------------------------------

    reviewed_before_sources = reviewed

    for header in source_headers:

        if header in reviewed_before_sources:

            reviewed_before_sources = (
                reviewed_before_sources.split(
                    header,
                    1
                )[0]
            )

            break

    # -------------------------------------------------
    # Restore original source section
    # -------------------------------------------------

    reviewed = (
        reviewed_before_sources.rstrip()
        + "\n\n"
        + original_header
        + original_source_content
    )

    return reviewed


# =====================================================
# Remove Accidental Markdown Wrapping
# =====================================================

def clean_markdown_wrapper(text):

    text = text.strip()

    # Sometimes an LLM returns:
    #
    # ```markdown
    # # Research Report
    # ...
    # ```
    #
    # Remove only the outer code fence.

    if text.startswith("```markdown"):

        text = text[len("```markdown"):].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

    elif text.startswith("```"):

        text = text[3:].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

    return text


# =====================================================
# Reviewer
# =====================================================

def review(report: str):

    print("\n" + "=" * 80)
    print("FINAL REPORT REVIEW")
    print("=" * 80)

    if not report:

        print(
            "Reviewer received an empty report."
        )

        return (
            "# Research Report\n\n"
            "No report was available for review."
        )

    print(
        f"Original report length: "
        f"{len(report)} characters"
    )

    # =================================================
    # Run LLM Reviewer
    # =================================================

    try:

        response = chain.invoke(
            {
                "report": report
            }
        )

        reviewed = extract_content(
            response
        )

    except Exception as e:

        print(
            f"Reviewer Error: {e}"
        )

        # IMPORTANT:
        # If review fails, never destroy the
        # already generated report.

        return report

    # =================================================
    # Clean Output
    # =================================================

    reviewed = clean_markdown_wrapper(
        reviewed
    )

    # =================================================
    # Safety Check
    # =================================================

    if not reviewed.strip():

        print(
            "Reviewer returned empty output."
        )

        return report

    # =================================================
    # Preserve Original Sources
    # =================================================

    reviewed = preserve_source_section(
        original=report,
        reviewed=reviewed
    )

    # =================================================
    # Final Debug
    # =================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "FINAL REPORT AFTER REVIEW"
    )

    print(
        "=" * 80
    )

    print(
        f"Final report length: "
        f"{len(reviewed)} characters"
    )

    print(
        "\nPreview:"
    )

    print(
        reviewed[:2000]
    )

    print(
        "\n" + "=" * 80
    )

    return reviewed