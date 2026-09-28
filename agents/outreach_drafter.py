from llm import call_tool
from schemas import JobRequirements, OutreachDraft, TailoredResume


def draft_outreach(job: JobRequirements, tailored: TailoredResume, candidate_name: str) -> OutreachDraft:
    input_schema = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["subject", "body"],
    }

    system = (
        "You write short, specific cold outreach messages for a job candidate reaching out to a "
        "recruiter or team member at a company. The message must reference 1-2 concrete items from "
        "the job's required skills or its role title, mention the candidate by name, and be grounded "
        "in the candidate's tailored resume summary. Never use generic flattery or boilerplate openers "
        "like 'I am writing to express my interest'. Keep it brief and human."
    )

    user_content = (
        f"Candidate name: {candidate_name}\n"
        f"Company: {job.company}\n"
        f"Role title: {job.role_title}\n"
        f"Seniority: {job.seniority}\n"
        f"Employment type: {job.employment_type}\n"
        f"Required skills: {', '.join(job.required_skills)}\n"
        f"Nice to have skills: {', '.join(job.nice_to_have_skills)}\n"
        f"Tailored resume summary: {tailored.summary}\n"
        f"Tailored resume bullets: {', '.join(tailored.bullets)}\n"
    )

    result = call_tool(
        agent_name="outreach_drafter",
        system=system,
        user_content=user_content,
        tool_name="draft_outreach",
        tool_description="Draft a short, specific cold outreach subject and body for this candidate and job.",
        input_schema=input_schema,
    )

    return OutreachDraft(**result)
