from llm import call_tool
from schemas import FitScore, JobRequirements, ResumeProfile, TailoredResume


def tailor_resume(resume: ResumeProfile, job: JobRequirements, fit: FitScore) -> TailoredResume:
    input_schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "bullets": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["summary", "bullets"],
    }

    system = (
        "You tailor a job candidate's resume to a specific job posting. You are given the "
        "candidate's existing summary, experience bullets, and project bullets, along with the "
        "job's required skills and a fit analysis of matched and gap skills. Rewrite the summary "
        "and select, reorder, and reword the EXISTING experience and project bullets to emphasize "
        "the skills that match the job's required skills. You must NEVER fabricate, invent, or "
        "imply any experience, tool, technology, or accomplishment that is not already present in "
        "the source resume bullets. Every bullet you output must be traceable to an existing bullet "
        "the candidate provided - you may reorder, reword, tighten, and reprioritize, but not add "
        "new facts. Do not claim skills from the gap_skills list unless they are also already "
        "present in the candidate's own bullets."
    )

    user_content = (
        f"Candidate headline: {resume.headline}\n"
        f"Current summary: {resume.summary}\n"
        f"Candidate skills: {', '.join(resume.skills)}\n"
        f"Experience bullets: {resume.experience_bullets}\n"
        f"Project bullets: {resume.project_bullets}\n"
        f"Job company: {job.company}\n"
        f"Job role title: {job.role_title}\n"
        f"Job required skills: {', '.join(job.required_skills)}\n"
        f"Fit matched skills: {', '.join(fit.matched_skills)}\n"
        f"Fit gap skills: {', '.join(fit.gap_skills)}\n"
    )

    result = call_tool(
        agent_name="resume_tailor",
        system=system,
        user_content=user_content,
        tool_name="tailor_resume",
        tool_description="Return a rewritten resume summary and a reordered/reworded list of existing bullets emphasizing skills that match the job.",
        input_schema=input_schema,
    )

    return TailoredResume(**result)
