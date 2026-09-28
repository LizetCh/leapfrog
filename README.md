# Leapfrog — AI Job-Search Copilot

Automates the manual job-application loop (read JD → judge fit → tailor resume → draft outreach) using a provider-agnostic LLM pipeline. Built as a portfolio project to demonstrate AI engineering, not just use it.

Full architecture, design rationale, and build progress: [SPEC.md](SPEC.md).

## Current state

v1 pipeline (`orchestrator.py`): sequential function calls, no graph orchestration yet.

```
JD Intake → Fit Scorer → Resume Tailor → Email Outreach
```

v2 (in progress, see [SPEC.md](SPEC.md)) rebuilds this as a LangGraph `StateGraph` with a fit-gate, an ATS-keyword retry loop, and a concurrent cover-letter/outreach fan-out. Section progress is tracked in SPEC.md's build order checklist.

## Stack

Python 3.13, FastAPI, Pydantic, `uv`. LLM calls go through a provider-agnostic interface (`llm/base.py`'s `ToolCaller` protocol) with two implementations:

- **Gemini** (`gemini-2.5-flash`, free tier) — default, zero-cost dev/demo.
- **Anthropic** (`claude-sonnet-5`) — secondary, same interface.

Selected at runtime via `LLM_PROVIDER` env var.

## Setup

```bash
uv sync
```

Set the API key for whichever provider you use:

```bash
export GEMINI_API_KEY=...       # default provider
export ANTHROPIC_API_KEY=...    # if LLM_PROVIDER=anthropic
```

Add your resume profile at `data/resume_profile.json` (see `schemas.py`'s `ResumeProfile` for shape).

## Run

```bash
uv run uvicorn main:app --reload
```

`POST /analyze` with `{"jd_text": "..."}` against a running server, or use the interactive docs at `/docs`.

## Evals

```bash
uv run evals/run_evals.py
```

Runs the pipeline against `evals/dataset.json` and scores results with an LLM-as-judge.
