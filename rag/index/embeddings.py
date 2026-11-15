"""Open CPU embeddings; explicit hash backend only for deterministic CI smoke tests."""

import hashlib
from functools import lru_cache

import numpy as np

from gigbid_core.config import ROOT, policy, settings


@lru_cache(maxsize=1)
def model():
    from fastembed import TextEmbedding

    return TextEmbedding(
        policy()["models"]["embedding_model"],
        cache_dir=str(ROOT / ".cache/models"),
        threads=settings().embedding_threads,
        enable_cpu_mem_arena=not settings().embedding_low_memory,
    )


def embed(texts):
    if settings().embedding_backend == "hash_smoke":
        import re

        output = np.zeros((len(texts), 384), dtype=np.float32)
        for i, text in enumerate(texts):
            for word in re.findall(r"[a-z0-9+#.-]+", text.lower()):
                digest = hashlib.sha256(word.encode()).digest()
                output[i, int.from_bytes(digest[:4], "little") % 384] += 1
    else:
        output = np.asarray(
            list(model().embed(texts, batch_size=settings().embedding_batch_size)), dtype=np.float32
        )
    norm = np.linalg.norm(output, axis=1, keepdims=True)
    return output / np.maximum(norm, 1e-9)
