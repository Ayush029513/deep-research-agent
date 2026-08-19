from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert Deep Research Planner.

Convert the user's topic into a structured research plan.

Return:

1. Research Objective
2. Research Questions
3. Important Keywords
4. Recommended Sources
5. Step-by-Step Research Plan
6. Expected Deliverables

Respond in Markdown.
""",
        ),
        ("human", "{topic}"),
    ]
)

planner = planner_prompt | llm


def create_plan(topic: str):
    response = planner.invoke({"topic": topic})

    if isinstance(response.content, str):
        return response.content

    if isinstance(response.content, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in response.content
        )

    return str(response.content)