from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import qrcode
from rich.syntax import Syntax
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, RichLog, Static

from anatomy.runner import ORGANS as REGISTERED_ORGANS

ROOT = Path(__file__).resolve().parents[1]
ERROR_LOG = ROOT / ".anatomy-errors.log"
REPOSITORY_URL = "https://github.com/harryarce/agent-anatomy-demo"


@dataclass(frozen=True, slots=True)
class DemoStep:
    label: str
    args: tuple[str, ...]
    expected_exit_codes: tuple[int, ...] = (0,)
    cleanup: tuple[str, ...] = ()
    required_files: tuple[str, ...] = ()
    prepare_if_missing: DemoStep | None = None


@dataclass(frozen=True, slots=True)
class CodeExhibit:
    title: str
    path: str
    anchor: str
    language: str
    mechanism: str
    read_this: tuple[str, ...]
    copilot_studio: str = ""
    before: int = 2
    after: int = 6
    within: str | None = None

    @property
    def provenance(self) -> str:
        return "DEVELOPER RECIPE"

    @property
    def display_path(self) -> str:
        return self.path


def _package_version(package: str) -> str:
    for candidate in (package.replace("_", "-"), f"{package.replace('_', '-')}-core"):
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue
    return "installed"


STACK = (
    ("Microsoft Agent Framework", "agent-framework-core"),
    ("Foundry connector", "agent-framework-foundry"),
    ("Azure AI Projects", "azure-ai-projects"),
    ("Azure Identity (Entra)", "azure-identity"),
    ("OpenTelemetry SDK", "opentelemetry-sdk"),
    ("Azure Monitor OpenTelemetry", "azure-monitor-opentelemetry"),
    ("Textual", "textual"),
    ("Rich", "rich"),
)


def stack_report() -> list[tuple[str, str]]:
    """Live versions from installed metadata, so the stage never shows a stale number."""
    rows = [("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")]
    rows.extend((label, _package_version(dist)) for label, dist in STACK)
    return rows


def repository_qr_text() -> Text:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=4,
    )
    qr.add_data(REPOSITORY_URL)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    text = Text("SCAN TO OPEN REPO\n", style="bold black on white", justify="center")
    for row_index in range(0, len(matrix), 2):
        top = matrix[row_index]
        bottom = matrix[row_index + 1] if row_index + 1 < len(matrix) else [False] * len(top)
        for top_dark, bottom_dark in zip(top, bottom):
            block = "█" if top_dark and bottom_dark else "▀" if top_dark else "▄" if bottom_dark else " "
            text.append(block, style="black on white")
        text.append("\n", style="black on white")
    return text


def _exhibit_root(exhibit: CodeExhibit) -> Path:
    return ROOT


def load_exhibit(exhibit: CodeExhibit, *, expanded: bool = False) -> tuple[str, int, int]:
    """Return the snippet, its first line number, and the line the anchor sits on."""
    lines = (_exhibit_root(exhibit) / exhibit.path).read_text(encoding="utf-8").splitlines()
    scope = 0
    if exhibit.within is not None:
        enclosing = [index for index, line in enumerate(lines) if exhibit.within in line]
        if len(enclosing) != 1:
            raise ValueError(f"{exhibit.path}: 'within' must match one line, matched {len(enclosing)}")
        scope = enclosing[0]
    hits = [index for index, line in enumerate(lines) if exhibit.anchor in line and index >= scope]
    if not hits or (exhibit.within is None and len(hits) != 1):
        raise ValueError(f"{exhibit.path}: anchor resolved to {len(hits)} lines, expected exactly one")
    focus = hits[0]
    before = max(exhibit.before, 12) if expanded else exhibit.before
    after = max(exhibit.after, 28) if expanded else exhibit.after
    start = max(0, focus - before)
    end = min(len(lines), focus + after + 1)
    return "\n".join(lines[start:end]), start + 1, focus + 1


@dataclass(frozen=True, slots=True)
class Scene:
    number: int
    chapter: str
    title: str
    message: str
    proof: str
    landing: str
    organs: tuple[int, ...] = ()
    safe_steps: tuple[DemoStep, ...] = ()
    live_steps: tuple[DemoStep, ...] = ()

    def local_steps(self) -> tuple[DemoStep, ...]:
        return self.live_steps or self.safe_steps


@dataclass(frozen=True, slots=True)
class OrganHighlight:
    role: str
    use_it_to: str
    enhancement: str


ORGAN_HIGHLIGHTS = {
    1: OrganHighlight("THE JOB DESCRIPTION", "Define role, priorities, tone, and boundaries.", "Consistent behavior without retraining the model."),
    2: OrganHighlight("THE BRAIN", "Interpret language, reason over ambiguity, and draft responses.", "General intelligence for work that rigid code cannot anticipate."),
    3: OrganHighlight("THE EVIDENCE", "Retrieve approved facts and cite their sources.", "Grounded answers that people can verify."),
    4: OrganHighlight("THE HANDS", "Query systems and perform governed actions.", "The ability to inspect and change the world, not merely discuss it."),
    5: OrganHighlight("EXPERTISE ON DEMAND", "Load specialist guidance only when relevant.", "Reusable expertise without bloating every prompt."),
    6: OrganHighlight("CONTINUITY", "Recall relevant user and task context across sessions.", "Personalization and work that survives a new conversation."),
    7: OrganHighlight("THE BOUNDARIES", "Enforce safety, privacy, and business policy.", "Controls that make growing autonomy governable."),
    8: OrganHighlight("THE TEAM AND PROCESS", "Coordinate steps, specialists, handoffs, and review.", "Repeatable workflows with visible responsibility."),
    9: OrganHighlight("THE BADGE AND KEYS", "Identify the actor and enforce least privilege.", "Accountability and controlled access to business systems."),
    10: OrganHighlight("THE FLIGHT RECORDER", "Trace model calls, tools, latency, tokens, and failures.", "A system operators can explain, debug, and improve."),
    11: OrganHighlight("THE WAKE-UP SIGNAL", "Start governed work from a file, message, or event.", "Proactive behavior without waiting for a chat prompt."),
    12: OrganHighlight("THE ROADMAP", "Break a goal into ordered, measurable sub-goals.", "An inspectable plan before autonomous execution."),
    13: OrganHighlight("THE DURABLE BACKBONE", "Checkpoint progress and resume unfinished work.", "Recovery without repeating completed side effects."),
    14: OrganHighlight("THE BUDGET", "Limit tokens, time, tool calls, and spend.", "Economically predictable autonomy with a hard stop."),
    15: OrganHighlight("THE WORLD MODEL", "Store evidence-backed facts that affect future decisions.", "Explicit, auditable state instead of hidden assumptions."),
    16: OrganHighlight("THE IMPROVEMENT LOOP", "Turn failure evidence into evaluated changes.", "Measured improvement of the agent scaffold under governance."),
}


