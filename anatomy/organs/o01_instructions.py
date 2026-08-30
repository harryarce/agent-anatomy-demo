from __future__ import annotations

from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 0
FAILURE_IT_FIXES = "Without explicit instructions, Ada drifts in tone and overstates certainty."
LANDING_LINE = "The model is the same; instructions changed behavior immediately."


def _persona_text(name: str) -> str:
    path = Path(__file__).resolve().parents[2] / "data" / "instructions" / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def _response(name: str) -> str:
    if name == "terse_expert":
        return "Approve only after evidence. Do not issue refund until order and policy are verified."
    if name == "patient_teacher":
        return "Step 1: confirm order 4471 and delivery timeline. Step 2: cite policy clause before deciding."
    return "Current evidence is insufficient. Any confident refund claim is a process defect."


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
        return load_report_replay("instructions")

    personas = ["terse_expert", "patient_teacher", "hostile_reviewer"]
    output = ["Demo setup: the application team owns Ada's instruction profiles; the model does not invent them."]
    for persona in personas:
        profile = persona.replace("_", " ")
        output.append(f"Application team configures '{profile}': '{_persona_text(persona)}'")
        output.append(f"Ada follows '{profile}': {_response(persona)}")
    output.append(
        "Demo setup: intentionally fabricated failure example for Knowledge next: "
        "'Section 4.2 guarantees full refunds for any delay.'"
    )

    status = "ok"
    if autopsy.strip().lower() == "instructions":
        status = "fail"
        output.append("[AUTOPSY] Instructions removed: tone and certainty become inconsistent.")

    return RunReport(
        organ="instructions",
        status=status,
        firing=["Instructions", "Model"],
        output=output,
        payoff=[
            "The application team supplied the three profiles from separate instruction files.",
            "The visible fabricated policy claim creates the failure that Knowledge fixes next.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=58, output_tokens=72, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local deterministic instruction variant demo",
    )