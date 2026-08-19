from dotenv import load_dotenv
import os

from app.config import llm
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()



prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert researcher.

Summarize the article.

Return:

- Key Findings
- Important Facts
- Technologies Mentioned
- Summary
"""
        ),
        ("human", "{article}")
    ]
)

chain = prompt | llm


def summarize(article: str):
    response = chain.invoke({"article": article})

    if isinstance(response.content, str):
        return response.content

    if isinstance(response.content, list):
        text = ""

        for item in response.content:
            if isinstance(item, dict):
                text += item.get("text", "")
            else:
                text += str(item)

        return text

    return str(response.content)