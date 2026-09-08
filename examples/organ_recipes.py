"""Small, adaptable recipes for attaching agent capabilities."""

import json
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from agent_framework import (
    Agent,
    ChatMiddleware,
    ContextProvider,
    FileCheckpointStorage,
    FunctionMiddleware,
    FunctionTool,
    MiddlewareTypes,
    SkillsProvider,
    ToolApprovalMiddleware,
    Workflow,
    WorkflowBuilder,
    tool,
)
from agent_framework.observability import configure_otel_providers
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import DefaultAzureCredential
from pydantic import BaseModel, Field


def build_model_agent(client: Any) -> Agent:
    return Agent(
        client=client,
        name="refund-agent",
    )


def add_instructions(client: Any) -> Agent:
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


def add_knowledge(client: Any, policy_provider: ContextProvider) -> Agent:
    return Agent(
        client=client,
        instructions="Cite the approved policy passage used in the answer.",
        context_providers=[policy_provider],
    )


def make_order_lookup(order_repository: Any) -> FunctionTool:
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


def add_memory(client: Any, customer_memory: ContextProvider) -> Agent:
    return Agent(
        client=client,
        instructions="Use remembered preferences only for the current customer.",
        context_providers=[customer_memory],
    )


def add_guardrails(client: Any, safety_middleware: MiddlewareTypes) -> Agent:
    return Agent(
        client=client,
        instructions="Never reveal another customer's data.",
        middleware=[safety_middleware],
    )


def build_reviewed_workflow(
    researcher: Agent, writer: Agent, reviewer: Agent
) -> Workflow:
    return (
        WorkflowBuilder(start_executor=researcher, output_from=[reviewer])
        .add_edge(researcher, writer)
        .add_edge(writer, reviewer)
        .build()
    )


async def run_with_identity(endpoint: str, model: str, prompt: str) -> str:
    async with AsyncExitStack() as stack:
        credential = await stack.enter_async_context(DefaultAzureCredential())
        client = FoundryChatClient(
            project_endpoint=endpoint,
            model=model,
            credential=credential,
        )
        stack.push_async_callback(client.project_client.close)
        stack.push_async_callback(client.client.close)
        agent = await stack.enter_async_context(Agent(client=client))
        return str(await agent.run(prompt))


def enable_observability() -> None:
    configure_otel_providers(env_file_path=".env")


def add_budget(
    client: Any, model_budget: ChatMiddleware, tool_budget: FunctionMiddleware
) -> Agent:
    return Agent(
        client=client,
        instructions="Stop when the run budget is exhausted.",
        middleware=[model_budget, tool_budget],
    )


def build_checkpointed_workflow(
    researcher: Agent, writer: Agent, reviewer: Agent, path: Path
) -> Workflow:
    storage = FileCheckpointStorage(path)
    return (
        WorkflowBuilder(
            start_executor=researcher,
            output_from=[reviewer],
            checkpoint_storage=storage,
        )
        .add_edge(researcher, writer)
        .add_edge(writer, reviewer)
        .build()
    )


async def resume_workflow(workflow: Workflow, checkpoint_id: str) -> str:
    result = await workflow.run(checkpoint_id=checkpoint_id)
    outputs = result.get_outputs()
    if not outputs:
        raise RuntimeError("Workflow has no terminal output; inspect pending requests and events.")
    return str(outputs[-1])


def add_skill(client: Any, skills_path: Path) -> Agent:
    provider = SkillsProvider.from_paths(skill_paths=skills_path)
    approval = ToolApprovalMiddleware(
        auto_approval_rules=[SkillsProvider.read_only_tools_auto_approval_rule]
    )
    return Agent(
        client=client,
        instructions="Select a skill only when its description matches the task.",
        context_providers=[provider],
        middleware=[approval],
    )


async def run_skill(agent: Agent, prompt: str) -> str:
    session = agent.create_session()
    response = await agent.run(prompt, session=session)
    if response.user_input_requests:
        raise RuntimeError("Skill execution requires explicit host approval.")
    return str(response)


def promote_instruction(candidate: str, evaluator: Any) -> str:
    baseline_score = evaluator.score_current()
    candidate_score = evaluator.score(candidate)
    return candidate if candidate_score > baseline_score else evaluator.current


def compose_agent(
    client: Any,
    tools: list[FunctionTool],
    providers: list[ContextProvider],
    middleware: list[MiddlewareTypes],
) -> Agent:
    return Agent(
        client=client,
        instructions="Act only from verified evidence and explain each decision.",
        tools=tools,
        context_providers=providers,
        middleware=middleware,
    )


class PlanStep(BaseModel):
    name: str
    depends_on: list[str]
    success_condition: str


class ExecutionPlan(BaseModel):
    steps: list[PlanStep] = Field(min_length=1)


def add_planning(client: Any) -> Agent:
    return Agent(
        client=client,
        instructions=(
            "Only plan; do not execute actions. Decompose the goal into ordered steps. "
            "Give each step a unique name, dependencies, and a success condition."
        ),
        default_options={"response_format": ExecutionPlan},
    )


async def create_plan(agent: Agent, goal: str) -> ExecutionPlan:
    response = await agent.run(goal)
    plan = ExecutionPlan.model_validate(response.value)
    completed: set[str] = set()
    for step in plan.steps:
        if step.name in completed or not set(step.depends_on) <= completed:
            raise ValueError("Plan has duplicate names or dependencies out of order.")
        completed.add(step.name)
    return plan


def add_beliefs(
    client: Any,
    belief_provider: ContextProvider,
    update_belief: FunctionTool,
) -> Agent:
    return Agent(
        client=client,
        instructions=(
            "Use only evidence-backed world state. "
            "Explain how any persisted update changes the next decision."
        ),
        context_providers=[belief_provider],
        tools=[update_belief],
    )