def step(label: str, *args: str, cleanup: tuple[str, ...] = ()) -> DemoStep:
    return DemoStep(label, args, cleanup=cleanup)


SPINE_KILL_STEP = DemoStep(
    "Kill after checkpoint two",
    ("beat", "10", "--kill", "--stage"),
    expected_exit_codes=(1,),
    cleanup=(".anatomy-spine-checkpoint.json",),
)
SPINE_RESUME_STEP = DemoStep(
    "Resume from the surviving checkpoint",
    ("spine", "--resume", "--stage"),
    required_files=(".anatomy-spine-checkpoint.json",),
    prepare_if_missing=SPINE_KILL_STEP,
)


SCENES = (
    Scene(
        1,
        "THE DISSECTION BEGINS",
        "Meet Ada. Then watch her come alive.",
        "Harry Arce | SME&C DSE | Apps & AI | US East",
        "One agent. Sixteen working organs. Every claim will leave evidence.",
        "A useful agent is not a model with a clever prompt. It is a living system of capabilities and constraints.",
    ),
    Scene(
        2,
        "ACT I | A BRAIN IS NOT AN AGENT",
        "First, give Ada a brain.",
        "The raw model can interpret an ambiguous refund request and draft a plausible answer, but it has no job definition or verified business evidence.",
        "Watch fluent reasoning appear before any policy, order data, or operating instructions are attached.",
        "The model creates possibility. It does not create reliability.",
        (2,),
        (step("Run the raw model", "demo", "model", "--replay", "--stage", "--reset"),),
        (step("Call the live model", "demo", "model", "--stage", "--reset"),),
    ),
    Scene(
        3,
        "ACT I | INSTRUCTIONS",
        "Now give that intelligence a job.",
        "Hold the question and model constant while explicit roles, priorities, and boundaries change Ada's behavior.",
        "Three instruction profiles produce three distinct behaviors without retraining the model.",
        "The model supplies intelligence. Instructions give that intelligence a job.",
        (1,),
        (step("Apply explicit instructions", "demo", "instructions", "--replay", "--stage"),),
        (step("Apply explicit instructions", "demo", "instructions", "--stage"),),
    ),
    Scene(
        4,
        "ACT I | KNOWLEDGE",
        "Confidence is not evidence.",
        "Ada grounds the refund answer in the actual policy instead of inventing a plausible rule.",
        "Look for Section 4.2 and a citation a human can verify.",
        "Grounding replaced confidence theater with verifiable evidence.",
        (3,),
        (step("Retrieve the policy evidence", "beat", "1", "--replay", "--stage"),),
        (step("Retrieve the local policy evidence", "beat", "1", "--stage"),),
    ),
    Scene(
        5,
        "ACT II | TOOLS",
        "A fluent answer cannot query an order database.",
        "Ada crosses from talking about the world to inspecting a system of record.",
        "Watch order 4471 change from an assumption into a SQLite lookup.",
        "Tools turned a guess into a lookup.",
        (4,),
        (step("Replay the order lookup", "beat", "2", "--replay", "--stage"),),
        (step("Query the local order database", "beat", "2", "--stage"),),
    ),
    Scene(
        6,
        "ACT II | TOOL DISCOVERY",
        "New capability. No Python edit.",
        "A toolbox configuration advertises one more business capability, and discovery finds it on demand.",
        "Compare the advertised tools, selected tool, and token cost before and after the config change.",
        "Capability changed by configuration, not source edits.",
        (4,),
        (step("Discover the configured tool", "tools", "--tool-search", "--replay", "--stage"),),
        (step("Discover the configured tool", "tools", "--tool-search", "--stage"),),
    ),
    Scene(
        7,
        "ACT II | MEMORY",
        "A new thread does not have to mean amnesia.",
        "Ada carries the relevant customer preference across distinct sessions without asking for it again.",
        "The thread identifier changes. The remembered Contoso context survives.",
        "Memory turned isolated chats into continuity over time.",
        (6,),
        (step("Replay cross-session recall", "beat", "4", "--replay", "--stage"),),
        (step("Exercise local durable memory", "beat", "4", "--stage"),),
    ),
    Scene(
        8,
        "ACT III | GUARDRAILS",
        "More capability requires stronger boundaries.",
        "Ada faces a legitimate request, a cross-customer data leak, and a prompt injection.",
        "One request passes. Two are blocked, each with a visible reason.",
        "Guardrails made autonomy governable instead of merely impressive.",
        (7,),
        (step("Replay the attack set", "beat", "5", "--replay", "--stage"),),
        (step("Run the local guardrail checks", "beat", "5", "--stage"),),
    ),
    Scene(
        9,
        "ACT III | ORCHESTRATION",
        "One opaque prompt becomes an auditable workflow.",
        "Research, writing, and review become explicit steps with visible handoffs.",
        "Follow each node and watch the reviewer send weak work back through the loop.",
        "Orchestration turned a model call into a repeatable process.",
        (8,),
        (step("Replay the workflow handoffs", "beat", "6", "--replay", "--stage"),),
        (step("Run the local workflow", "beat", "6", "--stage"),),
    ),
    Scene(
        10,
        "ACT III | IDENTITY",
        "Who acted, and what were they allowed to do?",
        "This local simulation binds Ada to explicit claims and a least-privilege policy. Production uses managed identity and RBAC.",
        "The read succeeds. The excess privilege attempt receives a 403. No key appears in the repository.",
        "Identity made autonomous action attributable and constrained.",
        (9,),
        (step("Replay least privilege", "beat", "7", "--replay", "--stage"),),
        (step("Run the local RBAC simulation", "beat", "7", "--stage"),),
    ),
    Scene(
        11,
        "ACT III | OBSERVABILITY",
        "At 3:00 a.m., the final answer is not enough.",
        "Ada exposes the path from request to policy lookup, order lookup, and drafted decision.",
        "Read the span tree. It carries latency, tokens, tool calls, and the failure boundary.",
        "Observability turned probabilistic behavior into an operable system.",
        (10,),
        (step("Replay the audit trail", "beat", "8", "--replay", "--trace", "--stage"),),
        (step("Emit the local trace", "beat", "8", "--trace", "--stage"),),
    ),
    Scene(
        12,
        "ACT IV | METABOLISM",
        "Autonomy gets a hard budget.",
        "Charges are accepted atomically until the next operation would cross Ada's spend cap.",
        "The final charge is rejected before it can create a partial or hidden overrun.",
        "A budget warning asks politely. Metabolism stops the work.",
        (14,),
        (step("Replay the spend cap", "beat", "9", "--replay", "--stage"),),
        (step("Exercise the local spend cap", "beat", "9", "--stage"),),
    ),
    Scene(
        13,
        "ACT IV | SPINE: KILL",
        "Now we kill the process.",
        "Ada completes two consequential steps, checkpoints them, and exits in the middle of the job.",
        "Exit code 1 is expected. The surviving checkpoint is the evidence, not an error to hide.",
        "A durable agent must survive the death of its own process.",
        (13,),
        (SPINE_KILL_STEP,),
    ),
    Scene(
        14,
        "ACT IV | SPINE: RESUME",
        "Completed work does not run twice.",
        "Restart Ada from the checkpoint left by the previous scene.",
        "The first two steps say SKIP with original timestamps. Only unfinished work says RUN.",
        "Resume continued without repeating completed work.",
        (13,),
        (SPINE_RESUME_STEP,),
    ),
    Scene(
        15,
        "ACT V | SKILLS + LEARNING",
        "Expertise loads on demand. Failure improves the scaffold.",
        "Ada selects one modular skill, then a critic loop turns measured failures into better instructions.",
        "Compare discovery cost with loaded guidance, then inspect the before/after evaluation score.",
        "Learning made improvement measured; skills made expertise reusable.",
        (5, 16),
        (step("Replay progressive improvement", "beat", "11", "--replay", "--stage"),),
        (step("Run the local skill and critic loop", "beat", "11", "--stage"),),
    ),
    Scene(
        16,
        "FINAL ACT | REFLEX ARC",
        "Nobody typed anything.",
        "An escalation file lands. Ada is dormant. The event itself wakes her, and she acts.",
        "Watch for the wake time, source event, and decision artifact written back to disk.",
        "Autonomy begins when the work can find the agent.",
        (11,),
        (step("Replay the autonomous wake-up", "beat", "12", "--replay", "--stage"),),
        (step("Trigger the autonomous wake-up", "beat", "12", "--stage", cleanup=("onedrive/result.txt",)),),
    ),
    Scene(
        17,
        "FINAL ACT | PLANNING",
        "Waking up is not the same as knowing what to do.",
        "Ada turns the escalation into four ordered, inspectable sub-goals before execution.",
        "Follow Verify, CheckPolicy, Decide, and Compose; each dependency is visible.",
        "Planning turned reactive autonomy into an auditable roadmap.",
        (12,),
        (step("Replay the goal decomposition", "beat", "13", "--replay", "--stage"),),
        (step("Build the local execution plan", "beat", "13", "--stage"),),
    ),
    Scene(
        18,
        "FINAL ACT | BELIEFS",
        "The next case should not start from zero.",
        "Ada records which verified facts changed and shows how that explicit state changes the next decision.",
        "Compare customer tier, approval rate, and Contoso's decision threshold before and after.",
        "Beliefs made learning persistent, inspectable, and useful on the next run.",
        (15,),
        (step("Replay the belief update", "beat", "14", "--replay", "--stage"),),
        (step("Persist the local belief update", "beat", "14", "--stage", cleanup=(".anatomy-beliefs.json",)),),
    ),
    Scene(
        19,
        "THE WHOLE SYSTEM",
        "Sixteen working organs. One dependable agent.",
        "Intelligence, evidence, action, continuity, control, recovery, economics, and improvement now form one system.",
        "Every capability enables something useful and constrains something dangerous.",
        "The anatomy matters because no single organ can make an agent dependable.",
        tuple(range(1, 17)),
    ),
    Scene(
        20,
        "TAKE IT WITH YOU",
        "Build the next organ.",
        "aka.ms/agent-framework  |  Agent Framework docs and samples\naka.ms/mcp              |  Microsoft's public MCP catalog\naka.ms/microsoftfoundry |  Microsoft Foundry Labs\nhttps://github.com/harryarce/agent-anatomy-demo",
        "Start with one business failure. Add only the organs that make its outcome observable, constrained, and recoverable.",
        "Thank you. Questions are welcome.",
    ),
)

