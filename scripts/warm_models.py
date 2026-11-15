from rag.index.embeddings import embed
from rag.retriever import reranker

if __name__ == "__main__":
    print("Downloading open CPU embedding and reranker weights into ignored local cache.")
    print("Embedding shape:", embed(["reproducible portfolio evidence"]).shape)
    reranker()
    print("Open retrieval models ready.")
