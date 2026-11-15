from typing import Literal

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=12, max_length=128)


class Profile(BaseModel):
    persona: Literal["ml", "web", "data", "own"] = "ml"
    hourly_rate: float = Field(default=45, ge=1, le=10000)
    minimum_project_budget: float = Field(default=200, ge=1, le=1000000)
    weekly_connects_budget: int = Field(default=100, ge=0, le=10000)
    saved_search: str = Field(default="Python", max_length=500)
    autonomy: Literal["review", "auto_skip"] = "review"


class DraftEdit(BaseModel):
    text: str = Field(min_length=10, max_length=10000)


class OutcomeInput(BaseModel):
    category: str
    outcome: Literal["won", "replied", "ignored", "hired", "lost"]


class RunResponse(BaseModel):
    id: str
    job_id: str
    kind: str
    status: str
    state: dict
    error: str
    created: str


class AuthResponse(BaseModel):
    id: str
    email: str
    profile: dict


class JobListResponse(BaseModel):
    jobs: list[dict]
    marketplace: str
    provenance_notice: str


class GithubInput(BaseModel):
    owner: str = Field(pattern=r"^[A-Za-z0-9-]+$")
    repo: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    path: str = Field(default="README.md", max_length=500)


class CalendarHold(BaseModel):
    start: str
    end: str
    title: str = Field(default="Tentative client interview", min_length=1, max_length=150)
    confirmed: bool = False


class EmailDraft(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    confirmed: bool = False


class ReplayRequest(BaseModel):
    checkpoint_id: str = Field(min_length=1, max_length=200)
    stage: Literal["analysis", "pricing", "writer", "verifier", "critic", "compliance_guard"] = "analysis"
