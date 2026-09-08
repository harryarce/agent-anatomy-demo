from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from collections.abc import Mapping
from pathlib import Path
from typing import Any, AsyncIterator

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from anatomy.budget import Usage
from anatomy.common import RunReport
from anatomy.telemetry import timed_span

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
load_dotenv(ENV_PATH if ENV_PATH.exists() else ROOT / ".env.example")

DEFAULT_ENDPOINT = "https://haro-foundryai.services.ai.azure.com/api/projects/aiprj"
DEFAULT_MODEL = "gpt-5.6-terra"
AZURE_CLI_PROCESS_TIMEOUT_SECONDS = 30


class AsyncAzureCliCredential:
    def __init__(self) -> None:
        self._credential = AzureCliCredential(process_timeout=AZURE_CLI_PROCESS_TIMEOUT_SECONDS)

    async def get_token(self, *scopes: str, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._credential.get_token, *scopes, **kwargs)

    async def get_token_info(self, *scopes: str, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._credential.get_token_info, *scopes, **kwargs)

    async def close(self) -> None:
        await asyncio.to_thread(self._credential.close)


def foundry_settings() -> tuple[str, str]:
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", DEFAULT_ENDPOINT)
    model = os.getenv("FOUNDRY_MODEL", os.getenv("FOUNDRY_MODEL_NAME", DEFAULT_MODEL))
    return endpoint, model


def usage_from_response(response: Any, latency_seconds: float) -> Usage:
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


def failure_summary(exc: Exception) -> str:
    current: BaseException | None = exc
    while current is not None:
        if getattr(current, "status_code", None) == 403:
            return "Foundry permission denied (HTTP 403)"
        current = current.__cause__ or current.__context__
    return type(exc).__name__


@asynccontextmanager
async def foundry_agent(*, instructions: str | None = None) -> AsyncIterator[Agent]:
    endpoint, model = foundry_settings()
    credential = AsyncAzureCliCredential()
    client: FoundryChatClient | None = None
    try:
        client = FoundryChatClient(
            project_endpoint=endpoint,
            model=model,
            credential=credential,
        )
        async with Agent(client=client, instructions=instructions) as agent:
            yield agent
    finally:
        if client is not None:
            await client.client.close()
            await client.project_client.close()
        await credential.close()


async def grounded_synthesis(
    *,
    organ: str,
    question: str,
    evidence: list[str],
    trace: bool,
) -> tuple[str, Usage, str]:
    _, model = foundry_settings()
    async with foundry_agent(
        instructions=(
            "You are Ada, a customer escalation agent. Use only the supplied evidence. "
            "Return one concise sentence explaining what the evidence proves. "
            "Do not invent facts, citations, actions, or outcomes."
        )
    ) as agent:
        prompt = (
            f"Organ: {organ}\n"
            f"Customer question: {question}\n"
            "Deterministic evidence:\n- "
            + "\n- ".join(evidence)
        )
        with timed_span(f"organ.{organ}.llm", enabled=trace) as timing:
            response = await agent.run(prompt)
        return (
            str(response).strip(),
            usage_from_response(response, timing["latency_seconds"]),
            f"live Azure deployment {model}",
        )


async def enhance_report_with_llm(
    report: RunReport,
    *,
    question: str,
    trace: bool,
) -> RunReport:
    try:
        synthesis, usage, source = await grounded_synthesis(
            organ=report.organ,
            question=question,
            evidence=report.output,
            trace=trace,
        )
    except Exception as exc:
        report.output.append(
            f"LLM synthesis unavailable ({failure_summary(exc)}); deterministic evidence retained."
        )
        if "DETERMINISTIC FALLBACK" not in report.labels:
            report.labels.append("DETERMINISTIC FALLBACK")
        return report

    report.output.append(f"LLM synthesis: {synthesis}")
    report.source = f"{report.source} + {source}"
    report.labels.append("LIVE LLM")
    report.usage = Usage(
        input_tokens=report.usage.input_tokens + usage.input_tokens,
        output_tokens=report.usage.output_tokens + usage.output_tokens,
        estimated_cost_usd=report.usage.estimated_cost_usd + usage.estimated_cost_usd,
        latency_seconds=report.usage.latency_seconds + usage.latency_seconds,
    )
    return report