from functools import lru_cache
from uuid import NAMESPACE_URL, uuid5

from gigbid_core.config import settings


@lru_cache(maxsize=1)
def client():
    from qdrant_client import QdrantClient

    return QdrantClient(url=settings().qdrant_url, api_key=settings().qdrant_api_key or None, timeout=15)


def index(collection, items, vectors):
    from qdrant_client.models import Distance, PointStruct, VectorParams

    db = client()
    if not db.collection_exists(collection):
        db.create_collection(
            collection, vectors_config=VectorParams(size=vectors.shape[1], distance=Distance.COSINE)
        )
    db.upsert(
        collection,
        [
            PointStruct(
                id=str(uuid5(NAMESPACE_URL, collection + item["id"])),
                vector=vector.tolist(),
                payload={"index": i, "id": item["id"]},
            )
            for i, (item, vector) in enumerate(zip(items, vectors))
        ],
        wait=True,
    )


def scores(collection, vector, count):
    import numpy as np

    result = client().query_points(collection, query=vector.tolist(), limit=count, with_payload=True)
    values = np.full(count, -1.0)
    for point in result.points:
        values[point.payload["index"]] = point.score
    return values
