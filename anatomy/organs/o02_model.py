import json
from dataclasses import dataclass
from pathlib import Path

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

from anatomy.budget import Usage
from anatomy.common import RunReport, load_report_replay
from anatomy.llm import failure_summary, foundry_settings, usage_from_response
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


async def run_live(*, replay: bool, trace: bool) -> ModelResult:
    if replay:
        return load_replay()

    endpoint, model = foundry_settings()
    credential = AzureCliCredential()
    try:
        agent = Agent(
            client=FoundryChatClient(
                project_endpoint=endpoint,
                model=model,
                credential=credential,
            ),
        )
        with timed_span("organ.model", enabled=trace) as timing:
            response = await agent.run(QUESTION)
        return ModelResult(
            answer=str(response),
            usage=usage_from_response(response, timing["latency_seconds"]),
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
    remote: bool = False,
) -> RunReport:
    del question, record, stage, beat, kill, resume, tool_search
    if replay:
        return load_report_replay("model")
    if not remote:
        return RunReport(
            organ="model",
            status="ok",
            firing=["Model"],
            output=[
                "A refund may be appropriate, but I cannot verify order 4471 or Contoso's eligibility from the information provided.",
                "Next step: retrieve the approved refund policy and current order record before taking action.",
            ],
            payoff=[
                "This deterministic baseline demonstrates the model's reasoning role without a network call.",
                "It deliberately exposes the missing Knowledge and Tools organs that come next.",
            ],
            landing_line=LANDING_LINE,
            usage=Usage(input_tokens=0, output_tokens=0, estimated_cost_usd=0.0, latency_seconds=0.0),
            source="local deterministic model baseline",
            labels=["LOCAL DETERMINISTIC"],
        )
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
        status = "ok"
        labels = ["DETERMINISTIC FALLBACK"]
        source = "local deterministic fallback"
        output = [
            "Section 4.2 says Contoso gets a full refund after any late shipment.",
            f"Live model unavailable: {failure_summary(exc)}",
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
        firing=["Model"],
        output=output,
        payoff=payoff,
        landing_line=LANDING_LINE,
        usage=usage,
        source=source,
        labels=labels,
    )


run = run_report