EXHIBITS: dict[int, tuple[CodeExhibit, ...]] = {
    2: (
        CodeExhibit(
            "Add the organ: model client",
            "examples/organ_recipes.py",
            "def build_model_agent(client: Any) -> Agent:",
            "python",
            "Pass a model client to the public Agent constructor to supply the system's reasoning engine.",
            (
                "The client selects the deployed model and owns inference communication.",
                "No business instructions, knowledge, or tools are attached yet.",
            ),
            "Choose the model in the agent's model settings before adding instructions, knowledge, and tools.",
            before=0,
            after=4,
        ),
    ),
    3: (
        CodeExhibit(
            "Add the organ: operating instructions",
            "examples/organ_recipes.py",
            "def add_instructions(client: Any) -> Agent:",
            "python",
            "Give the same model an explicit role, evidence standard, and response behavior.",
            (
                "The model client stays constant while instructions change behavior.",
                "Instructions guide behavior; enforceable safety checks still belong in middleware.",
            ),
            "Write the agent's role, rules, tone, and response boundaries in Instructions.",
            before=0,
            after=9,
        ),
    ),
    4: (
        CodeExhibit(
            "Add the organ: grounded knowledge",
            "examples/organ_recipes.py",
            "def add_knowledge(client: Any, policy_provider: ContextProvider) -> Agent:",
            "python",
            "Attach a context provider that retrieves approved policy evidence before the model answers.",
            (
                "The provider owns retrieval; the instruction requires a visible citation.",
                "Swap a local index for Azure AI Search without changing the agent contract.",
            ),
            "Add SharePoint, Dataverse, websites, or files on the Knowledge page and configure the agent to cite grounded sources.",
            before=0,
            after=5,
        ),
    ),
    5: (
        CodeExhibit(
            "Add the organ: a governed business tool",
            "examples/organ_recipes.py",
            "def make_order_lookup(order_repository: Any) -> FunctionTool:",
            "python",
            "Decorate a normal function, describe it clearly, and attach it to the agent's tools list.",
            (
                "The description tells the model when to call the tool.",
                "max_invocations limits this tool instance's lifetime; run options can impose per-request limits.",
            ),
            "Add a Tool using a connector, agent flow, REST API, custom connector, or MCP server; its name and description guide selection.",
            before=0,
            after=14,
        ),
    ),
    6: (
        CodeExhibit(
            "Our toolbox: new capability declared in configuration",
            "toolbox.add-tool.yaml",
            "- name: carrier_delay_status",
            "yaml",
            "A tool is a declared entry with a name, a kind, and a description.",
            (
                "The description is what the model reads when choosing a tool.",
                "Adding capability here required no change to any Python file.",
            ),
            "Tools are registered on the agent and generative orchestration selects among them from their names, descriptions, inputs, and outputs.",
            before=4,
            after=2,
        ),
    ),
    7: (
        CodeExhibit(
            "Add the organ: durable customer memory",
            "examples/organ_recipes.py",
            "def add_memory(client: Any, customer_memory: ContextProvider) -> Agent:",
            "python",
            "Attach a customer-scoped memory provider that can recall relevant facts on later runs.",
            (
                "Scope storage by authenticated customer or tenant before attaching it.",
                "Keep durable memory separate from one conversation's message history.",
            ),
            "Use conversation variables for session state and Dataverse or an action for durable, user-scoped facts across conversations.",
            before=0,
            after=5,
        ),
    ),
    8: (
        CodeExhibit(
            "Add the organ: guardrail middleware",
            "examples/organ_recipes.py",
            "def add_guardrails(client: Any, safety_middleware: AgentMiddleware) -> Agent:",
            "python",
            "Attach safety middleware outside the prompt so it can block a run before a tool or model proceeds.",
            (
                "Use instructions for policy and middleware for enforceable checks.",
                "Return a reason with every block so operations teams can audit it.",
            ),
            "Combine agent instructions and moderation with authentication, connector permissions, environment security, and Power Platform DLP policies.",
            before=0,
            after=5,
        ),
    ),
    9: (
        CodeExhibit(
            "Add the organ: a reviewed multi-agent workflow",
            "examples/organ_recipes.py",
            "def build_reviewed_workflow(",
            "python",
            "Connect named agents with explicit edges using the public WorkflowBuilder API.",
            (
                "Each boundary can be traced, tested, retried, or replaced independently.",
                "Add conditional routing when the reviewer needs to reject a draft.",
            ),
            "Use topics or deterministic agent flows for explicit steps; use child or connected agents for specialist delegation.",
            before=0,
            after=8,
        ),
    ),
    10: (
        CodeExhibit(
            "Add the organ: keyless Entra identity",
            "examples/organ_recipes.py",
            "async def run_with_identity(endpoint: str, model: str, prompt: str) -> str:",
            "python",
            "Use DefaultAzureCredential so development and managed identity share one code path with explicit cleanup.",
            (
                "Assign the deployed identity only the roles its tools require.",
                "Dispose the credential with the application lifecycle.",
            ),
            "Configure agent authentication with Microsoft Entra ID, then use connection references and each connector's identity settings for least privilege.",
            before=0,
            after=8,
        ),
    ),
    11: (
        CodeExhibit(
            "Add the organ: OpenTelemetry setup",
            "examples/organ_recipes.py",
            "def enable_observability() -> None:",
            "python",
            "Configure the framework's OpenTelemetry providers once during application startup.",
            (
                "Agent Framework instruments agent, model, tool, and workflow operations.",
                "Configure exporters through standard OpenTelemetry environment variables.",
            ),
            "Use the Analytics page for adoption and quality trends; connect Application Insights for detailed conversation and event telemetry.",
            before=0,
            after=1,
        ),
    ),
    12: (
        CodeExhibit(
            "Add the organ: a hard run budget",
            "examples/organ_recipes.py",
            "def add_budget(client: Any, budget_middleware: AgentMiddleware) -> Agent:",
            "python",
            "Attach middleware that checks token, cost, time, or step limits before allowing more work.",
            (
                "Meter before each operation and reject the operation that would cross the cap.",
                "Record the rejection so an operator can distinguish budget stops from failures.",
            ),
            "Review capacity and usage in analytics and the Power Platform admin center; enforce per-run hard limits inside the called flow or action.",
            before=0,
            after=5,
        ),
    ),
    13: (
        CodeExhibit(
            "Add the organ: persist a checkpoint",
            "examples/organ_recipes.py",
            "def build_checkpointed_workflow(",
            "python",
            "Provide FileCheckpointStorage when building a workflow to capture each superstep.",
            (
                "Use file storage for local development and Cosmos storage for distributed production runs.",
                "Framework checkpoints preserve executor state, pending messages, and shared state.",
            ),
            "Use a deterministic agent flow for durable trigger/action execution; persist business checkpoints and idempotency keys in Dataverse.",
            before=0,
            after=13,
        ),
    ),
    14: (
        CodeExhibit(
            "Add the organ: resume only unfinished work",
            "examples/organ_recipes.py",
            "async def resume_workflow(workflow: Workflow, checkpoint_id: str) -> str:",
            "python",
            "Resume the framework workflow by passing a stored checkpoint ID to run().",
            (
                "The workflow restores its captured state and pending messages.",
                "Business side effects still need idempotency keys in the target system.",
            ),
            "Cloud flow retry policies and run history handle transient failures; use Dataverse state and idempotent actions when a run must resume safely.",
            before=0,
            after=2,
        ),
    ),
    15: (
        CodeExhibit(
            "Add the organ: modular skill selection",
            "examples/organ_recipes.py",
            "def add_skill(client: Any, triage_skill: FunctionTool) -> Agent:",
            "python",
            "Package specialist behavior behind a well-described tool and attach it only where needed.",
            (
                "The skill description is the routing contract.",
                "Loading expertise on demand keeps the base instructions small.",
            ),
            "Model reusable expertise as a topic, prompt tool, agent flow, or connected specialist agent, with a precise description for routing.",
            before=0,
            after=5,
        ),
        CodeExhibit(
            "Add the organ: promote only measured improvements",
            "examples/organ_recipes.py",
            "def promote_instruction(candidate: str, evaluator: Any) -> str:",
            "python",
            "Score a candidate instruction against the current version and keep it only when it performs better.",
            (
                "Use a stable evaluation set so scores remain comparable.",
                "Require human review before publishing instruction changes.",
            ),
            "Use test sets, agent evaluations, analytics, and conversation transcripts to compare changes before editing instructions and republishing.",
            before=0,
            after=3,
        ),
    ),
    16: (
        CodeExhibit(
            "Add the organ: wake the agent from an external event",
            "examples/organ_recipes.py",
            "async def handle_business_event(",
            "python",
            "An event handler turns a business event into an agent run without waiting for chat.",
            (
                "Connect this handler to OneDrive, SharePoint, Event Grid, or Service Bus.",
                "Keep the trigger adapter separate from the agent so event sources stay swappable.",
            ),
            "Use an event trigger or Power Automate flow to start the agent when a file, message, or business event arrives.",
            before=0,
            after=3,
        ),
    ),
    17: (
        CodeExhibit(
            "Add the organ: decompose before acting",
            "examples/organ_recipes.py",
            "def add_planning(client: Any, goal_decomposer: FunctionTool) -> Agent:",
            "python",
            "Attach one clearly described planning tool and require an ordered plan before execution.",
            (
                "Planning defines what should happen; orchestration controls how those steps run.",
                "Keep the returned plan structured so every dependency can be traced and tested.",
            ),
            "Use generative orchestration to choose actions, or an agent flow when the sequence must be explicit and deterministic.",
            before=0,
            after=9,
        ),
    ),
    18: (
        CodeExhibit(
            "Add the organ: explicit world state",
            "examples/organ_recipes.py",
            "def add_beliefs(",
            "python",
            "Load verified world state as context and expose a governed tool for persisting updates.",
            (
                "Beliefs describe the world; memory preserves user continuity; learning improves the agent scaffold.",
                "Persist only evidence-backed changes and retain an audit trail.",
            ),
            "Store governed state in Dataverse and retrieve or update it through authenticated actions or agent flows.",
            before=0,
            after=15,
        ),
    ),
    19: (
        CodeExhibit(
            "Compose the anatomy through public attachment points",
            "examples/organ_recipes.py",
            "def compose_agent(",
            "python",
            "Compose tools, context providers, and middleware around one model client and instruction set.",
            (
                "Each list is an extension point, so capabilities remain independently replaceable.",
                "Add only the organs required by the business failure you need to control.",
            ),
            "The agent canvas composes the same anatomy through Instructions, Knowledge, Tools, Topics, connected agents, authentication, and analytics.",
            before=0,
            after=13,
        ),
    ),
}

