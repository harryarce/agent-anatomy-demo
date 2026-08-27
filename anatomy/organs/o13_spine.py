from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 10
FAILURE_IT_FIXES = "A process crash risked replaying already-completed refund steps."
LANDING_LINE = "Resume continued from checkpoint without re-running completed steps."

CHECKPOINT_PATH = Path(".anatomy-spine-checkpoint.json")


@dataclass(slots=True)
class Step:
    name: str
    done: bool
    timestamp: str


def _initial_steps() -> list[Step]:
    return [
        Step("validate_order", False, ""),
        Step("apply_policy", False, ""),
        Step("create_refund_draft", False, ""),
        Step("queue_finance_action", False, ""),
    ]


def _load_checkpoint() -> list[Step]:
    if not CHECKPOINT_PATH.exists():
        return _initial_steps()
    payload = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    return [Step(**item) for item in payload.get("steps", [])]


def _save_checkpoint(steps: list[Step]) -> None:
    payload = {"steps": [asdict(step) for step in steps]}
    CHECKPOINT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
    del question, record, trace, stage, beat, tool_search
    if replay:
        return load_report_replay("spine")

    steps = _load_checkpoint() if resume else _initial_steps()
    output = []
    for index, step in enumerate(steps):
        if step.done:
            output.append(f"SKIP {step.name} (already done at {step.timestamp})")
            continue
        step.done = True
        step.timestamp = datetime.now().isoformat(timespec="seconds")
        output.append(f"RUN  {step.name} at {step.timestamp}")
        _save_checkpoint(steps)
        if kill and index == 1:
            output.append("PROCESS TERMINATED intentionally after deterministic checkpoint boundary.")
            output.append("Lost: in-flight work after checkpoint boundary. Survived: completed step timestamps.")
            return RunReport(
                organ="spine",
                status="fail",
                firing=["Spine", "Orchestration", "Observability"],
                output=output,
                payoff=[
                    "Checkpoint file persisted completed supersteps before termination.",
                    "Resume will continue without re-running completed steps.",
                ],
                landing_line=LANDING_LINE,
                usage=Usage(input_tokens=14, output_tokens=29, estimated_cost_usd=0.0, latency_seconds=0.1),
                source="local checkpoint storage",
                labels=["LOCAL IMPLEMENTATION"],
            )

    if autopsy.strip().lower() == "spine":
        output.append("[AUTOPSY] Spine removed: restart would replay already completed steps.")
        status = "fail"
    else:
        status = "ok"

    return RunReport(
        organ="spine",
        status=status,
        firing=["Spine", "Orchestration", "Observability"],
        output=output,
        payoff=[
            "Completed step timestamps prove resume did not re-execute prior work.",
            "Checkpoint semantics are local and deterministic for wifi-safe demos.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=16, output_tokens=32, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local checkpoint storage",
        labels=["LOCAL IMPLEMENTATION"],
    )
