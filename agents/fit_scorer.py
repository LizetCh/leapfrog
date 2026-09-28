import llm
from schemas import FitScore, JobRequirements, ResumeProfile

SYSTEM_PROMPT = (
    "You are a strict technical recruiter comparing a candidate's resume against a job's "
    "requirements. Score fit honestly on a 0-100 scale based only on evidence in the resume. "
    "Do not inflate the score to be encouraging — the purpose of this tool is honest gap "
    "analysis, not flattery. List skills the resume actually demonstrates as matched_skills, "
    "and required or nice-to-have skills the resume does not demonstrate as gap_skills."
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Overall fit score from 0 (no fit) to 100 (perfect fit).",
        },
        "matched_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills required or nice-to-have by the job that the resume demonstrates.",
        },
        "gap_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills required or nice-to-have by the job that the resume does not demonstrate.",
        },
        "rationale": {
            "type": "string",
            "description": "Brief, honest explanation of the score, including notable gaps.",
        },
    },
    "required": ["score", "matched_skills", "gap_skills", "rationale"],
}


def score_fit(job: JobRequirements, resume: ResumeProfile) -> FitScore:
    user_content = (
        f"Job requirements:\n{job.model_dump_json(indent=2)}\n\n"
        f"Candidate resume:\n{resume.model_dump_json(indent=2)}"
    )
    result = llm.call_tool(
        agent_name="fit_scorer",
        system=SYSTEM_PROMPT,
        user_content=user_content,
        tool_name="score_fit",
        tool_description="Report an honest fit score between a candidate's resume and a job's requirements.",
        input_schema=INPUT_SCHEMA,
    )
    return FitScore(**result)
