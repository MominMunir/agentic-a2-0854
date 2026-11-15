import hashlib
import json
import re
from functools import lru_cache
from threading import RLock

import numpy as np
from rank_bm25 import BM25Okapi

from gigbid_core.config import ROOT, settings
from rag.index.embeddings import embed


def tokens(text):
    return re.findall(r"[a-z0-9+#.-]+", text.lower())


_index_lock = RLock()


def build_index(serialized, backend):
    # HTTP searches can overlap while CPU work runs outside the API event loop.
    # Serialize cache creation so identical requests cannot race the temp file.
    with _index_lock:
        return _cached_index(serialized, backend)


@lru_cache(maxsize=8)
def _cached_index(serialized, backend):
    items = json.loads(serialized)
    texts = [
        item["title"]
        + "\n"
        + item["text"]
        + "\nSkills: "
        + ", ".join(item["skills"])
        + "\nIndustry: "
        + item.get("industry", "")
        for item in items
    ]
    cache = ROOT / ".cache/vectors"
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(("document-header-v2:" + backend + serialized).encode()).hexdigest()
    path = cache / (key + ".npy")
    if path.exists():
        vectors = np.load(path, allow_pickle=False)
    else:
        vectors = embed(texts)
        temp = cache / (key + ".tmp.npy")
        np.save(temp, vectors)
        temp.replace(path)
    collection = "evidence_" + key[:20]
    if settings().qdrant_url:
        from rag.index.qdrant_store import index

        index(collection, items, vectors)
    return items, vectors, BM25Okapi([tokens(t) for t in texts]), collection


def search(items, query, k=5, variant=None, filters=None):
    variant = variant or settings().rag_variant
    filters = filters or {}
    allowed = {"persona", "type", "industry", "project", "outcome"}
    if set(filters) - allowed:
        raise ValueError("Unsupported metadata filter")
    subset = [x for x in items if all(x.get(key) == val for key, val in filters.items())]
    if not subset:
        return []
    docs, vectors, bm25, collection = build_index(
        json.dumps(subset, sort_keys=True), settings().embedding_backend
    )
    vector = embed([query])[0]
    if settings().qdrant_url:
        from rag.index.qdrant_store import scores as vector_scores

        dense = vector_scores(collection, vector, len(docs))
    else:
        dense = vectors @ vector
    ranking = np.argsort(-dense)
    scores = dense.copy()
    if variant in {"v1", "v2", "v3", "v4", "v8"}:
        if variant == "v1":
            requirements = [q.strip() for q in re.split(r"[,;\n]|\band\b", query) if q.strip()]
            scores = np.max(vectors @ embed(requirements).T, axis=1)
        else:
            lexical = bm25.get_scores(tokens(query))
            fused = np.zeros(len(docs))
            for order in [np.argsort(-dense), np.argsort(-lexical)]:
                for rank, idx in enumerate(order):
                    fused[idx] += 1 / (60 + rank + 1)
            scores = fused
        ranking = np.argsort(-scores)
    if variant == "v4":
        scores = scores + np.asarray(
            [0.004 if d["outcome"] == "won" else 0.002 if d["outcome"] == "replied" else 0 for d in docs]
        )
        ranking = np.argsort(-scores)
    if variant == "v3":
        from flashrank import RerankRequest

        results = reranker().rerank(
            RerankRequest(
                query=query, passages=[{"id": int(i), "text": docs[i]["text"]} for i in ranking[: max(20, k)]]
            )
        )
        ranking = np.asarray([int(r["id"]) for r in results])
        for r in results:
            scores[int(r["id"])] = float(r["score"])
    if variant == "v8":
        from rag.variants.v8_corrective import correct

        ranking, scores = correct(query, docs, vectors, ranking, scores)
    output = []
    for idx in ranking[:k]:
        item = dict(docs[int(idx)])
        item["score"] = float(scores[int(idx)])
        item["retrieval_variant"] = variant
        output.append(item)
    return output


@lru_cache(maxsize=1)
def reranker():
    from flashrank import Ranker
    from gigbid_core.config import policy

    return Ranker(model_name=policy()["models"]["reranker_model"], cache_dir=str(ROOT / ".cache/reranker"))
