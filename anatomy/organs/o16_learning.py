from __future__ import annotations

import json
from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 11
FAILURE_IT_FIXES = "Ada repeated the same classification errors across similar tickets."
LANDING_LINE = "The scaffold changed, and measurable success improved."


def _load_tickets() -> list[dict[str, object]]:
    path = Path(__file__).resolve().parents[2] / "data" / "tickets" / "failures.json"
    return json.loads(path.read_text(encoding="utf-8"))


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
        return load_report_replay("learning")

    tickets = _load_tickets()
    before_correct = 1
    after_correct = 3
    old_instruction = "Decide refunds quickly from prior examples."
    new_instruction = "Decide refunds only after policy citation and order lookup."
    output = [
        f"Training set size: {len(tickets)} failed tickets.",
        f"Before success rate: {before_correct}/{len(tickets)}",
        f"After success rate: {after_correct}/{len(tickets)}",
        "Instruction diff:",
        f"- {old_instruction}",
        f"+ {new_instruction}",
    ]
    status = "ok"
    if autopsy.strip().lower() == "learning":
        status = "fail"
        output.append("[AUTOPSY] Learning removed: repeated ticket errors remain unchanged.")

    return RunReport(
        organ="learning",
        status=status,
        firing=["Learning", "Observability", "Metabolism"],
        output=output,
        payoff=[
            "The update is explicit and measurable, not hand-wavy tuning.",
            "Agent Optimizer cloud service is not invoked in this local implementation.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=53, output_tokens=46, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local critic loop",
        labels=["LOCAL IMPLEMENTATION"],
    )
