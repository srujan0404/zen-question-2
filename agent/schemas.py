from typing import Literal, Any
from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    thought: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    action_input: dict[str, Any] = Field(default_factory=dict)


class CriticIssue(BaseModel):
    axis: Literal["arithmetic", "logical", "grounding"]
    detail: str


class CriticVerdict(BaseModel):
    verdict: Literal["APPROVE", "REJECT"]
    issues: list[CriticIssue] = Field(default_factory=list)
    hint: str | None = None


class FinishStep(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
