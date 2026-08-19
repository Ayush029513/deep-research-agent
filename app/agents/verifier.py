from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


# =====================================================
# Verification Prompt
# =====================================================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a STRICT research fact-checking and evidence
verification agent.

Your ONLY job is to verify the research findings against
the provided source evidence.

Do NOT use outside knowledge.

=====================================================
CORE VERIFICATION RULES
=====================================================

1. Every important claim must be checked against the
   provided source evidence.

2. A claim can ONLY be marked VERIFIED if the provided
   evidence directly supports it.

3. Do NOT mark a claim VERIFIED because it sounds
   reasonable or plausible.

4. Do NOT use outside knowledge.

5. Do NOT add new facts.

6. Do NOT create new citations.

7. Do NOT create new URLs.

8. Every [S#] citation must correspond to an actual
   source provided in the evidence.

9. Check whether the cited source actually supports
   the claim.

10. If a source only partially supports a claim, mark:

    PARTIALLY VERIFIED

11. If the source does not support the claim, mark:

    UNSUPPORTED

12. If sources directly disagree, mark:

    CONTRADICTED

13. If there is not enough information to determine
    whether the claim is true, mark:

    INSUFFICIENT EVIDENCE

=====================================================
VERIFICATION LABELS
=====================================================

Use ONLY these labels:

VERIFIED
PARTIALLY VERIFIED
UNSUPPORTED
CONTRADICTED
INSUFFICIENT EVIDENCE

=====================================================
SOURCE VALIDATION
=====================================================

For every citation:

[S1]
[S2]
[S3]

etc.

Check:

1. Does the source exist?
2. Does the source title match?
3. Does the URL match?
4. Does the evidence actually support the claim?

Never invent missing source information.

=====================================================
CLAIM EXTRACTION
=====================================================

Identify the important factual claims in the research.

Do not waste verification space on:

- headings
- formatting
- obvious transitions
- opinions that are clearly identified as opinions

Focus on claims involving:

- facts
- statistics
- dates
- trends
- predictions
- technological developments
- business impacts
- scientific findings
- comparisons
- cause-and-effect statements

=====================================================
EVIDENCE STRENGTH
=====================================================

Use these principles:

DIRECT SUPPORT
The source explicitly states the claim.

→ VERIFIED

PARTIAL SUPPORT
The source supports only part of the claim.

→ PARTIALLY VERIFIED

NO SUPPORT
The source does not support the claim.

→ UNSUPPORTED

CONFLICTING SOURCES
Sources provide contradictory evidence.

→ CONTRADICTED

INSUFFICIENT INFORMATION
The evidence is too weak or incomplete to decide.

→ INSUFFICIENT EVIDENCE

=====================================================
OUTPUT FORMAT
=====================================================

Return Markdown using this structure:

# Verification Report

## Verification Summary

Provide a short overall assessment.

Mention:

- number of sources examined
- major supported findings
- major unsupported findings
- contradictions
- evidence limitations

## Claim Verification

For every important claim:

### Claim 1

**Claim:**
...

**Status:**
VERIFIED / PARTIALLY VERIFIED / UNSUPPORTED /
CONTRADICTED / INSUFFICIENT EVIDENCE

**Evidence:**
...

**Sources:**
[S1]

**Reason:**
...

Repeat for every important claim.

## Supported Findings

List only findings that are directly supported
by the provided evidence.

Include [S#] citations.

## Unsupported or Weak Claims

List claims that are:

- UNSUPPORTED
- PARTIALLY VERIFIED
- INSUFFICIENT EVIDENCE

Explain why.

## Contradictions

Describe conflicts between sources.

If there are none, write:

"No significant contradictions were identified."

## Source Validation

For every source used, verify:

[S1]
[S2]
[S3]

Confirm whether:

- source exists
- title exists
- URL exists
- evidence supports the cited claims

## Evidence Quality

Discuss:

- source relevance
- source duplication
- source quality
- evidence completeness
- missing evidence
- conflicting evidence

## Verification Confidence

Give a score from 0 to 100.

The score MUST reflect the quality of the provided
evidence, not how convincing the research sounds.

Explain the reason for the score.

=====================================================
IMPORTANT
=====================================================

Never transform an unsupported claim into a verified claim.

If the evidence is weak, say so.

If the evidence is missing, say so.

If a URL is missing, do not invent one.

If a source is irrelevant, identify it as irrelevant.

If duplicate sources exist, identify them.

The verification output must remain completely
grounded in the provided source evidence.
"""
        ),
        (
            "human",
            """
Research Topic:
{topic}

=====================================================
RESEARCH FINDINGS TO VERIFY
=====================================================

{research}

=====================================================
ORIGINAL SOURCE EVIDENCE
=====================================================

{context}

=====================================================
FINAL INSTRUCTION
=====================================================

Verify the research findings claim-by-claim.

Use ONLY the source evidence above.

Do not use outside knowledge.

Do not invent facts.

Do not invent citations.

Do not invent URLs.
"""
        ),
    ]
)


chain = prompt | llm


# =====================================================
# Response Extraction
# =====================================================

def extract_response_content(response):

    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, dict):

                text = item.get("text", "")

                if text:
                    parts.append(str(text))

            else:

                parts.append(str(item))

        return "".join(parts)

    return str(content)


# =====================================================
# Build Evidence Context
# =====================================================

def build_evidence_context(documents):

    if not documents:
        return (
            "NO SOURCE DOCUMENTS WERE PROVIDED.\n\n"
            "Claims cannot be independently verified."
        )

    context_parts = []

    for i, doc in enumerate(documents, start=1):

        metadata = doc.metadata or {}

        title = metadata.get("title", "")
        source = metadata.get("source", "")
        query = metadata.get("query", "")

        content = doc.page_content or ""

        context_parts.append(
            f"""
=====================================================
SOURCE [S{i}]
=====================================================

Title:
{title}

URL:
{source}

Original Search Query:
{query}

Evidence:
{content}
"""
        )

    return "\n".join(context_parts)


# =====================================================
# Verification Function
# =====================================================

def verify(
    research: str,
    documents: list = None,
    topic: str = ""
):

    print("\n" + "=" * 80)
    print("VERIFIER")
    print("=" * 80)

    # -------------------------------------------------
    # Validate research
    # -------------------------------------------------

    if not research or not research.strip():

        return (
            "# Verification Report\n\n"
            "No research findings were provided."
        )

    # -------------------------------------------------
    # Validate documents
    # -------------------------------------------------

    documents = documents or []

    print(
        f"Source documents available: "
        f"{len(documents)}"
    )

    # -------------------------------------------------
    # Build evidence
    # -------------------------------------------------

    context = build_evidence_context(documents)

    print(
        f"Evidence context length: "
        f"{len(context)} characters"
    )

    # -------------------------------------------------
    # Run verification
    # -------------------------------------------------

    try:

        response = chain.invoke(
            {
                "topic": topic,
                "research": research,
                "context": context,
            }
        )

    except Exception as e:

        print(f"Verifier Error: {e}")

        return (
            "# Verification Report\n\n"
            "Verification failed.\n\n"
            f"Error: {e}\n\n"
            "## Verification Confidence\n\n"
            "0"
        )

    # -------------------------------------------------
    # Extract result
    # -------------------------------------------------

    result = extract_response_content(response)

    if not result.strip():

        return (
            "# Verification Report\n\n"
            "The verifier returned no result.\n\n"
            "## Verification Confidence\n\n"
            "0"
        )

    # -------------------------------------------------
    # Debug
    # -------------------------------------------------

    print(
        "\n========== VERIFICATION COMPLETED =========="
    )

    print(
        f"Verification output length: "
        f"{len(result)} characters"
    )

    print("\nPreview:")
    print(result[:2500])

    return result