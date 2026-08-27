from __future__ import annotations

from datetime import datetime
from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 12
FAILURE_IT_FIXES = "Ada required a human prompt and could not react to external events."
LANDING_LINE = "Nobody typed anything, and Ada still woke up and acted."


def _latest_synced_file() -> Path | None:
    synced_folder = Path(__file__).resolve().parents[2] / "onedrive"
    synced_folder.mkdir(parents=True, exist_ok=True)
    files = sorted(
        (item for item in synced_folder.glob("*") if item.is_file() and item.name != "result.txt"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


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
        return load_report_replay("reflex_arc")

    woke_at = datetime.now().strftime("%H:%M:%S")
    latest = _latest_synced_file()
    output = [f"woke at {woke_at} - nobody typed anything"]
    if latest is None:
        status = "fail"
        output.append("No drop event found; add a PDF or CSV to onedrive/ and run again.")
    else:
        event = latest.read_text(encoding="utf-8").strip()
        result_path = latest.parent / "result.txt"
        result_path.write_text(
            f"Processed {latest.name}\nEvent: {event}\nDecision: escalate order 4471 for policy review.\n",
            encoding="utf-8",
        )
        status = "ok"
        output.extend(
            [
                f"Drop trigger observed: {latest.name}",
                f"Event payload: {event}",
                "Result written to onedrive/result.txt",
            ]
        )
    output.append("Timer variant: schedule 'python -m anatomy demo reflex' for unattended polling.")
    if autopsy.strip().lower() == "reflex arc":
        status = "fail"
        output.append("[AUTOPSY] Reflex arc removed: no autonomous activation occurs.")

    return RunReport(
        organ="reflex_arc",
        status=status,
        firing=["Reflex Arc", "Tools", "Observability"],
        output=output,
        payoff=[
            "Activation is event-driven from the local filesystem.",
            "This is a local analog of a OneDrive or SharePoint file-created event handled by Logic Apps or Power Automate.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=19, output_tokens=21, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="local filesystem trigger",
        labels=["LOCAL IMPLEMENTATION"],
    )
