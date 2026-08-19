import json

from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert research planner.

Generate exactly 5 focused search queries.

Return ONLY a JSON array.

Example:

[
 "Latest AI Trends 2026",
 "Enterprise AI Adoption",
 "Autonomous AI Systems",
 "AI Agents",
 "Future of Artificial Intelligence"
]
"""
        ),
        ("human", "{topic}")
    ]
)

chain = prompt | llm


def generate_queries(topic: str):

    response = chain.invoke({"topic": topic})

    text = (
        response.content
        if isinstance(response.content, str)
        else "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in response.content
        )
    )

    return json.loads(text)