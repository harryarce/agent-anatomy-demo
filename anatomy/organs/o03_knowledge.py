from __future__ import annotations

from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 1
FAILURE_IT_FIXES = "Ada made policy claims with no citation and no grounding."
LANDING_LINE = "Grounding replaced confidence theater with verifiable evidence."


def _policy_clause() -> str:
    policy = Path(__file__).resolve().parents[2] / "data" / "refund-policy.txt"
    for line in policy.read_text(encoding="utf-8").splitlines():
        if line.startswith("Section 4.2"):
            return line.strip()
    return "Section 4.2 not found."


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
        return load_report_replay("knowledge")

    grounded = _policy_clause()
    output = [
        "Ungrounded answer: 'Section 4.2 allows full refunds for every late shipment.'",
        "Grounded answer with citation:",
        grounded,
        "Citation: data/refund-policy.txt#Section 4.2",
    ]
    status = "ok"
    if autopsy.strip().lower() == "knowledge":
        status = "fail"
        output.append("[AUTOPSY] Knowledge removed: no citation available; answer regresses to guesswork.")

    return RunReport(
        organ="knowledge",
        status=status,
        firing=["Instructions", "Model", "Knowledge", "Observability"],
        output=output,
        payoff=[
            "Policy claims are now checkable against local files.",
            "The room can verify the exact clause instead of trusting Ada's confidence.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=41, output_tokens=55, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local file grounding",
    )