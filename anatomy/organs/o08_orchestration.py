from __future__ import annotations

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 6
FAILURE_IT_FIXES = "A single-agent pass mixed research, decisioning, and tone in one brittle step."
LANDING_LINE = "Workflow separation made each handoff visible and auditable."


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
        return load_report_replay("orchestration")

    output = [
        "Workflow graph:",
        "researcher -> writer -> reviewer",
        "reviewer --(needs citation)--> writer",
        "Node researcher: found order delay evidence and policy clause.",
        "Node writer: drafted response with refund recommendation.",
        "Node reviewer: approved after citation check.",
    ]
    status = "ok"
    if autopsy.strip().lower() == "orchestration":
        status = "fail"
        output.append("[AUTOPSY] Orchestration removed: single pass omits reviewer gate.")

    return RunReport(
        organ="orchestration",
        status=status,
        firing=["Instructions", "Model", "Knowledge", "Tools", "Orchestration", "Observability"],
        output=output,
        payoff=[
            "Each node had one job and exposed a visible decision boundary.",
            "Conditional routing prevented an uncited response from shipping.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=66, output_tokens=52, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local workflow simulation",
        labels=["LOCAL IMPLEMENTATION"],
    )
