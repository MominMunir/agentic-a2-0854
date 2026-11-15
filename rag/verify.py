import re

PAST = re.compile(
    r"\b(?:built|delivered|created|achieved|worked|experience|years|certified|increased|reduced|trained|implemented|expert|specialist|successfully)\b",
    re.I,
)
FUTURE = re.compile(
    r"\b(?:propose|would|will|could|suggest|plan to|can discuss)\b|^(?:your\b|please\b|available interview|which\b|what\b|how\b)",
    re.I,
)
FORBIDDEN = re.compile(
    r"guarantee|100%|\b(?:whatsapp|telegram|paypal)\b|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+\d[\d ()-]{7,}", re.I
)


def split_claims(text):
    # Citation IDs may include periods, so punctuation inside brackets is preserved.
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z"“])|\n\s*\n', text) if s.strip()]


def verify(text, evidence):
    by_id = {e["id"]: e for e in evidence}
    claims = []
    for sentence in split_claims(text):
        citations = re.findall(r"\[([^\]]+)\]", sentence)
        content = re.sub(r"\[[^\]]+\]", "", sentence).strip().strip('"“” ')
        references = [by_id[c] for c in citations if c in by_id]
        status, reason = "supported", "Future approach or non-experience statement"
        if FORBIDDEN.search(sentence):
            status, reason = "unsupported", "Contact details, off-platform language or guarantee"
        elif citations or PAST.search(sentence) or not FUTURE.search(sentence):
            normalized = re.sub(r"\s+", " ", content).lower().rstrip(".")
            # Exact extractive grounding is conservative: paraphrases require review.
            if not references:
                status, reason = "unsupported", "Experience claim lacks a valid evidence citation"
            elif not any(normalized in re.sub(r"\s+", " ", e["text"]).lower() for e in references):
                status, reason = (
                    "partly_supported",
                    "Cited text does not entail the complete sentence verbatim",
                )
            else:
                reason = "Exact evidence passage with valid citation"
        claims.append(
            {
                "text": sentence,
                "status": status,
                "evidence_ids": [e["id"] for e in references],
                "reason": reason,
            }
        )
    clean = "\n\n".join(c["text"] for c in claims if c["status"] == "supported")
    return {
        "claims": claims,
        "text": clean,
        "unsupported_before": sum(c["status"] != "supported" for c in claims),
        "unsupported_after": 0,
    }


def compliance(text):
    from gigbid_core.config import policy

    violations = []
    if FORBIDDEN.search(text):
        violations.append("Remove contact details, guarantees and off-platform requests.")
    if len(text.split()) > policy()["marketplace"]["maximum_proposal_words"]:
        violations.append("Proposal exceeds configured maximum length.")
    return {"allowed": not violations, "violations": violations}
