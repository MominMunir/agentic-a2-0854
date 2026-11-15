from typing import Literal

from pydantic import BaseModel, Field


class JobSpec(BaseModel):
    job_id: str
    title: str
    deliverables: list[str]
    required_skills: list[str]
    budget_min: float = Field(ge=0)
    budget_max: float = Field(ge=0)
    timeline_days: int = Field(ge=1, le=3650)
    screening_questions: list[str] = []
    hidden_needs: list[str] = []


class RiskReport(BaseModel):
    score: float = Field(ge=0, le=1)
    flags: list[str]
    explanation: str
    injection_detected: bool = False


class FitReport(BaseModel):
    score: float = Field(ge=0, le=1)
    matched_skills: list[str]
    missing_skills: list[str]
    evidence_ids: list[str]
    matrix: list[dict]


class BidDecision(BaseModel):
    action: Literal["bid", "watch", "skip"]
    reasons: list[str]


class PriceQuote(BaseModel):
    amount: float = Field(ge=0)
    currency: Literal["USD"] = "USD"
    connects: int = Field(ge=0)
    rationale: str
    within_budget: bool


class ProposalDraft(BaseModel):
    cover_letter: str = Field(min_length=10, max_length=10000)
    screening_answers: list[str] = []
    evidence_ids: list[str] = []


class Critique(BaseModel):
    accepted: bool
    reasons: list[str]


class ComplianceVerdict(BaseModel):
    allowed: bool
    violations: list[str]


class ApprovalRequest(BaseModel):
    decision: Literal["approve", "reject", "edit"]
    text: str | None = Field(default=None, max_length=10000)
    reason: str = Field(default="", max_length=1000)
    approval_token: str = ""


class ProposalWrite(BaseModel):
    job_id: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=10, max_length=10000)
    bid: float = Field(ge=0, le=1000000)
    idempotency_key: str = Field(min_length=8, max_length=160)
    dry_run: bool = True
    approval_token: str = ""
    expected_connects_cost: int = Field(default=0, ge=0, le=10000)
    screening_answers: list[str] = Field(default_factory=list, max_length=20)


class MessageWrite(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=10000)
    idempotency_key: str = Field(min_length=8, max_length=160)
    dry_run: bool = True
    approval_token: str = ""


class ToolResult(BaseModel):
    status: str
    data: dict = {}
