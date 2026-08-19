from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from urllib.parse import urlparse

from app.graph.state import ResearchState

from app.agents.planner import create_plan
from app.agents.query_planner import generate_queries
from app.agents.rag_researcher import research
from app.agents.verifier import verify
from app.agents.writer import write_report
from app.agents.reviewer import review
from app.utils.citation_validator import validate_citations
from app.tools.search.search_manager import search_manager
from app.tools.crawl import crawl_url
from app.tools.text_splitter import split_text

from app.tools.vector_search import (
    store_documents,
    reset_database,
    search_documents,
    count_documents,
)

from app.utils.report import save_report


# =====================================================
# Utility Functions
# =====================================================

def normalize_url(url: str) -> str:
    """
    Normalize URL so small URL differences do not create
    duplicate crawling/retrieval entries.
    """

    if not url:
        return ""

    try:
        parsed = urlparse(url)

        return (
            parsed.netloc.lower().strip()
            + parsed.path.rstrip("/")
        )

    except Exception:
        return url.strip().lower().rstrip("/")


def diversify_documents(
    documents,
    max_per_source=2,
):
    """
    Prevent one website from dominating the retrieved context.

    Example:

    Source A -> maximum 2 chunks
    Source B -> maximum 2 chunks
    Source C -> maximum 2 chunks

    This improves source diversity for the research agent.
    """

    selected = []
    source_counts = {}

    for doc in documents:

        source = doc.metadata.get(
            "source",
            ""
        )

        source_key = normalize_url(source)

        if not source_key:
            source_key = "unknown_source"

        current_count = source_counts.get(
            source_key,
            0
        )

        if current_count >= max_per_source:
            continue

        selected.append(doc)

        source_counts[source_key] = (
            current_count + 1
        )

    return selected


def extract_response_content(response) -> str:
    """
    Safely extract text from an LLM response.
    """

    content = getattr(
        response,
        "content",
        response
    )

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
# Planner
# =====================================================

def planner_node(state: ResearchState):

    print("\n========== PLANNER ==========")

    topic = state.get(
        "topic",
        ""
    ).strip()

    if not topic:
        raise ValueError(
            "Research topic is missing."
        )

    try:

        plan = create_plan(topic)

        print("\nResearch Plan:")
        print(plan)

        return {
            "research_plan": plan
        }

    except Exception as e:

        print(
            f"Planner Error: {e}"
        )

        return {
            "research_plan": (
                f"Unable to create research plan: {e}"
            )
        }


# =====================================================
# Query Planner
# =====================================================

def query_planner_node(state: ResearchState):

    print("\n========== QUERY PLANNER ==========")

    topic = state.get(
        "topic",
        ""
    ).strip()

    if not topic:
        raise ValueError(
            "Research topic is missing."
        )

    try:

        queries = generate_queries(topic)

        if not queries:
            queries = [topic]

        # Remove duplicate queries
        queries = list(
            dict.fromkeys(
                q.strip()
                for q in queries
                if q and q.strip()
            )
        )

        print("\nGenerated Queries:")

        for q in queries:
            print("-", q)

        return {
            "search_queries": queries
        }

    except Exception as e:

        print(
            f"Query Planner Error: {e}"
        )

        return {
            "search_queries": [topic]
        }


# =====================================================
# Search + Crawl + Ingestion + Retrieval
# =====================================================

