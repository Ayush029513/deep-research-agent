from app.config import llm

response = llm.invoke("Explain what RAG is in one sentence.")

print(response.content)