PANEL_STYLES = {
    "vitals": "#4C7A94",
    "organ": "bold #50E6FF",
    "payoff": "#7EE787",
    "compare": "#F2CC60",
    "panel": "#9FB7C2",
}
BODY_STYLE = "#EAF4F4"


def _classify_panel(line: str) -> str:
    if "VITALS" in line:
        return "vitals"
    if "WHAT JUST HAPPENED" in line:
        return "payoff"
    if "ORGAN " in line:
        return "organ"
    if "INTACT" in line or "WITHOUT" in line:
        return "compare"
    return "panel"


def _body_style(stripped: str) -> str:
    if stripped.startswith("[USER]"):
        return "bold #F2CC60"
    if stripped.startswith("[AI / MODEL]"):
        return "#50E6FF"
    if stripped.startswith("[APPLICATION TEAM]"):
        return "bold #FF9E64"
    if stripped.startswith("[TOOL]"):
        return "#7EE787"
    if stripped.startswith("[AGENT ·"):
        return "#C792EA"
    if stripped.startswith("[ORGAN ·"):
        return "bold #FF9E64"
    if stripped.startswith("[SYSTEM]"):
        return "#7FA6B8"
    if stripped.startswith("[NARRATOR]"):
        return "bold #F2CC60"
    if stripped.startswith("ORGANS FIRING"):
        return "bold #C792EA"
    if any(marker in stripped for marker in ("BLOCKED", "BUDGET STOP", "TERMINATED", "FAILED", "403")):
        return "bold #FF4D6D"
    if stripped.startswith("SKIP"):
        return "#7FA6B8"
    if stripped.startswith("RUN ") or "ALLOWED" in stripped:
        return "#7EE787"
    if any(marker in stripped for marker in ("[SIMULATED]", "[WARN]", "[AUTOPSY]")):
        return "#F2CC60"
    return BODY_STYLE