def search_node(state: ResearchState):

    print("\n========== SEARCH ==========")

    # -------------------------------------------------
    # Reset vector database
    # -------------------------------------------------

    try:

        reset_database()

        print(
            "Vector database reset successfully."
        )

    except Exception as e:

        print(
            f"Database reset error: {e}"
        )

    results = []
    all_chunks = []

    # -------------------------------------------------
    # Duplicate protection
    # -------------------------------------------------

    seen_urls = set()

    search_queries = state.get(
        "search_queries",
        []
    )

    if not search_queries:

        topic = state.get(
            "topic",
            ""
        )

        if topic:
            search_queries = [topic]

    # =================================================
    # SEARCH EACH QUERY
    # =================================================

    for query in search_queries:

        print(
            f"\nSearching: {query}"
        )

        try:

            search_results = search_manager(
                query=query,
                max_results=3
            )

            print(
                f"Search manager returned "
                f"{len(search_results)} results"
            )

            results.extend(
                search_results
            )

        except Exception as e:

            print(
                f"Search Error for "
                f"'{query}': {e}"
            )

            continue

        # =================================================
        # CRAWL SEARCH RESULTS
        # =================================================

        for result in search_results:

            try:

                url = result.get(
                    "url",
                    ""
                )

                # -----------------------------------------
                # Validate URL
                # -----------------------------------------

                if not url.startswith(
                    (
                        "http://",
                        "https://"
                    )
                ):

                    print(
                        "Skipped invalid URL:",
                        url
                    )

                    continue

                # -----------------------------------------
                # Normalize URL
                # -----------------------------------------

                normalized_url = normalize_url(
                    url
                )

                # -----------------------------------------
                # Avoid duplicate crawling
                # -----------------------------------------

                if normalized_url in seen_urls:

                    print(
                        "Skipped duplicate URL:",
                        url
                    )

                    continue

                seen_urls.add(
                    normalized_url
                )

                print(
                    f"\nCrawling: {url}"
                )

                # -----------------------------------------
                # Crawl webpage
                # -----------------------------------------

                text = crawl_url(url)

                if not text:

                    print(
                        "Skipped: empty content"
                    )

                    continue

                text = text.strip()

                # -----------------------------------------
                # Minimum content check
                # -----------------------------------------

                if len(text) < 500:

                    print(
                        "Skipped: insufficient content"
                    )

                    continue

                print(
                    f"Crawled characters: "
                    f"{len(text)}"
                )

                # -----------------------------------------
                # Split into chunks
                # -----------------------------------------

                chunks = split_text(
                    text
                )

                print(
                    f"Created {len(chunks)} chunks"
                )

                # -----------------------------------------
                # Create LangChain Documents
                # -----------------------------------------

                for chunk in chunks:

                    if not chunk or not chunk.strip():
                        continue

                    document = Document(
                        page_content=chunk,
                        metadata={
                            "source": url,

                            "title": result.get(
                                "title",
                                ""
                            ),

                            "query": query,

                            "search_source": result.get(
                                "source",
                                ""
                            ),
                        }
                    )

                    all_chunks.append(
                        document
                    )

            except Exception as e:

                print(
                    f"Crawl Error: {e}"
                )

                continue

    # =====================================================
    # DOCUMENT INGESTION
    # =====================================================

    print(
        "\n========== DOCUMENT INGESTION =========="
    )

    print(
        f"Total chunks created: "
        f"{len(all_chunks)}"
    )

    if all_chunks:

        try:

            store_documents(
                all_chunks
            )

            print(
                f"Stored {len(all_chunks)} "
                f"chunks in vector database."
            )

        except Exception as e:

            print(
                f"Vector storage error: {e}"
            )

    else:

        print(
            "No documents available for storage."
        )

    # =====================================================
    # VECTOR DATABASE
    # =====================================================

    print(
        "\n========== VECTOR DATABASE =========="
    )

    try:

        document_count = count_documents()

        print(
            f"Stored Documents: "
            f"{document_count}"
        )

    except Exception as e:

        print(
            f"Database count error: {e}"
        )

        document_count = 0

    # =====================================================
    # RETRIEVAL
    # =====================================================

    docs = []

    topic = state.get(
        "topic",
        ""
    ).strip()

    if document_count > 0 and topic:

        try:

            # Retrieve more candidates first
            raw_docs = search_documents(
                topic,
                k=15
            )

            print(
                f"Raw retrieved documents: "
                f"{len(raw_docs)}"
            )

            # ---------------------------------------------
            # Diversify sources
            # ---------------------------------------------

            docs = diversify_documents(
                raw_docs,
                max_per_source=2
            )

            print(
                f"Documents after source "
                f"diversification: {len(docs)}"
            )

        except Exception as e:

            print(
                f"Retrieval Error: {e}"
            )

    else:

        print(
            "No documents available "
            "for retrieval."
        )

    # =====================================================
    # RETRIEVAL SOURCE DEBUG
    # =====================================================

    print(
        "\n========== RETRIEVAL SOURCES =========="
    )

    for i, doc in enumerate(
        docs,
        start=1
    ):

        print(
            f"\n{i}. "
            f"{doc.metadata.get('title', 'Unknown')}"
        )

        print(
            f"   Source: "
            f"{doc.metadata.get('source', '')}"
        )

        print(
            f"   Search Source: "
            f"{doc.metadata.get('search_source', '')}"
        )

    # =====================================================
    # RETRIEVED DOCUMENT DEBUG
    # =====================================================

    print(
        "\n========== RETRIEVED DOCUMENTS =========="
    )

    for i, doc in enumerate(
        docs,
        start=1
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            f"RETRIEVED DOCUMENT {i}"
        )

        print(
            "=" * 60
        )

        print(
            "\nMetadata:"
        )

        print(
            doc.metadata
        )

        print(
            "\nContent Preview:"
        )

        print(
            doc.page_content[:500]
        )

    # =====================================================
    # RETURN STATE
    # =====================================================

    return {
        "search_results": results,
        "retrieved_documents": docs
    }


# =====================================================
# Research
# =====================================================

def research_node(state: ResearchState):

    print(
        "\n========== RESEARCH =========="
    )

    documents = state.get(
        "retrieved_documents",
        []
    )

    print(
        f"Retrieved documents available: "
        f"{len(documents)}"
    )

    if not documents:

        print(
            "WARNING: No retrieved documents "
            "available for research."
        )

        return {
            "research": (
                "No reliable documents were retrieved "
                "from the research sources. "
                "Research cannot be completed reliably."
            )
        }

    try:

        result = research(
            state["topic"],
            documents
        )

        print(
            "\nResearch completed successfully."
        )

        print(
            f"Research length: "
            f"{len(result)} characters"
        )

        return {
            "research": result
        }

    except Exception as e:

        print(
            f"Research Error: {e}"
        )

        return {
            "research": (
                f"Research failed due to an error: {e}"
            )
        }


