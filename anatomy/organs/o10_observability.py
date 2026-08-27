from __future__ import annotations

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 8
FAILURE_IT_FIXES = "Actions happened without a trustworthy trace of what and when."
LANDING_LINE = "Even with no portal access, local traces prove the execution path."


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
        return load_report_replay("observability")

    output = [
        "Span tree (local console exporter):",
        "root 120ms",
        "  lookup_policy 33ms tokens=22",
        "  lookup_order 27ms tokens=18",
        "  draft_response 60ms tokens=41",
        "App Insights exporter: [WARN] not configured locally",
    ]
    status = "ok"
    removed = autopsy.strip().lower()
    if removed == "knowledge":
        output.remove("  lookup_policy 33ms tokens=22")
        output.insert(2, "  policy_lookup SKIPPED (Knowledge removed)")
        output.insert(3, "  draft_response UNGROUNDED")
    elif removed == "observability":
        status = "fail"
        output = ["[AUTOPSY] Observability removed: no trace evidence for postmortem."]

    return RunReport(
        organ="observability",
        status=status,
        firing=["Observability", "Metabolism"],
        output=output,
        payoff=[
            "The span tree is deterministic and stage-safe.",
            "Cloud export is optional and honestly marked as a warning when absent.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=26, output_tokens=17, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local trace renderer",
        labels=["LOCAL IMPLEMENTATION"],
    )
