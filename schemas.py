"""Shared Pydantic contracts passed between pipeline agents."""
from pydantic import BaseModel, Field


class ResumeProfile(BaseModel):
    name: str
    headline: str
    summary: str
    skills: list[str]
    experience_bullets: list[str]
    project_bullets: list[str]


class JobRequirements(BaseModel):
    company: str
    role_title: str
    seniority: str
    employment_type: str
    required_skills: list[str]
    nice_to_have_skills: list[str] = Field(default_factory=list)


class FitScore(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    gap_skills: list[str]
    rationale: str


class TailoredResume(BaseModel):
    summary: str
    bullets: list[str]


class OutreachDraft(BaseModel):
    subject: str
    body: str


class PipelineResult(BaseModel):
    job: JobRequirements
    fit: FitScore
    tailored_resume: TailoredResume
    outreach: OutreachDraft
