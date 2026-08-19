from app.agents.researcher import summarize

article = """
Large Language Models are transforming healthcare.
They assist doctors in diagnosis, automate medical documentation,
predict diseases, and improve patient outcomes through AI-powered
decision support systems.
"""

print(summarize(article))