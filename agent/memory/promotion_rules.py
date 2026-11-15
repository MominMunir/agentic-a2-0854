import difflib
from collections import Counter

from agent.memory.store import store
from gigbid_core.config import policy
from gigbid_core.db import db, put, records, uid


def observe_edit(tenant, before, after):
    removed = [word.lower() for word in difflib.ndiff(before.split(), after.split()) if word.startswith("- ")]
    with db() as session:
        put(
            session,
            tenant,
            "edit_observation",
            uid(),
            {
                "removed": removed,
                "diff": list(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="")),
            },
        )
        observations = records(session, tenant, "edit_observation")
    config = policy()["memory"]
    if len(observations) < config["minimum_style_observations"]:
        return []
    counts = Counter(word for observation in observations for word in set(observation["removed"]))
    promoted = []
    for word, count in counts.items():
        word = word.removeprefix("- ")
        if count >= config["style_repeat_edits"] and word in {
            "passionate",
            "excited",
            "thrilled",
            "expert",
            "guaranteed",
        }:
            key = "avoid-" + word
            store.put(
                (tenant, "style"),
                key,
                {
                    "rule": "Avoid the word " + word,
                    "observations": count,
                    "promotion_rule": ">=5 edits and repeated deletion in >=3 distinct edits",
                },
            )
            promoted.append(key)
    return promoted


def observe_outcome(tenant, job_id, category, outcome):
    if outcome not in {"won", "replied", "ignored", "hired", "lost"}:
        raise ValueError("Unsupported outcome")
    with db() as session:
        put(
            session,
            tenant,
            "outcome_observation",
            job_id,
            {"job_id": job_id, "category": category, "outcome": outcome},
        )
        observations = [
            x for x in records(session, tenant, "outcome_observation") if x["category"] == category
        ]
    if len(observations) >= policy()["memory"]["minimum_outcomes"]:
        counts = dict(Counter(x["outcome"] for x in observations))
        store.put(
            (tenant, "outcome"),
            category,
            {
                "category": category,
                "counts": counts,
                "n": len(observations),
                "promotion_rule": ">=3 distinct user-confirmed outcomes in category",
            },
        )