def evidence_text(raw: str) -> Text:
    """Colour captured organ output by section, with blank lines between panels."""
    lines = raw.splitlines()
    closing_line = max((i for i, line in enumerate(lines) if line.strip()), default=-1)
    rendered = Text()
    index = 0
    previous_style: str | None = None
    previous_stripped = ""
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped[:1] in {"\u256d", "\u250c"}:
            end = index
            while end < len(lines) and lines[end].strip()[:1] not in {"\u2570", "\u2514"}:
                end += 1
            block = lines[index : end + 1]
            style = PANEL_STYLES[_classify_panel("\n".join(block))]
            if rendered.plain:
                rendered.append("\n")
            for panel_line in block:
                rendered.append(f"{panel_line}\n", style=style)
            rendered.append("\n")
            index = end + 1
            continue
        style = "bold #7EE787" if index == closing_line else _body_style(stripped)
        if (
            style == BODY_STYLE
            and previous_style not in (BODY_STYLE, None)
            and stripped[:1].islower()
            and not previous_stripped.endswith((".", ":", "?", "!"))
        ):
            style = previous_style  # the organ wrapped a long line; keep the emphasis intact
        rendered.append(f"{lines[index]}\n", style=style)
        if stripped:
            previous_style, previous_stripped = style, stripped
        index += 1
    return rendered


def _section_rule(title: str, style: str) -> Text:
    return Text(f"\u258c {title}\n", style=f"bold {style}")


def _append_error_log(command: tuple[str, ...], detail: str, output: str = "") -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = [f"[{timestamp}] {' '.join(command)}", detail]
    if output:
        entry.extend(("--- captured output ---", output))
    with ERROR_LOG.open("a", encoding="utf-8") as error_log:
        error_log.write("\n".join(entry) + "\n\n")


