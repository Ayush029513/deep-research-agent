from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

print("Model loaded!")

emb = model.encode("Hello World")

print(emb.shape)