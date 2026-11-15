from agent.nodes.analysis import fit_matcher


async def corrective_retrieval(state):
    """One bounded graph-level re-query using Analyst-extracted requirements."""
    requirements = state.get("spec", {}).get("required_skills", [])
    if state.get("corrective_queries", 0) or not requirements:
        return {"steps": 1}
    retry_state = {**state, "job": {**state["job"], "required_skills": requirements}}
    result = await fit_matcher(retry_state)
    return {**result, "corrective_queries": 1}
