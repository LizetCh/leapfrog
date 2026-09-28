import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm import call_tool
from orchestrator import run_pipeline
from schemas import PipelineResult, ResumeProfile

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "no_fabrication": {
            "type": "boolean",
            "description": "True if the tailored resume only reframes existing bullets and invents no new experience, tools, or accomplishments.",
        },
        "outreach_grounded": {
            "type": "boolean",
            "description": "True if the outreach message references at least one concrete requirement from the job posting rather than generic boilerplate.",
        },
        "notes": {"type": "string"},
    },
    "required": ["no_fabrication", "outreach_grounded", "notes"],
}


def judge_pipeline_result(jd_text: str, resume: ResumeProfile, result: PipelineResult) -> dict:
    user_content = (
        f"Original job posting:\n{jd_text}\n\n"
        f"Candidate's real resume:\n{resume.model_dump_json(indent=2)}\n\n"
        f"Pipeline's tailored resume:\n{result.tailored_resume.model_dump_json(indent=2)}\n\n"
        f"Pipeline's outreach draft:\n{result.outreach.model_dump_json(indent=2)}"
    )
    return call_tool(
        agent_name="eval_judge",
        system=(
            "You are a strict QA judge for an AI job-search pipeline. Check whether the tailored "
            "resume fabricates anything not present in the candidate's real resume, and whether the "
            "outreach message is grounded in specific job details rather than generic boilerplate."
        ),
        user_content=user_content,
        tool_name="judge_pipeline_result",
        tool_description="Report whether the pipeline output passes the no-fabrication and grounded-outreach checks.",
        input_schema=JUDGE_SCHEMA,
    )


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    with open(base_dir / "data" / "resume_profile.json") as f:
        resume = ResumeProfile(**json.load(f))
    with open(Path(__file__).resolve().parent / "dataset.json") as f:
        cases = json.load(f)

    passed = 0
    for case in cases:
        result = run_pipeline(case["jd_text"], resume)
        low, high = case["expected_fit_range"]
        score_ok = low <= result.fit.score <= high
        judgement = judge_pipeline_result(case["jd_text"], resume, result)
        case_passed = score_ok and judgement["no_fabrication"] and judgement["outreach_grounded"]
        passed += case_passed

        status = "PASS" if case_passed else "FAIL"
        print(f"[{status}] {case['id']}: fit={result.fit.score} (expected {low}-{high}), "
              f"no_fabrication={judgement['no_fabrication']}, outreach_grounded={judgement['outreach_grounded']}")
        if not case_passed:
            print(f"  judge notes: {judgement['notes']}")

    print(f"\n{passed}/{len(cases)} cases passed")


if __name__ == "__main__":
    main()
