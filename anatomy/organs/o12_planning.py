from __future__ import annotations

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 13
FAILURE_IT_FIXES = "Ada woke from the reflex arc but had no structured approach to the escalation."
LANDING_LINE = "Planning decomposed reactive autonomy into measurable, auditable sub-goals."


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
        return load_report_replay("planning")

    output = [
        "Goal decomposition for escalation (Contoso order 4471):",
        "",
        "GOAL: Approve or deny refund",
        "├── SUBGOAL 1: Verify order metadata",
        "│   ├── Fetch order 4471 from database",
        "│   └── Confirm customer = Contoso",
        "├── SUBGOAL 2: Check refund policy applicability",
        "│   ├── Load refund-policy.txt",
        "│   ├── Extract Section 4.2 (delay thresholds)",
        "│   └── Compute days_late vs. threshold",
        "├── SUBGOAL 3: Reach decision with evidence",
        "│   ├── If days_late >= threshold: approve",
        "│   └── Else: deny with policy citation",
        "└── SUBGOAL 4: Prepare auditable response",
        "    ├── Include order_id, customer, policy ref",
        "    └── Timestamp and trace for observability",
        "",
        "Plan validation (before execution):",
        "  READY Subgoal 1: no dependencies",
        "  READY Subgoal 2: no dependencies; may run with Subgoal 1",
        "  WAIT  Subgoal 3: requires Subgoals 1 and 2",
        "  WAIT  Subgoal 4: requires Subgoal 3",
    ]
    status = "ok"
    if autopsy.strip().lower() == "planning":
        status = "fail"
        output.append("[AUTOPSY] Planning removed: escalation handled as monolithic single step; no visibility into decision boundaries.")

    return RunReport(
        organ="planning",
        status=status,
        firing=["Instructions", "Model", "Knowledge", "Tools", "Planning", "Observability"],
        output=output,
        payoff=[
            "Event-driven autonomy (reflex arc) now has a visible roadmap.",
            "Each subgoal is checkable and has explicit dependencies before execution.",
            "The plan separates deciding what to do from orchestrating the work.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=124, output_tokens=89, estimated_cost_usd=0.0, latency_seconds=0.15),
        source="local goal decomposition engine",
        labels=["LOCAL IMPLEMENTATION"],
    )
