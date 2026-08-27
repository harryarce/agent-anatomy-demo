from __future__ import annotations

from anatomy.budget import BudgetCapExceeded, BudgetMeter
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 9
FAILURE_IT_FIXES = "Ada could loop on expensive operations with no hard stop."
LANDING_LINE = "Budget policy stopped the run before spend escaped control."


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
        return load_report_replay("metabolism")

    meter = BudgetMeter(token_cap=240, usd_cap=0.020)
    output = []
    status = "ok"
    for idx, charge in enumerate((80, 90, 120), start=1):
        try:
            meter.add(input_tokens=charge // 2, output_tokens=charge // 2, estimated_cost_usd=0.006)
            output.append(f"step {idx}: spend={meter.input_tokens + meter.output_tokens} tokens ${meter.estimated_cost_usd:.4f}")
        except BudgetCapExceeded as exc:
            output.append(f"BUDGET STOP: {exc}")
            break

    if autopsy.strip().lower() == "metabolism":
        status = "fail"
        output.append("[AUTOPSY] Metabolism removed: no spend cap enforcement applied.")

    return RunReport(
        organ="metabolism",
        status=status,
        firing=["Metabolism", "Observability"],
        output=output,
        payoff=[
            "A hard cap is enforced in-process and visible in the transcript.",
            "The run terminates deterministically at the same budget boundary.",
        ],
        landing_line=LANDING_LINE,
        usage=meter.snapshot(latency_seconds=0.1),
        source="local budget meter",
        labels=["LOCAL IMPLEMENTATION"],
    )
