"""Small, adaptable recipes for attaching agent capabilities."""

import json
from pathlib import Path
from typing import Any

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import DefaultAzureCredential


def build_agent(client: Any) -> Agent:
    return Agent(
        client=client,
        name="refund-agent",
        instructions=(
            "Resolve refund requests from verified policy and order facts. "
            "Explain the evidence used for every decision."
        ),
    )


async def handle_business_event(agent: Agent, event: dict[str, Any]) -> str:
    prompt = f"Handle this new escalation event: {json.dumps(event)}"
    response = await agent.run(prompt)
    return str(response)


def add_knowledge(client: Any, policy_provider: Any) -> Agent:
    return Agent(
        client=client,
        instructions="Cite the approved policy passage used in the answer.",
        context_providers=[policy_provider],
    )


def make_order_lookup(order_repository: Any) -> Any:
    @tool(
        name="lookup_order",
        description="Return verified status and delay details for an order ID.",
        max_invocations=1,
    )
    def lookup_order(order_id: int) -> dict[str, Any]:
        return order_repository.find(order_id)

    return lookup_order


def add_tools(client: Any, order_repository: Any) -> Agent:
    return Agent(client=client, tools=[make_order_lookup(order_repository)])


def add_memory(client: Any, customer_memory: Any) -> Agent:
    return Agent(
        client=client,
        instructions="Use remembered preferences only for the current customer.",
        context_providers=[customer_memory],
    )


def add_guardrails(client: Any, safety_middleware: Any) -> Agent:
    return Agent(
        client=client,
        instructions="Never reveal another customer's data.",
        middleware=[safety_middleware],
    )


async def run_reviewed_workflow(
    request: str, researcher: Agent, writer: Agent, reviewer: Agent
) -> str:
    evidence = await researcher.run(request)
    draft = await writer.run(f"Draft from this evidence: {evidence}")
    approved = await reviewer.run(f"Review and correct this draft: {draft}")
    return str(approved)


async def run_with_identity(endpoint: str, model: str, prompt: str) -> str:
    async with DefaultAzureCredential() as credential:
        client = FoundryChatClient(
            project_endpoint=endpoint,
            model=model,
            credential=credential,
        )
        agent = Agent(client=client)
        return str(await agent.run(prompt))


def add_observability(client: Any, telemetry_middleware: Any) -> Agent:
    return Agent(
        client=client,
        middleware=[telemetry_middleware],
        additional_properties={"service.name": "refund-agent"},
    )


def add_budget(client: Any, budget_middleware: Any) -> Agent:
    return Agent(
        client=client,
        instructions="Stop when the run budget is exhausted.",
        middleware=[budget_middleware],
    )


def save_checkpoint(path: Path, completed_steps: set[str]) -> None:
    state = {"completed_steps": sorted(completed_steps)}
    path.write_text(json.dumps(state), encoding="utf-8")


def unfinished_steps(path: Path, all_steps: list[str]) -> list[str]:
    state = json.loads(path.read_text(encoding="utf-8"))
    completed = set(state["completed_steps"])
    return [step for step in all_steps if step not in completed]


def add_skill(client: Any, triage_skill: Any) -> Agent:
    return Agent(
        client=client,
        instructions="Select a skill only when its description matches the task.",
        tools=[triage_skill],
    )


def promote_instruction(candidate: str, evaluator: Any) -> str:
    baseline_score = evaluator.score_current()
    candidate_score = evaluator.score(candidate)
    return candidate if candidate_score > baseline_score else evaluator.current


def compose_agent(
    client: Any,
    tools: list[Any],
    providers: list[Any],
    middleware: list[Any],
) -> Agent:
    return Agent(
        client=client,
        instructions="Act only from verified evidence and explain each decision.",
        tools=tools,
        context_providers=providers,
        middleware=middleware,
    )