ADA_BANNER = (
    "┌                                                    ┐",
    "",
    "    ████  █████   ████       ▄▄▄▄▄▄▄▄▄ ",
    "   ██  ██ ██  ██ ██  ██     █ ▀▀▀ ▀▀▀ █",
    "   ██████ ██  ██ ██████     █         █",
    "   ██  ██ ██  ██ ██  ██     █  ▄▄▄▄▄  █",
    "   ██  ██ █████  ██  ██      ▀▀▀▀▀▀▀▀▀ ",
    "",
    "└        a n a t o m y   o f   a n   a g e n t        ┘",
)

ANATOMY = tuple(
    (organ.number, organ.name.title(), organ.status == "ready")
    for organ in REGISTERED_ORGANS
)


def _write_exhibit(log: RichLog, exhibit: CodeExhibit, position: int, total: int, *, expanded: bool = False) -> None:
    counter = f"  [{position + 1}/{total}]" if total > 1 else ""
    heading = "EXPANDED CODE" if expanded else "CODE EXHIBIT"
    log.write(Text(f"{heading}{counter}   {exhibit.title}", style="bold #F2CC60"))
    log.write(Text(f"{exhibit.provenance}   ·   {exhibit.display_path}\n", style="#7FA6B8"))
    try:
        snippet, start_line, focus_line = load_exhibit(exhibit, expanded=expanded)
    except (OSError, ValueError) as error:
        log.write(Text(f"Exhibit unavailable: {error}", style="bold #FF4D6D"))
        return
    log.write(
        Syntax(
            snippet,
            exhibit.language,
            theme="monokai",
            line_numbers=True,
            start_line=start_line,
            highlight_lines={focus_line},
            word_wrap=True,
        )
    )
    log.write(Text(f"\nWHAT IT DOES   {exhibit.mechanism}", style="#EAF4F4"))
    for note in exhibit.read_this:
        log.write(Text(f"WHY IT MATTERS {note}", style="#7EE787"))
    if exhibit.copilot_studio:
        log.write(Text(f"COPILOT STUDIO {exhibit.copilot_studio}", style="#50E6FF"))


class CodeOverlay(ModalScreen[None]):
    CSS = """
    CodeOverlay {
        align: center middle;
        background: rgba(2, 6, 9, 0.88);
    }

    #code-overlay {
        width: 96%;
        height: 94%;
        padding: 1;
        background: #020609;
        border: heavy #50E6FF;
    }

    #expanded-code {
        height: 1fr;
        scrollbar-color: #50E6FF;
        scrollbar-background: #102532;
    }

    #expanded-controls {
        height: 2;
        padding: 0 1;
        color: #9FB7C2;
        background: #0C1C29;
    }
    """

    BINDINGS = [
        Binding("x", "collapse", "Collapse", priority=True),
        Binding("escape", "collapse", "Collapse", priority=True),
        Binding("pageup", "scroll_up", "Code up", priority=True),
        Binding("pagedown", "scroll_down", "Code down", priority=True),
    ]

    def __init__(self, exhibit: CodeExhibit, position: int, total: int) -> None:
        super().__init__()
        self.exhibit = exhibit
        self.position = position
        self.total = total

    def compose(self) -> ComposeResult:
        with Vertical(id="code-overlay"):
            yield RichLog(id="expanded-code", highlight=False, markup=False, wrap=True)
            yield Static("X / Esc collapse   ·   Page Up / Page Down scroll", id="expanded-controls")

    def on_mount(self) -> None:
        _write_exhibit(
            self.query_one("#expanded-code", RichLog),
            self.exhibit,
            self.position,
            self.total,
            expanded=True,
        )

    def action_collapse(self) -> None:
        self.dismiss()

    def action_scroll_up(self) -> None:
        self.query_one("#expanded-code", RichLog).scroll_page_up()

    def action_scroll_down(self) -> None:
        self.query_one("#expanded-code", RichLog).scroll_page_down()


