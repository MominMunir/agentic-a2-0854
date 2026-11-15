import numpy as np

from rag.index.embeddings import embed


def correct(query, docs, vectors, ranking, scores):
    """Bounded corrective retrieval: one re-query, then refuse unrelated evidence."""
    from rag.retriever import tokens

    keywords = set(tokens(query)) - {"the", "a", "for", "and", "with", "we", "to", "of", "in", "need", "work"}

    def grade(item):
        return len(keywords & set(tokens(item["text"] + " " + " ".join(item["skills"])))) / max(
            1, min(len(keywords), 8)
        )

    if ranking.size and max(grade(docs[int(i)]) for i in ranking[:5]) < 0.25:
        rewritten = " ".join(sorted(keywords))
        scores = vectors @ embed([rewritten])[0]
        ranking = np.argsort(-scores)
    return np.asarray([i for i in ranking if grade(docs[int(i)]) >= 0.25], dtype=int), scores


def retrieve(items, query, k=5, filters=None):
    from rag.retriever import search

    return search(items, query, k, "v8", filters)
