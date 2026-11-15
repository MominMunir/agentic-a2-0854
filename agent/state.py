import operator
from typing import Annotated, TypedDict


class BidState(TypedDict, total=False):
    tenant: str
    run_id: str
    job: dict
    profile: dict
    spec: dict
    risk: dict
    fit: dict
    evidence: list[dict]
    decision: dict
    price: dict
    draft: dict
    verification: dict
    critique: dict
    compliance: dict
    revision: int
    approval: dict
    preview: dict
    outcome: dict
    status: str
    usage: Annotated[list[dict], operator.add]
    steps: Annotated[int, operator.add]
    corrective_queries: int
    conversation_id: str
    messages: list[dict]
    intent: str
    slots: list[dict]
    regenerate_index: int | None
    replay_of: str
