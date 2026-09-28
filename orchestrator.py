from agents.fit_scorer import score_fit
from agents.jd_intake import extract_requirements
from agents.outreach_drafter import draft_outreach
from agents.resume_tailor import tailor_resume
from schemas import PipelineResult, ResumeProfile


def run_pipeline(jd_text: str, resume: ResumeProfile) -> PipelineResult:
    job = extract_requirements(jd_text)
    fit = score_fit(job, resume)
    tailored = tailor_resume(resume, job, fit)
    outreach = draft_outreach(job, tailored, resume.name)
    return PipelineResult(job=job, fit=fit, tailored_resume=tailored, outreach=outreach)
