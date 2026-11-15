from rag.retriever import search


def retrieve(items, query, k=5, filters=None):
    return search(items, query, k, "v2", filters)