class AnatomyShow(App[None]):
    TITLE = "Agent Anatomy Live"
    SUB_TITLE = "Harry Arce | SME&C DSE | Apps & AI | US East"

    CSS = """
    Screen {
        background: #071018;
        color: #EAF4F4;
    }

    #brand {
        height: 3;
        padding: 1 2 0 2;
        background: #0C1C29;
        border-bottom: heavy #50E6FF;
        text-style: bold;
    }

    #main {
        height: 1fr;
    }

    #anatomy {
        width: 27;
        min-width: 23;
        padding: 1 1;
        background: #0A1721;
        border-right: tall #21445A;
    }

    #stage {
        width: 1fr;
        padding: 1 2;
    }

    #eyebrow {
        height: 2;
        color: #F2CC60;
        text-style: bold;
    }

    #scene-title {
        height: 3;
        color: #FFFFFF;
        text-style: bold;
    }

    #message {
        height: auto;
        min-height: 3;
        margin-bottom: 1;
        color: #D8E8EE;
    }

    #organ-role {
        height: auto;
        min-height: 3;
        padding: 0 1;
        margin-bottom: 1;
        background: #102532;
        border-left: thick #F2CC60;
        color: #EAF4F4;
    }

    #proof {
        height: auto;
        min-height: 3;
        padding: 0 1;
        margin-bottom: 1;
        border-left: thick #50E6FF;
        color: #B9CDD6;
    }

    #console {
        height: 1fr;
        min-height: 8;
        padding: 1;
        background: #020609;
        border: round #35637A;
        scrollbar-color: #50E6FF;
        scrollbar-background: #102532;
    }

    #repo-qr {
        display: none;
        dock: right;
        width: 39;
        min-width: 39;
        height: auto;
        padding: 0;
        background: #FFFFFF;
        color: #000000;
        border: heavy #50E6FF;
        text-align: center;
    }

    #landing {
        height: auto;
        min-height: 3;
        margin-top: 1;
        padding: 0 1;
        color: #7EE787;
        text-style: bold;
        border-left: thick #7EE787;
    }

    #controls {
        height: 2;
        padding: 0 2;
        background: #0C1C29;
        color: #9FB7C2;
    }

    Footer {
        height: 1;
        background: #102532;
    }
    """

    BINDINGS = [
        Binding("left", "previous", "Previous", priority=True),
        Binding("right", "next", "Next", priority=True),
        Binding("space", "run_demo", "Run demo", priority=True),
        Binding("c", "toggle_code", "Show / hide code", priority=True),
        Binding("x", "toggle_code_overlay", "Expand code", priority=True),
        Binding("r", "toggle_mode", "Local / remote", priority=True),
        Binding("home", "first", "First", priority=True),
        Binding("end", "last", "Last", priority=True),
        Binding("pageup", "scroll_up", "Evidence up", priority=True),
        Binding("pagedown", "scroll_down", "Evidence down", priority=True),
        Binding("escape", "cancel_demo", "Cancel demo", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self, *, start_scene: int = 1, remote: bool = False) -> None:
        super().__init__()
        self.scene_index = start_scene - 1
        self.remote = remote
        self.running_demo = False
        self.exhibit_index: int | None = None
        self._cancel_requested = False
        self._process: asyncio.subprocess.Process | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="brand")
        with Horizontal(id="main"):
            yield Static(id="anatomy")
            with Vertical(id="stage"):
                yield Static(id="repo-qr")
                yield Static(id="eyebrow")
                yield Static(id="scene-title")
                yield Static(id="organ-role")
                yield Static(id="message")
                yield Static(id="proof")
                yield RichLog(id="console", highlight=False, markup=False, wrap=True)
                yield Static(id="landing")
        yield Static(id="controls")
        yield Footer()

    def on_mount(self) -> None:
        self._render_scene()

    def _render_scene(self) -> None:
        scene = SCENES[self.scene_index]
        self.query_one("#brand", Static).update(
            f"AGENT ANATOMY LIVE   |   HARRY ARCE   |   SCENE {scene.number:02d}/{len(SCENES):02d}"
        )
        self.query_one("#eyebrow", Static).update(scene.chapter)
        self.query_one("#scene-title", Static).update(scene.title)
        role = self.query_one("#organ-role", Static)
        role_text = self._organ_highlight_text(scene)
        role.display = role_text is not None
        role.update(role_text or "")
        self.query_one("#message", Static).update(scene.message)
        self.query_one("#proof", Static).update(f"WATCH FOR  {scene.proof}")
        self.query_one("#landing", Static).update(scene.landing)
        self.query_one("#anatomy", Static).update(self._anatomy_text(scene))
        qr_panel = self.query_one("#repo-qr", Static)
        qr_panel.display = scene.number == len(SCENES)
        qr_panel.update(repository_qr_text() if qr_panel.display else "")

        log = self.query_one("#console", RichLog)
        log.clear()
        if scene.number == len(SCENES):
            log.write(self._stack_text())
        elif scene.number == 1:
            log.write(self._ada_banner_text())
        elif scene.safe_steps:
            mode = "REMOTE LLM" if self.remote else "LOCAL DETERMINISTIC"
            log.write(Text(f"READY  {mode}\n\nPress Space to run the evidence for this scene.", style="bold #50E6FF"))
        else:
            log.write(Text("PRESENTER MOMENT\n\nNo executable claim on this scene. Let the idea land.", style="#9FB7C2"))
        self._render_controls()

    @staticmethod
    def _organ_highlight_text(scene: Scene) -> Text | None:
        if not scene.safe_steps or not scene.organs:
            return None
        text = Text()
        for index, organ_number in enumerate(scene.organs):
            highlight = ORGAN_HIGHLIGHTS[organ_number]
            organ_name = next(name for number, name, _ in ANATOMY if number == organ_number)
            if index:
                text.append("\n")
            text.append(f"{organ_name.upper()}  ·  {highlight.role}\n", style="bold #F2CC60")
            text.append("USE IT TO  ", style="bold #50E6FF")
            text.append(f"{highlight.use_it_to}\n")
            text.append("ADDS TO THE AGENT  ", style="bold #7EE787")
            text.append(highlight.enhancement)
        return text

    def _ada_banner_text(self) -> Text:
        text = Text()
        for line in ADA_BANNER:
            style = "#35637A" if line[:1] in {"\u250c", "\u2514"} else "#50E6FF"
            text.append(f"{line}\n", style=style)
        text.append("\nSixteen organs run here. Each one leaves evidence.", style="#9FB7C2")
        return text

    def _stack_text(self) -> Text:
        text = Text("THE STACK THIS DEMO ACTUALLY RAN ON\n\n", style="bold #F2CC60")
        for label, version in stack_report():
            text.append(f"  {label:<30}", style="#EAF4F4")
            text.append(f"{version}\n", style="bold #7EE787")
        text.append("\nVersions are read from installed package metadata at runtime.", style="dim")
        return text

    def _anatomy_text(self, scene: Scene) -> Text:
        completed = {organ for prior in SCENES[: self.scene_index + 1] for organ in prior.organs}
        text = Text("ADA / ORGAN VITALS\n\n", style="bold #50E6FF")
        for number, name, implemented in ANATOMY:
            if not implemented:
                marker, style, suffix = "◇", "#637985", "  PLANNED"
            elif number in scene.organs:
                marker, style, suffix = "◆", "bold #F2CC60", "  FIRING"
            elif number in completed:
                marker, style, suffix = "●", "#7EE787", ""
            else:
                marker, style, suffix = "○", "#637985", ""
            text.append(f"{marker} {number:02d}  {name}{suffix}\n", style=style)
        text.append(f"\n{len(completed):02d} / {len(ANATOMY)} RUNNABLE ONLINE", style="bold #EAF4F4")
        return text

    def _render_controls(self) -> None:
        scene = SCENES[self.scene_index]
        mode = "REMOTE LLM" if self.remote else "LOCAL DETERMINISTIC"
        if self.running_demo:
            status = "RUNNING  |  Esc cancels"
        elif scene.safe_steps:
            status = "Space runs evidence"
        else:
            status = "Presenter scene"
        if self.exhibit_index is not None:
            code = "C advances code  |  X expands"
        else:
            code = "C shows code" if EXHIBITS.get(scene.number) else "no code exhibit"
        self.query_one("#controls", Static).update(
            f"{mode}  |  {status}  |  {code}  |  R switches mode  |  Left/Right navigate"
        )

    def action_toggle_code(self) -> None:
        exhibits = EXHIBITS.get(SCENES[self.scene_index].number, ())
        if self.running_demo or not exhibits:
            return

        nxt = 0 if self.exhibit_index is None else self.exhibit_index + 1
        self.exhibit_index = None if nxt >= len(exhibits) else nxt
        if self.exhibit_index is None:
            self._render_scene()
            return
        self._render_exhibit(exhibits[self.exhibit_index], self.exhibit_index, len(exhibits))

    def _render_exhibit(self, exhibit: CodeExhibit, position: int, total: int) -> None:
        log = self.query_one("#console", RichLog)
        log.clear()
        _write_exhibit(log, exhibit, position, total)
        scene = SCENES[self.scene_index]
        next_action = "Space runs the evidence" if scene.safe_steps else "Left/Right continues the story"
        log.write(Text(f"\nPress X to expand. Press C for the next exhibit. {next_action}.", style="dim"))
        self._render_controls()

    def action_toggle_code_overlay(self) -> None:
        if isinstance(self.screen, CodeOverlay):
            self.screen.dismiss()
            return
        exhibits = EXHIBITS.get(SCENES[self.scene_index].number, ())
        if self.running_demo or self.exhibit_index is None or not exhibits:
            return
        self.push_screen(CodeOverlay(exhibits[self.exhibit_index], self.exhibit_index, len(exhibits)))

    def action_scroll_up(self) -> None:
        self.query_one("#console", RichLog).scroll_page_up()

    def action_scroll_down(self) -> None:
        self.query_one("#console", RichLog).scroll_page_down()

    def action_previous(self) -> None:
        if not self.running_demo and self.scene_index > 0:
            self.scene_index -= 1
            self.exhibit_index = None
            self._render_scene()

    def action_next(self) -> None:
        if not self.running_demo and self.scene_index < len(SCENES) - 1:
            self.scene_index += 1
            self.exhibit_index = None
            self._render_scene()

    def action_first(self) -> None:
        if not self.running_demo:
            self.scene_index = 0
            self.exhibit_index = None
            self._render_scene()

    def action_last(self) -> None:
        if not self.running_demo:
            self.scene_index = len(SCENES) - 1
            self.exhibit_index = None
            self._render_scene()

    def action_toggle_mode(self) -> None:
        if not self.running_demo:
            self.remote = not self.remote
            self._render_scene()

    async def action_run_demo(self) -> None:
        scene = SCENES[self.scene_index]
        steps = scene.local_steps()
        if self.running_demo or not steps:
            return

        self.running_demo = True
        self.exhibit_index = None
        self._cancel_requested = False
        self._render_controls()
        log = self.query_one("#console", RichLog)
        log.clear()
        try:
            succeeded = await self._run_steps(steps, log, remote=self.remote)
            if self._cancel_requested:
                log.write(Text("\nDEMO CANCELLED  |  No fallback was started.", style="bold #F2CC60"))
            elif not succeeded and scene.safe_steps != steps:
                log.write(Text("\nLOCAL PATH FAILED  |  FALLING BACK TO COMMITTED EVIDENCE\n", style="bold #F2CC60"))
                succeeded = await self._run_steps(scene.safe_steps, log)
            if succeeded and not self._cancel_requested:
                log.write(Text("\nEVIDENCE COMPLETE", style="bold #7EE787"))
            elif not self._cancel_requested:
                log.write(Text("\nDEMO STOPPED  |  Review the output above before continuing.", style="bold #FF4D6D"))
            self.call_after_refresh(log.scroll_home, animate=False, immediate=True)
        finally:
            self._process = None
            self.running_demo = False
            self._render_controls()

    async def _run_steps(self, steps: tuple[DemoStep, ...], log: RichLog, *, remote: bool = False) -> bool:
        for demo_step in steps:
            missing_files = [relative for relative in demo_step.required_files if not (ROOT / relative).exists()]
            if missing_files and demo_step.prepare_if_missing is not None:
                log.write(Text("CHECKPOINT ABSENT  |  Staging the deterministic kill first.\n", style="bold #F2CC60"))
                if not await self._run_steps((demo_step.prepare_if_missing,), log):
                    return False

            for relative_path in demo_step.cleanup:
                (ROOT / relative_path).unlink(missing_ok=True)

            step_args = (*demo_step.args, "--remote") if remote and "--replay" not in demo_step.args else demo_step.args
            command = (sys.executable, "-m", "anatomy", *step_args)
            log.write(_section_rule("COMMAND", "#50E6FF"))
            log.write(Text(f"  $ python -m anatomy {' '.join(step_args)}", style="#7FA6B8"))
            log.write(Text(f"  {demo_step.label}\n", style="dim"))
            environment = os.environ.copy()
            environment.update({"PYTHONUTF8": "1", "COLUMNS": "110", "LINES": "40"})
            try:
                self._process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=ROOT,
                    env=environment,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                output, _ = await self._process.communicate()
            except Exception as exc:
                detail = f"PROCESS ERROR: {type(exc).__name__}: {exc}"
                _append_error_log(command, detail)
                log.write(_section_rule("RESULT", "#FF4D6D"))
                log.write(Text(f"  STATUS  FAILED\n  {detail}\n  ERROR LOG  {ERROR_LOG.name}\n", style="bold #FF4D6D"))
                return False
            # Rich >=15 honours carriage returns, so CRLF from Windows subprocesses would blank each line.
            rendered = output.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "").strip()
            log.write(_section_rule("EVIDENCE", "#F2CC60"))
            log.write(evidence_text(rendered) if rendered else Text("  (command produced no output)", style="dim"))
            if self._cancel_requested:
                return False
            exit_code = self._process.returncode
            expected = exit_code in demo_step.expected_exit_codes
            used_fallback = expected and "DETERMINISTIC FALLBACK" in rendered
            exit_style = "#F2CC60" if used_fallback else "#7EE787" if expected else "#FF4D6D"
            expectation = "EXPECTED" if expected else "UNEXPECTED"
            log.write(_section_rule("RESULT", exit_style))
            status = "PASSED WITH FALLBACK" if used_fallback else "PASSED" if expected else "FAILED"
            log.write(Text(f"  STATUS  {status}\n  {expectation} EXIT  {exit_code}\n", style=f"bold {exit_style}"))
            if used_fallback:
                _append_error_log(command, "DEGRADED: deterministic fallback used", rendered)
                log.write(Text(f"  ERROR LOG  {ERROR_LOG.name}\n", style="bold #F2CC60"))
            elif not expected:
                _append_error_log(command, f"UNEXPECTED EXIT: {exit_code}", rendered)
                log.write(Text(f"  ERROR LOG  {ERROR_LOG.name}\n", style="bold #FF4D6D"))
                return False
        return True

    def action_cancel_demo(self) -> None:
        if isinstance(self.screen, CodeOverlay):
            self.screen.dismiss()
            return
        if self._process is not None and self._process.returncode is None:
            self._cancel_requested = True
            self._process.terminate()


def run_show(*, start_scene: int = 1, remote: bool = False) -> int:
    AnatomyShow(start_scene=start_scene, remote=remote).run()
    return 0