# =====================================================
# Verifier
# =====================================================

def verifier_node(state: ResearchState):

    print(
        "\n========== VERIFIER =========="
    )

    research_text = state.get(
        "research",
        ""
    )

    documents = state.get(
        "retrieved_documents",
        []
    )

    topic = state.get(
        "topic",
        ""
    )

    print(
        f"Research length: "
        f"{len(research_text)} characters"
    )

    print(
        f"Retrieved documents for verification: "
        f"{len(documents)}"
    )

    if not research_text:

        return {
            "verified": (
                "## Verification Summary\n\n"
                "No research findings were available "
                "for verification."
            )
        }

    try:

        verified = verify(
            research=research_text,
            documents=documents,
            topic=topic
        )

    except Exception as e:

        print(
            f"Verifier Node Error: {e}"
        )

        verified = (
            "## Verification Summary\n\n"
            "Verification failed.\n\n"
            f"Error: {e}"
        )

    print(
        f"Verification length: "
        f"{len(verified)} characters"
    )

    # Debug: show actual verifier output
    print("\n========== VERIFIED RESULT ==========")
    print(verified)
    print("=====================================")

    return {
        "verified": verified
    }

# =====================================================
# Writer
# =====================================================

def writer_node(state: ResearchState):

    print("\n========== WRITER ==========")

    verified = state.get("verified", "")
    topic = state.get("topic", "")

    print(f"Verified research length: {len(verified)}")

    if not verified:
        print("No verified research available.")

        return {
            "report": ""
        }

    try:

        report = write_report(
            verified=verified,
            topic=topic
        )

        if not report:
            print("Writer returned an empty report.")

            return {
                "report": ""
            }

        print(
            f"Report generated successfully: "
            f"{len(report)} characters"
        )

        return {
            "report": report
        }

    except Exception as e:

        print(f"Writer Error: {e}")

        return {
            "report": ""
        }

# =====================================================
# Reviewer
# =====================================================

def reviewer_node(state: ResearchState):

    print(
        "\n========== REVIEWER =========="
    )

    report = state.get(
        "report",
        ""
    )

    if not report:

        print(
            "WARNING: No report available "
            "for review."
        )

        fallback_report = (
            "# Research Report\n\n"
            "No report was available "
            "for final review."
        )

        return {
            "final_report": fallback_report
        }

    print(
        f"Report received for review: "
        f"{len(report)} characters"
    )

    try:

        final_report = review(
            report
        )

        if not final_report:

            print(
                "Reviewer returned empty output."
            )

            final_report = report

        # ---------------------------------------------
        # Save final report
        # ---------------------------------------------

        try:

            save_report(
                final_report
            )

            print(
                "\nFinal report saved successfully."
            )

        except Exception as e:

            print(
                f"Report save error: {e}"
            )

        # ---------------------------------------------
        # Debug
        # ---------------------------------------------

        print(
            "\n========== REVIEW COMPLETED =========="
        )

        print(
            f"Final report length: "
            f"{len(final_report)} characters"
        )

        print(
            "\nFinal Report Preview:"
        )

        print(
            final_report[:1500]
        )

        return {
            "final_report": final_report
        }

    except Exception as e:

        print(
            f"Reviewer Error: {e}"
        )

        # Preserve the generated report
        return {
            "final_report": report
        }

# =====================================================
# Citation Validator
# =====================================================

def citation_validator_node(state: ResearchState):

    print("\n========== CITATION VALIDATOR ==========")

    report = state.get(
        "final_report",
        ""
    )

    documents = state.get(
        "retrieved_documents",
        []
    )

    validation = validate_citations(
        report,
        documents
    )

    return {
        "citation_validation": validation
    }
# =====================================================
# BUILD LANGGRAPH
# =====================================================

builder = StateGraph(
    ResearchState
)


# =====================================================
# Nodes
# =====================================================

builder.add_node(
    "planner",
    planner_node
)

builder.add_node(
    "query_planner",
    query_planner_node
)

builder.add_node(
    "search",
    search_node
)

builder.add_node(
    "research",
    research_node
)

builder.add_node(
    "verifier",
    verifier_node
)

builder.add_node(
    "writer",
    writer_node
)

builder.add_node(
    "reviewer",
    reviewer_node
)
builder.add_node(
    "citation_validator",
    citation_validator_node
)


# =====================================================
# Entry Point
# =====================================================

builder.set_entry_point(
    "planner"
)


# =====================================================
# Edges
# =====================================================

builder.add_edge(
    "planner",
    "query_planner"
)

builder.add_edge(
    "query_planner",
    "search"
)

builder.add_edge(
    "search",
    "research"
)

builder.add_edge(
    "research",
    "verifier"
)

builder.add_edge(
    "writer",
    "reviewer"
)
builder.add_edge(
    "verifier",
    "writer"
)
builder.add_edge(
    "reviewer",
    "citation_validator"
)

builder.add_edge(
    "citation_validator",
    END
)


# =====================================================
# Compile Graph
# =====================================================

graph = builder.compile()