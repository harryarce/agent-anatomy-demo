from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from anatomy.budget import Usage

DEFAULT_QUESTION = "Contoso is asking for a refund on order 4471. What do we do?"


@dataclass(slots=True)
class RunReport:
    organ: str
    status: str
    firing: list[str]
    output: list[str]
    payoff: list[str]
    landing_line: str
    usage: Usage = field(default_factory=Usage)
    labels: list[str] = field(default_factory=list)
    source: str = "local"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["usage"] = asdict(self.usage)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunReport":
        usage_payload = payload.get("usage", {})
        usage = Usage(
            input_tokens=int(usage_payload.get("input_tokens", 0)),
            output_tokens=int(usage_payload.get("output_tokens", 0)),
            estimated_cost_usd=float(usage_payload.get("estimated_cost_usd", 0.0)),
            latency_seconds=float(usage_payload.get("latency_seconds", 0.0)),
        )
        return cls(
            organ=str(payload.get("organ", "unknown")),
            status=str(payload.get("status", "ok")),
            firing=[str(item) for item in payload.get("firing", [])],
            output=[str(item) for item in payload.get("output", [])],
            payoff=[str(item) for item in payload.get("payoff", [])],
            landing_line=str(payload.get("landing_line", "")),
            usage=usage,
            labels=[str(item) for item in payload.get("labels", [])],
            source=str(payload.get("source", "local")),
        )


def replay_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "replays"


def replay_path(organ: str) -> Path:
    return replay_dir() / f"{organ}.json"


def load_report_replay(organ: str) -> RunReport:
    payload = json.loads(replay_path(organ).read_text(encoding="utf-8"))
    if "answer" in payload and organ == "model":
        return RunReport(
            organ="model",
            status="ok",
            firing=["Model", "Observability", "Metabolism"],
            output=[str(payload["answer"])],
            payoff=["Replay loaded from committed transcript."],
            landing_line="A brain can answer, but without organs it cannot know whether its answer is true.",
            usage=Usage(**payload.get("usage", {})),
            source="recorded Azure response",
        )
    return RunReport.from_dict(payload)


def save_report_replay(report: RunReport) -> Path:
    path = replay_path(report.organ)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return path


def _actor_for_line(organ: str, line: str) -> str:
    if line.startswith("Application team configures"):
        return "APPLICATION TEAM"
    if line.startswith("Ada follows"):
        return "AI / MODEL"
    if line.startswith("Demo setup"):
        return "SYSTEM"
    if organ in {"instructions", "model"}:
        return "AI / MODEL"
    if organ == "tools":
        return "TOOL"
    if organ == "orchestration" and line.startswith("Node "):
        node = line.removeprefix("Node ").split(":", 1)[0]
        return f"AGENT · {node.upper()}"
    if organ in {"spine", "observability"}:
        return "SYSTEM"
    return f"ORGAN · {organ.upper().replace('_', ' ')}"


def attributed_story(report: RunReport, question: str = DEFAULT_QUESTION) -> list[tuple[str, str]]:
    """Turn organ evidence into a speaker-friendly, actor-attributed transcript."""
    story = [("USER", question)]
    for output_item in report.output:
        for line in output_item.splitlines() or [""]:
            if report.organ == "guardrails" and " -> " in line:
                request, decision = line.split(" -> ", 1)
                requester = "TOOL" if "tool output" in request.lower() else "USER"
                story.append((requester, request))
                story.append(("ORGAN · GUARDRAILS", decision))
                continue
            story.append((_actor_for_line(report.organ, line), line))
    return story


def attributed_story_text(report: RunReport, question: str = DEFAULT_QUESTION) -> str:
    return "\n".join(f"[{actor}]  {line}" for actor, line in attributed_story(report, question))