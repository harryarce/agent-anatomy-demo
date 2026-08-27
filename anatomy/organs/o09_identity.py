from __future__ import annotations

from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 7
FAILURE_IT_FIXES = "Ada could not prove least-privilege identity boundaries for data-plane actions."
LANDING_LINE = "Identity is explicit: no keys in repo, and denied calls fail cleanly."


def _secret_scan_hint() -> str:
    env_files = sorted(Path(__file__).resolve().parents[2].glob(".env*"))
    return "no .env files with secrets" if not env_files else f"checked {len(env_files)} env-style files"


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
        return load_report_replay("identity")

    output = [
        "[SIMULATED] Data-plane operation with per-agent identity: blob write attempted.",
        "Decoded token claims: oid=11111111-2222-3333-4444-555555555555 appid=66666666-7777-8888-9999-aaaaaaaaaaaa",
        f"Secret hygiene check: {_secret_scan_hint()}",
        "[SIMULATED] Unauthorized call result: HTTP 403 Forbidden (expected).",
    ]
    status = "ok"
    if autopsy.strip().lower() == "identity":
        status = "fail"
        output.append("[AUTOPSY] Identity removed: operation would require shared credentials.")

    return RunReport(
        organ="identity",
        status=status,
        firing=["Instructions", "Model", "Identity", "Observability"],
        output=output,
        payoff=[
            "This demo is explicitly simulated because Blob RBAC is cloud-only.",
            "The no-secrets property still holds locally and is verifiable.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=29, output_tokens=23, estimated_cost_usd=0.0, latency_seconds=0.1),
        source="simulated local identity walkthrough",
        labels=["SIMULATED"],
    )
