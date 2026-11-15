import asyncio
from datetime import datetime

from langgraph.store.base import BaseStore, GetOp, Item, ListNamespacesOp, PutOp, SearchItem, SearchOp

from gigbid_core.db import Record, db, get, now, put, records


class DurableMemoryStore(BaseStore):
    """LangGraph Store backed by the application's SQLite/Postgres transaction layer."""

    def batch(self, ops):
        results = []
        with db() as session:
            for op in ops:
                if isinstance(op, GetOp):
                    value = get(session, op.namespace[0], "memory_" + op.namespace[1], op.key)
                    results.append(
                        Item(
                            value=value,
                            key=op.key,
                            namespace=op.namespace,
                            created_at=datetime.fromisoformat(value["promoted_at"]),
                            updated_at=datetime.fromisoformat(value["promoted_at"]),
                        )
                        if value
                        else None
                    )
                elif isinstance(op, PutOp):
                    if op.value is None:
                        row = session.get(Record, f"{op.namespace[0]}:memory_{op.namespace[1]}:{op.key}")
                        if row:
                            session.delete(row)
                    else:
                        put(
                            session,
                            op.namespace[0],
                            "memory_" + op.namespace[1],
                            op.key,
                            {**op.value, "key": op.key, "promoted_at": op.value.get("promoted_at", now())},
                        )
                    results.append(None)
                elif isinstance(op, SearchOp):
                    values = records(session, op.namespace_prefix[0], "memory_" + op.namespace_prefix[1])
                    values = [
                        v for v in values if not op.filter or all(v.get(k) == x for k, x in op.filter.items())
                    ]
                    results.append(
                        [
                            SearchItem(
                                namespace=op.namespace_prefix,
                                key=v["key"],
                                value=v,
                                created_at=datetime.fromisoformat(v["promoted_at"]),
                                updated_at=datetime.fromisoformat(v["promoted_at"]),
                            )
                            for v in values[op.offset : op.offset + op.limit]
                        ]
                    )
                elif isinstance(op, ListNamespacesOp):
                    namespaces = {
                        (r.tenant, r.kind.removeprefix("memory_"))
                        for r in session.query(Record).filter(Record.kind.like("memory_%")).all()
                    }
                    for condition in op.match_conditions or ():

                        def matches(namespace):
                            path = condition.path
                            if len(path) > len(namespace):
                                return False
                            segment = (
                                namespace[: len(path)]
                                if condition.match_type == "prefix"
                                else namespace[-len(path) :]
                                if path
                                else ()
                            )
                            return all(
                                expected == "*" or actual == expected
                                for actual, expected in zip(segment, path)
                            )

                        namespaces = {ns for ns in namespaces if matches(ns)}
                    if op.max_depth is not None:
                        namespaces = {ns[: op.max_depth] for ns in namespaces}
                    results.append(sorted(namespaces)[op.offset : op.offset + op.limit])
                else:
                    raise TypeError(type(op).__name__)
        return results

    async def abatch(self, ops):
        return await asyncio.to_thread(self.batch, list(ops))


store = DurableMemoryStore()


def read_memory(tenant, kind):
    return [item.value for item in store.search((tenant, kind), limit=100)]


def delete_memory(tenant, kind, key):
    store.delete((tenant, kind), key)
