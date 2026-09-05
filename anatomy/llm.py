from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from anatomy.budget import Usage
from anatomy.common import RunReport
from anatomy.telemetry import timed_span

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
load_dotenv(ENV_PATH if ENV_PATH.exists() else ROOT / ".env.example")

DEFAULT_ENDPOINT = "https://haro-foundryai.services.ai.azure.com/api/projects/aiprj"
DEFAULT_MODEL = "gpt-5.6-terra"


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


async def grounded_synthesis(
    *,
    organ: str,
    question: str,
    evidence: list[str],
    trace: bool,
) -> tuple[str, Usage, str]:
    endpoint, model = foundry_settings()
    credential = AzureCliCredential()
    try:
        agent = Agent(
            client=FoundryChatClient(
                project_endpoint=endpoint,
                model=model,
                credential=credential,
            ),
            instructions=(
                "You are Ada, a customer escalation agent. Use only the supplied evidence. "
                "Return one concise sentence explaining what the evidence proves. "
                "Do not invent facts, citations, actions, or outcomes."
            ),
        )
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
    finally:
        await credential.close()


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