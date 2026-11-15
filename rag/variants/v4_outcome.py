from rag.retriever import search


def retrieve(items, query, k=5, filters=None):
    return search(items, query, k, "v4", filters)
