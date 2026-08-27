from __future__ import annotations

import sqlite3
from pathlib import Path

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 2
FAILURE_IT_FIXES = "Ada could not verify whether order 4471 exists or why it was delayed."
LANDING_LINE = "Tools turned a guess into a lookup, and adding a tool changed behavior without code edits."


def _tool_names(path: Path) -> list[str]:
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            names.append(stripped.split(":", 1)[1].strip())
    return names


def _order_lookup() -> str:
    db_path = Path(__file__).resolve().parents[2] / "data" / "orders.db"
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT order_id, customer, days_late, status FROM orders WHERE order_id = 4471"
        ).fetchone()
    if row is None:
        return "Order 4471 not found."
    return f"order {row[0]} customer={row[1]} days_late={row[2]} status={row[3]}"


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
    del question, record, trace, stage, kill, resume
    if replay:
        return load_report_replay("tools")

    root = Path(__file__).resolve().parents[2]
    before = _tool_names(root / "toolbox.before.yaml")
    after = _tool_names(root / "toolbox.add-tool.yaml")
    selected = after if beat == 3 else before

    output = ["Discovered tools:"]
    for item in selected:
        output.append(f"- {item}")
    output.append(f"SQLite lookup: {_order_lookup()}")
    if beat == 3:
        added = sorted(set(after) - set(before))
        output.append("Added with zero code change:")
        for item in added:
            output.append(f"+ {item}")

    if tool_search:
        all_tools_cost = 390
        selected_cost = 170
        output.append(
            f"Tool search token demo: advertised={all_tools_cost} selected={selected_cost} delta={all_tools_cost - selected_cost}"
        )

    status = "ok"
    if autopsy.strip().lower() == "tools":
        status = "fail"
        output.append("[AUTOPSY] Tools removed: order 4471 cannot be verified.")

    return RunReport(
        organ="tools",
        status=status,
        firing=["Instructions", "Model", "Knowledge", "Tools", "Observability"],
        output=output,
        payoff=[
            "Order facts came from SQLite instead of prompt memory.",
            "Beat 3 proves capability changed by toolbox config, not source code.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=78, output_tokens=64, estimated_cost_usd=0.0, latency_seconds=0.2),
        source="local toolbox and sqlite lookup",
    )