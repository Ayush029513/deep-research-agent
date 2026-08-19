from app.graph.workflow import graph


def main():

    print("\n" + "=" * 80)
    print("DEEP RESEARCH AGENT")
    print("=" * 80)

    topic = input(
        "\nEnter research topic: "
    ).strip()

    if not topic:
        print("Please enter a research topic.")
        return

    initial_state = {
        "topic": topic,
        "research_plan": "",
        "search_queries": [],
        "search_results": [],
        "retrieved_documents": [],
        "research": "",
        "verified": "",
        "report": "",
        "final_report": "",
    }

    print("\nStarting research...\n")

    try:

        result = graph.invoke(
            initial_state
        )

    except Exception as e:

        print("\n" + "=" * 80)
        print("GRAPH EXECUTION FAILED")
        print("=" * 80)

        print(e)

        return

    print("\n" + "=" * 80)
    print("RESEARCH COMPLETED")
    print("=" * 80)

    final_report = result.get(
        "final_report",
        ""
    )

    if final_report:

        print("\nFINAL REPORT\n")
        print(final_report)

    else:

        print(
            "\nNo final report was returned."
        )

    print("\n" + "=" * 80)
    print("STATE SUMMARY")
    print("=" * 80)

    print(
        "Search results:",
        len(
            result.get(
                "search_results",
                []
            )
        )
    )

    print(
        "Retrieved documents:",
        len(
            result.get(
                "retrieved_documents",
                []
            )
        )
    )

    print(
        "Research length:",
        len(
            result.get(
                "research",
                ""
            )
        )
    )

    print(
        "Verification length:",
        len(
            result.get(
                "verified",
                ""
            )
        )
    )

    print(
        "Report length:",
        len(
            result.get(
                "report",
                ""
            )
        )
    )

    print(
        "Final report length:",
        len(
            result.get(
                "final_report",
                ""
            )
        )
    )


if __name__ == "__main__":
    main()