from __future__ import annotations

from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 11
FAILURE_IT_FIXES = "Ada lacked reusable house rules and repeated formatting errors."
LANDING_LINE = "Skills are scaffolding on demand: advertise cheap, load when needed."


async def run(
    *,
    question: str,
    replay: bool,
    record: bool,
    trace: bool,
    stage: bool,
    autopsy: str,
    beat: int | None,
    kill: bool,
    resume: bool,
    tool_search: bool,
) -> RunReport:
    del question, record, trace, stage, beat, kill, resume, tool_search
    if replay:
        return load_report_replay("skills")

    skills_dir = Path(__file__).resolve().parents[2] / "skills"
    skills = sorted(path.parent.name for path in skills_dir.glob("*/SKILL.md"))
    advertise_tokens = 210
    load_tokens = 122
    output = ["Advertised skills:"]
    for skill in skills:
        output.append(f"- {skill}")
    output.append(f"Progressive disclosure cost: advertise={advertise_tokens} load={load_tokens}")

    status = "ok"
    if autopsy.strip().lower() == "skills":
        status = "fail"
        output.append("[AUTOPSY] Skills removed: output regresses to inconsistent style and missing checklist.")

    return RunReport(
        organ="skills",
        status=status,
        firing=["Instructions", "Model", "Skills", "Observability"],
        output=output,
        payoff=[
            "The skills are discoverable before they are loaded.",
            "Loading on demand lowers token overhead for routine turns.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=advertise_tokens, output_tokens=load_tokens, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local skill catalog",
        labels=["LOCAL IMPLEMENTATION"],
    )