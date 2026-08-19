from app.graph.workflow import graph


def main():
    topic = input("\nEnter research topic: ").strip()

    if not topic:
        print("Topic cannot be empty.")
        return

    print(f"\nStarting deep research on: {topic}\n")

    result = graph.invoke({"topic": topic})

    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80)
    print(result["final_report"])
    print("\nReport saved to app/reports/report.md")


if __name__ == "__main__":
    main()
