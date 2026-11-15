from agent.memory.promotion_rules import observe_edit, observe_outcome
from agent.memory.store import delete_memory, read_memory
from rag.ingest.loaders import load_upload


def test_memory_promotion_requires_observations(user):
    for _ in range(4):
        observe_edit(user.id, "I am passionate about this.", "I would propose a milestone.")
    assert not read_memory(user.id, "style")
    observe_edit(user.id, "I am passionate about this.", "I would propose a milestone.")
    assert read_memory(user.id, "style")[0]["key"] == "avoid-passionate"
    assert not read_memory("another-user", "style")
    delete_memory(user.id, "style", "avoid-passionate")
    assert not read_memory(user.id, "style")
    for i in range(2):
        observe_outcome(user.id, str(i), "ml", "replied")
    assert not read_memory(user.id, "outcome")
    observe_outcome(user.id, "2", "ml", "hired")
    assert read_memory(user.id, "outcome")[0]["n"] == 3


def test_incremental_document_ids_are_stable():
    a = load_upload("case.md", b"Built a Python API with typed endpoints.", "own")
    b = load_upload("case.md", b"Built a Python API with typed endpoints.", "own")
    assert a == b
    assert a[0]["provenance"] == "user_upload"
    assert not a[0]["synthetic"]


def test_promoted_memory_namespaces_can_be_listed_and_scoped(user):
    from agent.memory.store import store

    store.put((user.id, "style"), "fixture", {"value": "concise"})
    store.put((user.id, "outcome"), "fixture", {"n": 3})
    assert store.list_namespaces(prefix=(user.id,)) == [(user.id, "outcome"), (user.id, "style")]
    assert store.list_namespaces(prefix=(user.id,), suffix=("style",)) == [(user.id, "style")]
    assert store.list_namespaces(prefix=(user.id,), max_depth=1) == [(user.id,)]
