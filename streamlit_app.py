import streamlit as st

from app.graph.workflow import graph
from app.utils.report import save_report


NODE_LABELS = {
    "planner": "Creating research plan",
    "query_planner": "Generating search queries",
    "search": "Searching, crawling, and ingesting sources",
    "research": "Running RAG research",
    "verifier": "Verifying facts",
    "writer": "Writing report",
    "reviewer": "Reviewing final report",
}


st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🔬",
    layout="wide",
)

st.title("Deep Research Agent")
st.caption(
    "Multi-agent research pipeline: plan, search, crawl, RAG, verify, write, and review."
)

with st.sidebar:
    st.header("Pipeline")
    for node, label in NODE_LABELS.items():
        st.markdown(f"- **{label}**")

    st.divider()
    st.markdown(
        "Reports are saved to `app/reports/report.md` after each run."
    )

topic = st.text_input(
    "Research topic",
    placeholder="e.g. Latest developments in generative AI in 2026",
)

run = st.button("Start Research", type="primary", disabled=not topic.strip())

if run:
    progress = st.progress(0, text="Starting pipeline...")
    status = st.empty()
    results = {}

    steps = list(NODE_LABELS.keys())

    for i, event in enumerate(graph.stream({"topic": topic.strip()})):
        node_name = next(iter(event))
        node_output = event[node_name]
        results.update(node_output)

        label = NODE_LABELS.get(node_name, node_name)
        progress.progress((i + 1) / len(steps), text=label)
        status.success(f"Done: {label}")

    progress.progress(1.0, text="Research complete")
    save_report(results["final_report"])

    st.divider()

    tab_plan, tab_queries, tab_research, tab_report = st.tabs(
        ["Plan", "Queries", "Research Notes", "Final Report"]
    )

    with tab_plan:
        st.markdown(results.get("research_plan", ""))

    with tab_queries:
        for q in results.get("search_queries", []):
            st.markdown(f"- {q}")

    with tab_research:
        st.markdown(results.get("research", ""))

    with tab_report:
        st.markdown(results["final_report"])
        st.download_button(
            "Download report",
            data=results["final_report"],
            file_name="research_report.md",
            mime="text/markdown",
        )
