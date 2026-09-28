# Leapfrog — AI Job-Search Copilot

## Problem

Landing an AI Engineer role fast, using AI engineering itself as the mechanism. Applying to a job posting manually (read JD, judge fit, tailor resume, write outreach) is slow and repeated N times per week. This automates that pipeline while doubling as the portfolio project that proves the skill.

## Priority (revised 2026-09-26)

Depth of understanding over speed. Built teaching-paced: every concept explained before/while coding, built together not delegated. No fixed deadline — ships when it's genuinely defensible in an interview, not by a date.

## Scope (v2)

Graph-based pipeline (LangGraph), typed state, one FastAPI endpoint, provider-agnostic LLM layer (demoed on Gemini's free tier).

```
START
  │
  ▼
[JD Intake] ──▶ JobRequirements
  │
  ▼
[Fit Scorer] ──▶ FitScore
  │
  ▼
 <fit.score >= FIT_THRESHOLD?>──NO──▶ END (low-fit report only)
  │ YES
  ▼
[Resume Tailor] ──▶ TailoredResume
  │
  ▼
[ATS Keyword Check] (deterministic, no LLM call) ──▶ ats_score
  │
  ▼
 <ats_score >= ATS_THRESHOLD or retries exhausted?>──NO──▶ back to [Resume Tailor] with feedback
  │ YES (uses best-scoring attempt across all retries, not just the last one)
  ▼
  ┌─────────────┴─────────────┐
  ▼                           ▼
[Cover Letter]          [Email Outreach]     ← run concurrently, no data dependency between them
CoverLetterDraft         OutreachDraft
  └─────────────┬─────────────┘
                ▼
     [Render Markdown] (deterministic) ──▶ resume.md, cover_letter.md
                │
                ▼
               END
```

Every arrow is a typed field on one shared `PipelineState`, not free text — LangGraph nodes read/write that state.

### Nodes

0. **Resume Intake** — your resume as free-text Markdown (`data/resume_master.md`, human-edited) → `ResumeProfile`. Same structured-extraction pattern as JD Intake, reused rather than reinvented — you maintain one plain-text file instead of hand-editing JSON. Runs once per pipeline invocation (or could be cached — see Section 1c questions).
1. **JD Intake** — raw job posting text → `JobRequirements`.
2. **Fit Scorer** — `JobRequirements` + `ResumeProfile` → `FitScore` (score 0-100, matched_skills, gap_skills, rationale). System prompt forbids inflating the score.
3. **Fit gate (conditional edge)** — routes to `END` if `fit.score < FIT_THRESHOLD` (default 70, configurable). Below threshold, no resume/cover-letter/outreach is generated — saves API calls on jobs that aren't worth tailoring for. The response is never silently empty on this path: `job` and `fit` (including `rationale` and `gap_skills`) are always returned, so the caller sees exactly why tailoring was skipped.
4. **Resume Tailor** — `ResumeProfile` + `JobRequirements` + `FitScore` (+ ATS feedback on retry) → `TailoredResume`. Never invents experience — only reorders/rewords existing bullets. On a retry (see ATS gate below), the prompt also receives which required-skill keywords are still missing, and is told to paraphrase toward them without inventing anything.
5. **ATS Keyword Check** — deterministic Python, no LLM call. Computes what fraction of `job.required_skills` appear (case-insensitive, simple substring/token match) in `tailored_resume.summary` + `bullets`. Returns `ats_score` (0-100) + list of still-missing keywords. Why deterministic: real ATS parsers mostly do literal keyword matching — an LLM call here would be slower, costlier, and less faithful to what's being simulated.
6. **ATS gate (conditional edge)** — if `ats_score < ATS_THRESHOLD` (default 60) and retries remain (cap at 2), loops back to Resume Tailor with the missing-keyword list. Otherwise proceeds. This is also the first LangGraph **loop** in the graph — worth understanding State accumulation (`retry_count`) to avoid an infinite cycle. State tracks `best_ats_score` + `best_tailored_resume` across every attempt (not just the last); whichever attempt scored highest is what proceeds downstream, even if a later retry regressed. Final `ats_score` and any still-missing keywords are always surfaced in the output — never a silent gap.
7. **Cover Letter** — `ResumeProfile` + `JobRequirements` + `TailoredResume` (the best-scoring one) → `CoverLetterDraft` (subject, body). Longer, formal document — distinct from the short cold-outreach email. Same no-fabrication constraint as Resume Tailor.
8. **Email Outreach** — `JobRequirements` + `TailoredResume` summary → `OutreachDraft` (subject, body). Short cold message to a recruiter/team member, references 1-2 concrete JD requirements, no boilerplate.

   **Cover Letter and Email Outreach run concurrently** — both depend only on the finalized `TailoredResume` + `JobRequirements`, not on each other, so there's no reason to serialize them. Implemented as a LangGraph fan-out: one node's outgoing edges point to both, an async node function each (`ainvoke`), state merges both results once both complete before continuing. **Alternative considered:** keep them sequential (simpler mental model, no async) — rejected once the independence was noticed, since parallelizing here is low-risk (no shared mutable state between the two) and directly demonstrates async LangGraph usage.
9. **Render Markdown** — deterministic Python, no LLM call, runs after both parallel branches join. Writes `TailoredResume` and `CoverLetterDraft` to `.md` files (returned inline via the API, not written to disk in the deployed service — local CLI/dev usage can write to disk).

### Cross-cutting

- **Observability**: every LLM call logs `{agent_name, latency_ms, input_tokens, output_tokens, estimated_cost_usd}` as structured JSON. Pricing table lives in a small config file (not a hardcoded Python constant), with a "last verified" date.
- **Evals**: `evals/dataset.json` — 8-10 real job postings spanning strong/weak fit. `evals/run_evals.py` runs the full graph on each, then an LLM-as-judge call scores: fit-score accuracy against an expected range, no-fabrication in resume/cover letter, outreach groundedness, and (new) whether the fit gate correctly skipped tailoring on low-fit cases.
- **API**: FastAPI, single `POST /analyze` endpoint. Pydantic request/response validation. HTTP error handling + exponential backoff on LLM calls.
- **Provider-agnostic LLM layer**: agents call through a small interface (`ToolCaller` protocol: same `call_tool(...)` shape as before), not a concrete SDK. Two implementations: `AnthropicToolCaller` (current), `GeminiToolCaller` (new, using Gemini's free tier for zero-cost development/demo). Selected via env var. This is real added complexity, taken on deliberately so the project runs at zero cost while still supporting Claude for production-shaped discussion in interviews.

### Explicitly out of scope for v2

- No vector DB / RAG.
- No Docker (Railway deploys directly from repo).
- No frontend — FastAPI `/docs` is the demo surface.
- No multi-JD batch processing, no auth/multi-user — personal tool first.
- No live pricing API lookup — config file with a manually verified date is enough for an advisory cost estimate.

## Stack

Python, FastAPI, Pydantic, `uv`, LangGraph (orchestration), Gemini API (`google-genai`, free tier, primary demo provider) + Anthropic Claude API (secondary, via the same interface), deployed to Railway.

## Repo layout

```
leapfrog/
  SPEC.md
  README.md
  pyproject.toml
  main.py                    # FastAPI app, /analyze endpoint
  graph.py                   # LangGraph StateGraph: nodes + edges + conditional routing
  state.py                   # PipelineState (shared graph state)
  schemas.py                 # Pydantic models for each node's structured output
  llm/
    base.py                  # ToolCaller protocol
    anthropic_client.py
    gemini_client.py
    pricing.json              # per-model $/1K tokens, "last verified" date
  agents/
    jd_intake.py
    fit_scorer.py
    resume_tailor.py
    ats_check.py               # deterministic, no LLM call
    cover_letter.py
    email_outreach.py
    render_markdown.py         # deterministic, no LLM call
  data/
    resume_profile.json
  evals/
    dataset.json
    run_evals.py
```

## Success criteria

- `POST /analyze` with a real job posting returns a complete, valid pipeline result.
- Low-fit postings correctly short-circuit before resume/cover-letter/outreach generation.
- `evals/run_evals.py` runs clean with a printed pass rate.
- Runs at zero cost on Gemini's free tier; Claude path also functional if `LLM_PROVIDER=anthropic`.
- Deployed on Railway, reachable via `/docs`.
- You can explain every node, every edge, and every design decision without notes.

## Build order (iterative sections)

Each section: built together, then explained (what/why), then likely recruiter/interview questions on it. Check off as completed.

- [x] **Section 1 — Shared contracts (v1)**: `schemas.py` (5 core models), original `llm.py` (Anthropic-only). Superseded by Section 1b below but concepts carry over.
- [x] **Section 1b — Provider-agnostic LLM layer**: `llm/base.py` (protocol), `llm/anthropic_client.py`, `llm/gemini_client.py`, `llm/pricing.json`.
- [ ] **Section 1c — LangGraph fundamentals + `state.py`**: State design, before touching the graph itself.
- [ ] **Section 2 — Graph skeleton**: `graph.py` with JD Intake → Fit Scorer → fit gate, using existing agent logic as nodes.
- [ ] **Section 3 — Resume Tailor + ATS check + retry loop**: the graph's first loop.
- [ ] **Section 4 — Cover Letter node** (new).
- [ ] **Section 5 — Email Outreach node** (renamed from Outreach Drafter, logic unchanged).
- [ ] **Section 6 — Render Markdown node** (deterministic).
- [ ] **Section 7 — FastAPI wiring**: `main.py` calling the compiled graph.
- [ ] **Section 8 — Eval harness** updated for the graph + fit-gate behavior.
- [ ] **Section 9 — Deploy + README**.
