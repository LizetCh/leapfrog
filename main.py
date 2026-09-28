import json
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator import run_pipeline
from schemas import PipelineResult, ResumeProfile

app = FastAPI(title="Leapfrog", description="AI job-search copilot pipeline")


class AnalyzeRequest(BaseModel):
    jd_text: str


@lru_cache
def _resume_profile() -> ResumeProfile:
    with open("data/resume_profile.json") as f:
        return ResumeProfile(**json.load(f))


@app.post("/analyze", response_model=PipelineResult)
def analyze(request: AnalyzeRequest) -> PipelineResult:
    try:
        return run_pipeline(request.jd_text, _resume_profile())
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
