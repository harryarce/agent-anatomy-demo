import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay
from anatomy.telemetry import timed_span

STORY_BEAT = 0
FAILURE_IT_FIXES = "Ada needs a model before she can reason about the escalation."
LANDING_LINE = "A brain can answer, but without organs it cannot know whether its answer is true."
QUESTION = "Contoso is asking for a refund on order 4471. What do we do?"


@dataclass(slots=True)
class ModelResult:
    answer: str
    usage: Usage
    source: str


def _replay_path() -> Path:
    return Path(__file__).resolve().parents[2] / "replays" / "model.json"


def load_replay() -> ModelResult:
    payload = json.loads(_replay_path().read_text(encoding="utf-8"))
    return ModelResult(
        answer=payload["answer"],
        usage=Usage(**payload["usage"]),
        source="recorded Azure response",
    )


def _usage_from_response(response: Any, latency_seconds: float) -> Usage:
    raw = getattr(response, "usage_details", None) or getattr(response, "usage", None)
    if isinstance(raw, Mapping):
        input_tokens = raw.get("input_token_count", raw.get("input_tokens", 0))
        output_tokens = raw.get("output_token_count", raw.get("output_tokens", 0))
    else:
        input_tokens = getattr(raw, "input_token_count", 0)
        output_tokens = getattr(raw, "output_token_count", 0)
    return Usage(
        input_tokens=int(input_tokens or 0),
        output_tokens=int(output_tokens or 0),
        latency_seconds=latency_seconds,
    )


async def run_live(*, replay: bool, trace: bool) -> ModelResult:
    if replay:
        return load_replay()

    endpoint = os.getenv(
        "FOUNDRY_PROJECT_ENDPOINT",
        "https://haro-foundryai.services.ai.azure.com/api/projects/aiprj",
    )
    model = os.getenv("FOUNDRY_MODEL", os.getenv("FOUNDRY_MODEL_NAME", "gpt-5.6-terra"))
    credential = AzureCliCredential()
    try:
        agent = Agent(
            client=FoundryChatClient(
                project_endpoint=endpoint,
                model=model,
                credential=credential,
            ),
            instructions="Answer only from verified facts. State what must be checked when evidence is missing.",
        )
        with timed_span("organ.model", enabled=trace) as timing:
            response = await agent.run(QUESTION)
        return ModelResult(
            answer=str(response),
            usage=_usage_from_response(response, timing["latency_seconds"]),
            source=f"live Azure deployment {model}",
        )
    finally:
        await credential.close()


async def run_report(
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
    del question, record, stage, beat, kill, resume, tool_search
    if replay:
        return load_report_replay("model")
    try:
        model_result = await run_live(replay=False, trace=trace)
        output = [model_result.answer]
        payoff = [
            f"Ada answered using {model_result.source}.",
            "Without policy or order evidence, the answer remains tentative.",
        ]
        status = "ok"
        source = model_result.source
        labels: list[str] = []
        usage = model_result.usage
    except Exception as exc:
        status = "fail"
        labels = ["LOCAL IMPLEMENTATION"]
        source = "local deterministic fallback"
        output = [
            "Section 4.2 says Contoso gets a full refund after any late shipment.",
            f"Live model unavailable: {type(exc).__name__}",
        ]
        payoff = [
            "This is a deterministic local fallback for stage safety.",
            "The fabricated policy section demonstrates why Knowledge is next.",
        ]
        usage = Usage(input_tokens=21, output_tokens=24, estimated_cost_usd=0.0, latency_seconds=0.2)

    if autopsy.strip().lower() == "model":
        output.append("[AUTOPSY] Model organ removed: no language response generated.")
        status = "fail"

    return RunReport(
        organ="model",
        status=status,
        firing=["Model", "Observability", "Metabolism"],
        output=output,
        payoff=payoff,
        landing_line=LANDING_LINE,
        usage=usage,
        source=source,
        labels=labels,
    )


run = run_report
