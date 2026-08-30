from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay

STORY_BEAT = 14
FAILURE_IT_FIXES = "Ada could not maintain or update her world model; facts learned in one context had no impact on future decisions."
LANDING_LINE = "Belief updates cascaded through the decision engine, improving future accuracy."

BELIEFS_PATH = Path(".anatomy-beliefs.json")


def _load_beliefs() -> dict[str, Any]:
    if not BELIEFS_PATH.exists():
        return _default_beliefs()
    return json.loads(BELIEFS_PATH.read_text(encoding="utf-8"))


def _default_beliefs() -> dict[str, Any]:
    return {
        "customer_tiers": {
            "Contoso": "standard",
            "Tailspin Toys": "premium",
            "Fabrikam": "standard",
        },
        "policy_thresholds": {
            "standard_tier_days_late_refund_threshold": 5,
            "premium_tier_days_late_refund_threshold": 7,
            "executive_escalation_threshold": 30,
        },
        "customer_decision_thresholds": {
            "Contoso_auto_approve_days_late": 5,
        },
        "learned_patterns": {
            "Contoso_refund_approval_rate": 0.72,
            "recent_policy_disputes": 3,
        }
    }


def _save_beliefs(beliefs: dict[str, Any]) -> None:
    BELIEFS_PATH.write_text(json.dumps(beliefs, indent=2), encoding="utf-8")


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
        return load_report_replay("beliefs")

    beliefs = _load_beliefs()
    old_rate = beliefs["learned_patterns"]["Contoso_refund_approval_rate"]
    old_disputes = beliefs["learned_patterns"]["recent_policy_disputes"]
    old_tier = beliefs["customer_tiers"]["Contoso"]
    old_threshold = beliefs.get("customer_decision_thresholds", {}).get(
        "Contoso_auto_approve_days_late", 5
    )
    new_rate = 0.75
    new_disputes = 2
    new_tier = "standard-trusted"
    new_threshold = 4

    output = [
        "World state (beliefs) before learning:",
        json.dumps(beliefs, indent=2),
        "",
        "New evidence from recent interaction:",
        "- Contoso escalation 4471 resolved with policy citation",
        "- Customer accepted decision without legal challenge",
        "- 48-hour follow-up: customer satisfaction score = 8/10",
        "",
        "Belief update:",
        f"  learned_patterns.Contoso_refund_approval_rate: {old_rate} -> {new_rate}",
        f"  learned_patterns.recent_policy_disputes: {old_disputes} -> {new_disputes}",
        f"  customer_tiers.Contoso: '{old_tier}' -> '{new_tier}'",
        f"  customer_decision_thresholds.Contoso_auto_approve_days_late: {old_threshold} -> {new_threshold}",
        "",
        "Downstream impact on NEXT escalation:",
        f"  IF customer = Contoso AND days_late >= {new_threshold} (was >= {old_threshold}):",
        "      THEN auto-approve (was: require-review)",
        "      CONFIDENCE increased from 0.68 -> 0.78",
    ]

    beliefs["learned_patterns"]["Contoso_refund_approval_rate"] = new_rate
    beliefs["learned_patterns"]["recent_policy_disputes"] = new_disputes
    beliefs["customer_tiers"]["Contoso"] = new_tier
    beliefs.setdefault("customer_decision_thresholds", {})[
        "Contoso_auto_approve_days_late"
    ] = new_threshold
    _save_beliefs(beliefs)

    status = "ok"
    if autopsy.strip().lower() == "beliefs":
        status = "fail"
        output.append("[AUTOPSY] Beliefs removed: each interaction treated independently; no learning accumulation across sessions.")

    return RunReport(
        organ="beliefs",
        status=status,
        firing=["Instructions", "Model", "Knowledge", "Tools", "Memory", "Beliefs", "Observability"],
        output=output,
        payoff=[
            "World state is explicit, versioned, and queryable—not hidden in weights or prompt history.",
            "Belief updates show exactly which facts changed and why (audit trail).",
            "Future decisions are shaped by accumulated evidence, not repeated guesswork.",
        ],
        landing_line=LANDING_LINE,
        usage=Usage(input_tokens=156, output_tokens=118, estimated_cost_usd=0.0, latency_seconds=0.18),
        source="local belief state engine",
        labels=["LOCAL IMPLEMENTATION"],
    )
