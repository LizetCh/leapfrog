from llm import call_tool
from schemas import JobRequirements

SYSTEM_PROMPT = (
    "You extract structured job requirements from a raw job posting. "
    "Read the posting carefully and identify the company, role title, seniority level, "
    "employment type, required skills, and nice-to-have skills. "
    "Infer seniority (e.g. junior, mid, senior, staff) and employment type "
    "(e.g. full-time, part-time, contract) even if not stated explicitly, using the "
    "posting's overall tone and requirements as context."
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "role_title": {"type": "string"},
        "seniority": {"type": "string"},
        "employment_type": {"type": "string"},
        "required_skills": {"type": "array", "items": {"type": "string"}},
        "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "company",
        "role_title",
        "seniority",
        "employment_type",
        "required_skills",
    ],
}


def extract_requirements(jd_text: str) -> JobRequirements:
    result = call_tool(
        agent_name="jd_intake",
        system=SYSTEM_PROMPT,
        user_content=jd_text,
        tool_name="extract_job_requirements",
        tool_description="Record the structured job requirements extracted from the job posting.",
        input_schema=INPUT_SCHEMA,
    )
    return JobRequirements(**result)
