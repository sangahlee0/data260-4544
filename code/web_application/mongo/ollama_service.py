import os
from langchain_ollama import OllamaEmbeddings

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

def get_embedding_model():
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_URL
    )

def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.embed_query(text)
