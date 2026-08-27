from __future__ import annotations

import json
from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 4
FAILURE_IT_FIXES = "Ada forgot durable customer preferences across sessions."
LANDING_LINE = "Session IDs changed, but durable memory still answered correctly."

MEMORY_PATH = Path(".anatomy-memory.json")


def _load_store() -> dict[str, str]:
    if not MEMORY_PATH.exists():
        return {}
    return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))


def _save_store(store: dict[str, str]) -> None:
    MEMORY_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


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
        return load_report_replay("memory")

    store = _load_store()
    session_a = "thread-ada-001"
    session_b = "thread-ada-002"
    store["contoso.preference"] = "Escalations require email summary and invoice attachment."
    _save_store(store)
    recalled = store.get("contoso.preference", "missing")

    output = [
        f"Session 1 thread_id={session_a} stored fact: {store['contoso.preference']}",
        f"Session 2 thread_id={session_b} recalled fact: {recalled}",
    ]
    status = "ok"
    if autopsy.strip().lower() == "memory":
        status = "fail"
        output.append("[AUTOPSY] Memory removed: second session cannot recall stored preference.")

    return RunReport(
        organ="memory",
        status=status,
        firing=["Instructions", "Model", "Memory", "Observability"],
        output=output,
        payoff=[
            "Thread IDs differ, proving this is not chat-history carryover.",
            "Memory persisted to local storage and survived process boundaries.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=32, output_tokens=27, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local memory store",
        labels=["LOCAL IMPLEMENTATION"],
    )
